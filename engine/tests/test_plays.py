import json
from pathlib import Path

import pytest

from cfbm.plays import normalize_plays, order_key

FIX = json.loads((Path(__file__).parent / "fixtures" / "plays_sample.json").read_text())


def _play(i, period=1, down=1, distance=10, ptype="Pass Reception", off="A", deff="B",
          home="A", away="B", off_score=0, def_score=0, ppa=0.1, game=1):
    return {"id": str(i), "gameId": game, "offense": off, "defense": deff, "home": home, "away": away,
            "offenseScore": off_score, "defenseScore": def_score, "period": period, "down": down,
            "distance": distance, "playType": ptype, "playText": "", "ppa": ppa}


def test_dropback_classification_on_real_plays():
    df = normalize_plays(FIX, 2025, "regular", 5).set_index("play_type")
    for t in ["Pass Reception", "Pass Incompletion", "Passing Touchdown", "Sack", "Pass Interception Return"]:
        assert bool(df.loc[t, "is_dropback"]), t
    for t in ["Rush", "Rushing Touchdown", "Punt", "Penalty", "Kickoff"]:
        assert not bool(df.loc[t, "is_dropback"]), t
    assert bool(df.loc["Sack", "is_sack"]) and not bool(df.loc["Pass Reception", "is_sack"])
    assert bool(df.loc["Pass Interception Return", "is_int"])


def test_pressure_est_off_when_proxy_is_havoc():
    df = normalize_plays(FIX, 2025, "regular", 5)
    assert not df["is_pressure_est"].any()


def test_columns_and_season_fields():
    df = normalize_plays(FIX, 2025, "regular", 5)
    assert set(["game_id", "season", "week", "season_type", "offense", "defense", "period", "down",
                "distance", "play_type", "play_text", "ppa", "margin_pre", "is_dropback", "is_sack",
                "is_int", "is_pressure_est", "is_passing_down", "is_garbage"]) <= set(df.columns)
    assert (df["season"] == 2025).all() and (df["week"] == 5).all() and (df["season_type"] == "regular").all()


@pytest.mark.parametrize("down,distance,expected", [(2, 8, True), (2, 7, False), (3, 5, True),
                                                    (3, 4, False), (4, 5, True), (1, 10, False)])
def test_passing_down_boundaries(down, distance, expected):
    df = normalize_plays([_play(1, down=down, distance=distance)], 2025, "regular", 1)
    assert bool(df["is_passing_down"].iloc[0]) is expected


@pytest.mark.parametrize("period,margin,expected", [(2, 39, True), (2, 38, False), (3, 29, True),
                                                   (3, 28, False), (4, 23, True), (4, 22, False),
                                                   (1, 50, False)])
def test_garbage_thresholds(period, margin, expected):
    # Margin is established by the previous play (scores are post-play in CFBD).
    plays = [_play(1, period=period, off_score=margin, def_score=0),
             _play(2, period=period, off_score=margin, def_score=0)]
    df = normalize_plays(plays, 2025, "regular", 1)
    assert bool(df["is_garbage"].iloc[1]) is expected


def test_margin_uses_pre_play_score():
    # A touchdown row already carries the new score; its pre-play margin must not include it.
    plays = [_play(1, off_score=0, def_score=0, ptype="Rush"),
             _play(2, off_score=7, def_score=0, ptype="Rushing Touchdown"),
             _play(3, off="B", deff="A", off_score=0, def_score=7, ptype="Pass Reception")]
    df = normalize_plays(plays, 2025, "regular", 1).sort_values("play_id")
    assert list(df["margin_pre"]) == [0, 0, -7]  # offense-oriented: B trails by 7


def test_margin_orders_by_play_id_not_input_order():
    plays = [_play(2, off_score=7, ptype="Rushing Touchdown"), _play(1), _play(3, off_score=7)]
    df = normalize_plays(plays, 2025, "regular", 1).sort_values("play_id")
    assert list(df["margin_pre"]) == [0, 0, 7]


def test_order_key():
    assert order_key("postseason", 1) > order_key("regular", 15)
    assert order_key("regular", 3) == 3
