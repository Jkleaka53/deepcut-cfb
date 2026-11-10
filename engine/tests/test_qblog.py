import pandas as pd

from cfbm.qblog import qb_log, rank_lookup


def _tg(gid, season, team, opp, epa_sum, epa_n, db, st="regular"):
    return {"game_id": gid, "season": season, "season_type": st, "team": team, "opponent": opp,
            "epa_sum": epa_sum, "epa_n": epa_n, "dropbacks": db}


GAMES = {
    1: {"id": 1, "homeTeam": "Georgia", "awayTeam": "Notre Dame", "homePoints": 10, "awayPoints": 23},
    2: {"id": 2, "homeTeam": "Texas", "awayTeam": "Georgia", "homePoints": 10, "awayPoints": 35},
    3: {"id": 3, "homeTeam": "Georgia", "awayTeam": "FCS U", "homePoints": 50, "awayPoints": 0},
    4: {"id": 4, "homeTeam": "Ole Miss", "awayTeam": "Georgia", "homePoints": 39, "awayPoints": 34,
        "notes": "College Football Playoff Quarterfinal - Sugar Bowl"},
    5: {"id": 5, "homeTeam": "Georgia", "awayTeam": "Kentucky", "homePoints": 35, "awayPoints": 14,
        "notes": "Citrus Bowl"},
}
RANKS = {(2024, "Notre Dame"): 1, (2025, "Texas"): 40, (2025, "Ole Miss"): 24, (2025, "Kentucky"): 77}


def test_rank_lookup_reads_pass_defense_rank_and_field_size():
    df = pd.DataFrame({"pass_defense_rank": [1.0, 2.0, float("nan")]}, index=["A", "B", "C"])
    ranks, sizes = rank_lookup({2025: df})
    assert ranks == {(2025, "A"): 1, (2025, "B"): 2}
    assert sizes == {2025: 2}


def test_log_rows_sorted_by_rank_with_results():
    rows = pd.DataFrame([_tg(2, 2025, "Georgia", "Texas", 11.0, 30, 31), _tg(1, 2024, "Georgia", "Notre Dame", -1.2, 30, 32),
                         _tg(3, 2025, "Georgia", "FCS U", 9.0, 20, 20)])
    log = qb_log(rows, GAMES, RANKS)
    assert [r["opponent"] for r in log] == ["Notre Dame", "Texas"]  # FCS opponent (no rank) dropped
    nd = log[0]
    assert nd == {"gameId": 1, "season": 2024, "opponent": "Notre Dame", "oppRank": 1, "stage": None,
                  "result": "L", "pf": 10, "pa": 23, "epaPerDb": -0.04, "dropbacks": 32}
    assert log[1]["result"] == "W" and log[1]["pf"] == 35 and log[1]["pa"] == 10


def test_postseason_stage_labels():
    rows = pd.DataFrame([_tg(4, 2025, "Georgia", "Ole Miss", 9.8, 35, 35, "postseason"),
                         _tg(5, 2025, "Georgia", "Kentucky", 6.0, 25, 25, "postseason")])
    log = {r["opponent"]: r for r in qb_log(rows, GAMES, RANKS)}
    assert log["Ole Miss"]["stage"] == "CFP" and log["Kentucky"]["stage"] == "Bowl"


def test_unfinished_game_has_no_result():
    g = {**GAMES, 2: {**GAMES[2], "homePoints": None, "awayPoints": None}}
    rows = pd.DataFrame([_tg(2, 2025, "Georgia", "Texas", 11.0, 30, 31)])
    assert qb_log(rows, g, RANKS)[0]["result"] is None
