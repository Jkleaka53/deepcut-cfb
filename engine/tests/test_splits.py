import pandas as pd
import pytest

from cfbm.splits import split_table, tier_lookup


def _row(season, gid, team, opp, db=40, sacks=2, epa=4.0, ints=1):
    return dict(game_id=gid, season=season, season_type="regular", week=1, order=1, team=team, opponent=opp,
                dropbacks=db, epa_sum=epa, epa_n=db, success=db // 2, sacks=sacks, ints=ints, pressure_est=0,
                pd_dropbacks=10, pd_epa_sum=0.5, pd_epa_n=10, pd_sacks=1)


TIERS = {(2025, "Good"): {"pass_defense": 1, "pass_offense": 1}, (2025, "Mid"): {"pass_defense": 2, "pass_offense": 2},
         (2025, "Bad"): {"pass_defense": 3, "pass_offense": 3}, (2024, "Good"): {"pass_defense": 3}}


def _table(rows, side="offense", skill="pass_defense", highlight=1):
    return split_table(pd.DataFrame(rows), side, skill, TIERS, highlight, "T", "S")


def test_rows_always_three_tiers_in_order():
    t = _table([_row(2025, 1, "WVU", "Good")])
    assert [r["tier"] for r in t["rows"]] == [1, 2, 3]
    assert t["rows"][1]["games"] == 0 and all(v is None for v in t["rows"][1]["metrics"].values())


def test_pooled_offense_metrics():
    t = _table([_row(2025, 1, "WVU", "Good", db=40, sacks=2, epa=4.0), _row(2025, 2, "WVU", "Good", db=60, sacks=8, epa=-1.0)])
    r = t["rows"][0]
    assert r["games"] == 2 and r["plays"] == 100
    assert r["metrics"]["sack_rate"] == pytest.approx(0.10)
    assert r["metrics"]["epa_per_db"] == pytest.approx(0.03)
    assert set(t["metricLabels"]) == set(t["metricFormats"]) == set(r["metrics"])


@pytest.mark.parametrize("games,db,expected", [(2, 50, True), (3, 19, True), (3, 20, False)])
def test_small_sample_flag(games, db, expected):
    # db per game; plays = games * db -> (2,100) small, (3,57) small, (3,60) ok
    t = _table([_row(2025, i, "WVU", "Good", db=db) for i in range(games)])
    assert t["rows"][0]["smallSample"] is expected


def test_fcs_opponent_dropped():
    t = _table([_row(2025, 1, "WVU", "Good"), _row(2025, 2, "WVU", "Some FCS")])
    assert sum(r["games"] for r in t["rows"]) == 1


def test_highlight_passthrough_and_meta():
    t = _table([_row(2025, 1, "WVU", "Good")], highlight=2)
    assert t["highlightTier"] == 2 and t["tierSkill"] == "pass_defense" and t["title"] == "T" and t["subject"] == "S"


def test_past_game_uses_that_seasons_tier():
    t = _table([_row(2024, 1, "WVU", "Good")])
    assert t["rows"][2]["games"] == 1  # Good was bottom third in 2024


def test_seasons_listed():
    t = _table([_row(2025, 1, "WVU", "Good"), _row(2024, 2, "WVU", "Good"), _row(2025, 3, "WVU", "Mid")])
    assert t["seasons"] == [2024, 2025]


def test_defense_side_buckets_by_the_offense_faced():
    # Defensive rows: team = offense faced, opponent = our defense.
    rows = [_row(2025, 1, "Good", "Tech", sacks=4), _row(2025, 2, "Bad", "Tech", sacks=0)]
    t = _table(rows, side="defense", skill="pass_offense")
    assert t["rows"][0]["games"] == 1 and t["rows"][0]["metrics"]["sack_rate"] == pytest.approx(0.1)
    assert t["rows"][2]["metrics"]["sack_rate"] == 0
    assert "epa_allowed_per_db" in t["rows"][0]["metrics"]


def test_tier_lookup_from_frames():
    df = pd.DataFrame({"pass_defense_tier": [1.0, float("nan")], "pass_rush_tier": [2.0, 3.0]}, index=["A", "B"])
    lk = tier_lookup({2025: df})
    assert lk[(2025, "A")] == {"pass_defense": 1, "pass_rush": 2}
    assert lk[(2025, "B")] == {"pass_rush": 3}
