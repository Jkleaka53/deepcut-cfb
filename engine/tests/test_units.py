import numpy as np
import pandas as pd
import pytest

from cfbm.tiers import assign_tiers
from cfbm.units import edge, unit_tables


@pytest.mark.parametrize("off,dfn,expected", [
    (50, 50, "even"), (60, 46, "even"), (65, 50, "slight-offense"), (50, 65, "slight-defense"),
    (90, 50, "clear-offense"), (20, 60, "clear-defense"), (None, 50, None), (50, float("nan"), None)])
def test_edge_bands(off, dfn, expected):
    assert edge(off, dfn) == expected


def _profile():
    teams = ["WVU", "Tech", "C", "D", "E"]
    p = pd.DataFrame({
        "off_epa_per_db": [0.0, 0.2, 0.1, -0.1, -0.2], "def_epa_per_db": [0.1, -0.2, 0.0, 0.2, -0.1],
        "off_success_rate": [0.4, 0.5, 0.45, 0.35, 0.3], "def_success_rate": [0.45, 0.35, 0.4, 0.5, 0.42],
        "off_sack_rate": [0.12, 0.04, 0.06, 0.08, 0.10], "def_sack_rate": [0.05, 0.11, 0.07, 0.06, 0.08],
        "off_int_rate": [0.03, 0.01, 0.02, 0.02, 0.04], "def_int_rate": [0.01, 0.03, 0.02, 0.02, 0.02],
        "off_pd_epa": [-0.2, 0.1, 0.0, -0.1, -0.3], "def_pd_epa": [0.0, -0.3, -0.1, 0.1, 0.0],
        "off_pd_sack_rate": [0.2, 0.05, 0.1, 0.1, 0.15], "def_pd_sack_rate": [0.08, 0.2, 0.1, 0.1, 0.1],
        "def_front7_havoc": [0.04, 0.09, 0.05, 0.06, np.nan],
    }, index=pd.Index(teams, name="team"))
    return p, assign_tiers(p, set(teams))


def test_two_tables_with_expected_rows():
    p, r = _profile()
    tables = unit_tables("WVU", "Tech", p, r)
    assert [t["title"] for t in tables] == ["Pass protection vs. pass rush", "Passing offense vs. pass defense"]
    assert [row["key"] for row in tables[0]["rows"]] == ["sack_rate", "pd_sack_rate", "front7_havoc"]
    assert [row["key"] for row in tables[1]["rows"]] == ["epa_per_db", "success_rate", "int_rate", "pd_epa"]
    assert tables[0]["offenseTeam"] == "WVU" and tables[0]["defenseTeam"] == "Tech"


def test_unit_rows_have_rank_and_value():
    p, r = _profile()
    row = unit_tables("WVU", "Tech", p, r)[0]["rows"][0]
    assert row["offense"] == {"value": pytest.approx(0.12), "rank": 5, "pct": 0.0}   # worst protection
    assert row["defense"] == {"value": pytest.approx(0.11), "rank": 1, "pct": 100.0}   # best rush
    assert row["edge"] == "clear-defense" and row["format"] == "pct"


def test_offense_only_row_has_null_offense_side():
    p, r = _profile()
    row = unit_tables("WVU", "Tech", p, r)[0]["rows"][2]
    assert row["offense"] == {"value": None, "rank": None, "pct": None} and row["defense"]["rank"] == 1 and row["edge"] is None


def test_unknown_team_gives_nulls_not_crash():
    p, r = _profile()
    row = unit_tables("Nobody", "Tech", p, r)[1]["rows"][0]
    assert row["offense"] == {"value": None, "rank": None, "pct": None} and row["edge"] is None


from cfbm.units import biggest_gap, side_edge


def _row(key, off, dfn):
    return {"key": key, "offense": {"value": 1, "rank": 1, "pct": off}, "defense": {"value": 1, "rank": 1, "pct": dfn}}


def test_plain_label_explain_and_hint():
    p, r = _profile()
    rows = {row["key"]: row for t in unit_tables("WVU", "Tech", p, r) for row in t["rows"]}
    assert rows["int_rate"]["label"] == "Interceptions"
    assert rows["int_rate"]["explain"] == "How often a pass gets picked off"
    assert rows["int_rate"]["hint"] == "Offense: lower is better · Defense: higher is better"
    assert rows["epa_per_db"]["hint"] == "Offense: higher is better · Defense: lower is better"
    assert rows["front7_havoc"]["label"] == "Front-seven disruption"
    assert 0 <= rows["int_rate"]["offense"]["pct"] <= 100


def test_side_edge_average_gap():
    assert side_edge([_row("a", 10, 50), _row("b", 20, 50), _row("c", 14, 50)]) == "clear-defense"
    assert side_edge([_row("a", 55, 50), _row("b", 45, 50)]) == "even"
    assert side_edge([]) is None


def test_biggest_gap_and_missing_pct_skipped():
    rows = [_row("a", 10, 50), _row("b", 20, 50), _row("c", None, 99), _row("d", 80, 50)]
    assert biggest_gap(rows) == "a"
    assert side_edge([_row("c", None, 99)]) is None
    assert biggest_gap([]) is None


def test_run_tables_rows_and_hints():
    from cfbm.units import RUN_TABLES
    p, r = _profile()
    p["off_stuff_rate"] = [0.1, 0.2, 0.15, 0.18, 0.12]
    p["def_stuff_rate"] = [0.2, 0.1, 0.15, 0.12, 0.18]
    r = assign_tiers(p, set(p.index))
    t = unit_tables("WVU", "Tech", p, r, RUN_TABLES)
    labels = [row["label"] for u in t for row in u["rows"]]
    assert labels == ["Yards the line creates", "Runs stuffed", "Short-yardage runs converted",
                      "Points added per run", "Yards past the line (5 to 10)", "Breakaway yards (past 10)"]
    stuff = t[0]["rows"][1]
    assert stuff["hint"] == "Offense: lower is better · Defense: higher is better"
    assert stuff["offense"]["rank"] == 1 and stuff["edge"] is not None


def test_run_tables_without_run_data_are_empty_not_crashing():
    from cfbm.units import RUN_TABLES
    p, r = _profile()
    t = unit_tables("WVU", "Tech", p, r, RUN_TABLES)
    assert all(row["offense"]["value"] is None and row["edge"] is None for u in t for row in u["rows"])
