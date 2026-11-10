import pandas as pd

from cfbm.backup import backup_block, rank_against
from cfbm.team_stats import TG_COLUMNS


def test_rank_against_higher_better():
    field = pd.Series([0.3, 0.2, 0.1, 0.0, None])
    assert rank_against(0.25, field, 1) == (2, round((4 - 2) / 3 * 100, 1))


def test_rank_against_lower_better():
    field = pd.Series([0.02, 0.05, 0.08, 0.11])
    assert rank_against(0.06, field, -1) == (3, round((4 - 3) / 3 * 100, 1))


def test_rank_against_worse_than_all_clamps():
    assert rank_against(-1.0, pd.Series([0.3, 0.2, 0.1]), 1) == (4, 0.0)


def test_rank_against_none():
    assert rank_against(None, pd.Series([0.1, 0.2]), 1) == (None, None)


def _row(gid, season, opp, db=30, epa=6.0, succ=14, sacks=2, ints=1):
    return {"game_id": gid, "season": season, "season_type": "regular", "week": 1, "order": 1, "team": "M",
            "opponent": opp, "dropbacks": db, "epa_sum": epa, "epa_n": db - sacks, "success": succ, "sacks": sacks,
            "ints": ints, "pressure_est": 4, "pd_dropbacks": 6, "pd_epa_sum": 0.6, "pd_epa_n": 6, "pd_sacks": 1}


PROFILE = pd.DataFrame({"off_epa_per_db": [0.4, 0.2, 0.1, 0.0], "off_success_rate": [0.5, 0.45, 0.4, 0.3],
                        "off_sack_rate": [0.04, 0.06, 0.08, 0.1], "off_int_rate": [0.01, 0.02, 0.03, 0.04],
                        "off_pd_epa": [0.2, 0.1, 0.0, -0.1], "off_pd_sack_rate": [0.05, 0.1, 0.15, 0.2]},
                       index=["T1", "T2", "T3", "T4"])
GAMES = {1: {"notes": None, "homeTeam": "M", "awayTeam": "X", "homePoints": 20, "awayPoints": 10, "completed": True},
         2: {"notes": None, "homeTeam": "Y", "awayTeam": "M", "homePoints": 30, "awayPoints": 14, "completed": True}}
RANKS = {(2026, "X"): 40, (2026, "Y"): 12}


def test_block_cells_and_sample():
    rows = pd.DataFrame([_row(1, 2026, "X"), _row(2, 2026, "Y", epa=3.0)], columns=TG_COLUMNS)
    b = backup_block(rows, "Back Up", 11, PROFILE, PROFILE.index, GAMES, RANKS)
    assert (b["athleteId"], b["name"], b["games"], b["smallSample"]) == (11, "Back Up", 2, True)
    epa = b["cells"]["epa_per_db"]
    assert round(epa["value"], 4) == round(9.0 / 56, 4) and epa["rank"] == 3
    assert b["cells"]["sack_rate"]["value"] == 4 / 60
    assert "front7_havoc" not in b["cells"]
    assert [g["opponent"] for g in b["qbVs"]["games"]] == ["Y", "X"]
    assert b["qbVs"]["name"] == "Back Up"


def test_block_no_starts_all_null():
    b = backup_block(pd.DataFrame(columns=TG_COLUMNS), "Back Up", 11, PROFILE, PROFILE.index, GAMES, RANKS)
    assert b["games"] == 0 and b["smallSample"] is True
    assert all(c == {"value": None, "rank": None, "pct": None} for c in b["cells"].values())
    assert b["qbVs"]["games"] == []
