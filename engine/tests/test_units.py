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
    assert row["offense"] == {"value": pytest.approx(0.12), "rank": 5}   # worst protection
    assert row["defense"] == {"value": pytest.approx(0.11), "rank": 1}   # best rush
    assert row["edge"] == "clear-defense" and row["format"] == "pct"


def test_offense_only_row_has_null_offense_side():
    p, r = _profile()
    row = unit_tables("WVU", "Tech", p, r)[0]["rows"][2]
    assert row["offense"] == {"value": None, "rank": None} and row["defense"]["rank"] == 1 and row["edge"] is None


def test_unknown_team_gives_nulls_not_crash():
    p, r = _profile()
    row = unit_tables("Nobody", "Tech", p, r)[1]["rows"][0]
    assert row["offense"] == {"value": None, "rank": None} and row["edge"] is None
