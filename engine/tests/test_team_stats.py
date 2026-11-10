import math

import pandas as pd
import pytest

from cfbm.plays import normalize_plays
from cfbm.team_stats import blended_profile, season_profile, team_game_pass


def _raw(i, ptype, ppa=0.1, off="A", deff="B", down=1, distance=10, period=1, game=1, off_score=0):
    return {"id": str(i), "gameId": game, "offense": off, "defense": deff, "home": "A", "away": "B",
            "offenseScore": off_score, "defenseScore": 0, "period": period, "down": down,
            "distance": distance, "playType": ptype, "playText": "", "ppa": ppa}


def _tg(rows):
    """rows: (season, season_type, week, game_id, team, opponent, dropbacks, sacks, epa_sum)"""
    out = []
    for s, st, wk, gid, team, opp, db, sk, epa in rows:
        out.append(dict(game_id=gid, season=s, season_type=st, week=wk,
                        order=wk if st == "regular" else 100 + wk, team=team, opponent=opp,
                        dropbacks=db, epa_sum=epa, epa_n=db, success=0, sacks=sk, ints=0, pressure_est=0,
                        pd_dropbacks=0, pd_epa_sum=0.0, pd_epa_n=0, pd_sacks=0))
    return pd.DataFrame(out)


def test_team_game_pass_counts_and_drops_garbage():
    raw = [_raw(1, "Pass Reception", 0.5), _raw(2, "Sack", -1.0), _raw(3, "Rush", 0.2),
           _raw(4, "Pass Incompletion", -0.2, down=3, distance=7),
           _raw(5, "Pass Reception", 0.3, off="B", deff="A")]
    tg = team_game_pass(normalize_plays(raw, 2025, "regular", 2)).set_index("team")
    a = tg.loc["A"]
    assert a["opponent"] == "B" and a["dropbacks"] == 3 and a["sacks"] == 1
    assert a["epa_sum"] == pytest.approx(-0.7) and a["success"] == 1
    assert a["pd_dropbacks"] == 1 and a["order"] == 2
    assert tg.loc["B", "dropbacks"] == 1

    garbage = [_raw(1, "Rush", off_score=30, period=4), _raw(2, "Pass Reception", 0.4, period=4)]
    assert team_game_pass(normalize_plays(garbage, 2025, "regular", 2)).empty


def test_rates_are_pooled():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 10, 1, 0.0), (2025, "regular", 2, 2, "A", "C", 30, 0, 0.0)])
    p = season_profile(tg, 2025, None)
    assert p.loc["A", "off_sack_rate"] == pytest.approx(0.025)
    assert p.loc["A", "games"] == 2


def test_defense_side_uses_opponent_rows():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 20, 4, 2.0)])
    p = season_profile(tg, 2025, None)
    assert p.loc["B", "def_sack_rate"] == pytest.approx(0.2)
    assert p.loc["B", "def_epa_per_db"] == pytest.approx(0.1)


def test_before_order_excludes_same_and_later_games():
    tg = _tg([(2025, "regular", w, w, "A", "B", 10, s, 0.0) for w, s in ((1, 0), (2, 5), (3, 5))])
    p = season_profile(tg, 2025, before_order=2)
    assert p.loc["A", "off_sack_rate"] == 0 and p.loc["A", "games"] == 1


def test_postseason_sees_full_regular_season():
    tg = _tg([(2025, "regular", 14, 1, "A", "B", 10, 2, 0.0), (2025, "postseason", 1, 2, "A", "C", 10, 0, 0.0)])
    p = season_profile(tg, 2025, before_order=101)
    assert p.loc["A", "games"] == 1 and p.loc["A", "off_sack_rate"] == pytest.approx(0.2)


def test_havoc_attached_to_defense():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 10, 1, 0.0)])
    p = season_profile(tg, 2025, None, havoc={"B": 0.07})
    assert p.loc["B", "def_front7_havoc"] == 0.07 and math.isnan(p.loc["A", "def_front7_havoc"])


def test_zero_dropbacks_gives_nan_not_error():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 0, 0, 0.0)])
    p = season_profile(tg, 2025, None)
    assert math.isnan(p.loc["A", "off_sack_rate"]) and math.isnan(p.loc["A", "off_epa_per_db"])


def _two_seasons():
    return _tg([(2024, "regular", 5, 1, "A", "B", 10, 4, 0.0),   # last season: A sack rate 0.4
                (2025, "regular", 1, 2, "A", "B", 10, 0, 0.0),   # this season week 1: 0.0
                (2025, "regular", 2, 3, "A", "B", 10, 0, 0.0),
                (2025, "regular", 1, 4, "N", "B", 10, 2, 0.0)])  # N is new to FBS in 2025


def test_week1_uses_last_season_only():
    p, early = blended_profile(_two_seasons(), 2025, 1, "regular", None, None)
    assert early and p.loc["A", "off_sack_rate"] == pytest.approx(0.4)


def test_week3_blend_weights():
    p, early = blended_profile(_two_seasons(), 2025, 3, "regular", None, None)
    assert early and p.loc["A", "off_sack_rate"] == pytest.approx(0.2)  # w = 0.5


def test_new_fbs_team_uses_this_season_only():
    p, _ = blended_profile(_two_seasons(), 2025, 3, "regular", None, None)
    assert p.loc["N", "off_sack_rate"] == pytest.approx(0.2)


def test_week5_is_not_early():
    p, early = blended_profile(_two_seasons(), 2025, 5, "regular", None, None)
    assert not early and p.loc["A", "off_sack_rate"] == 0


def test_postseason_is_not_early():
    _, early = blended_profile(_two_seasons(), 2025, 1, "postseason", None, None)
    assert not early
