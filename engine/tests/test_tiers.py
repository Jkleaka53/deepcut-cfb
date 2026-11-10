import math

import numpy as np
import pandas as pd

from cfbm.tiers import METRIC_DIRECTION, SKILLS, assign_tiers


def _profile(n, **overrides):
    teams = [f"T{i}" for i in range(n)]
    base = {
        "off_epa_per_db": np.linspace(0.3, -0.3, n),
        "def_epa_per_db": np.linspace(-0.3, 0.3, n),   # T0 allows least -> best defense
        "off_sack_rate": np.linspace(0.03, 0.12, n),   # T0 allows fewest sacks
        "def_sack_rate": np.linspace(0.12, 0.03, n),   # T0 gets most sacks
        "def_front7_havoc": np.linspace(0.10, 0.02, n),
    }
    base.update(overrides)
    return pd.DataFrame(base, index=pd.Index(teams, name="team"))


def _counts(df, skill):
    return df[f"{skill}_tier"].value_counts().sort_index().tolist()


def test_thirds_split_of_nine():
    t = assign_tiers(_profile(9), {f"T{i}" for i in range(9)})
    for s in SKILLS:
        assert _counts(t, s) == [3, 3, 3], s


def test_thirds_of_134():
    t = assign_tiers(_profile(134), {f"T{i}" for i in range(134)})
    assert _counts(t, "pass_defense") == [45, 45, 44]


def test_fcs_team_excluded():
    t = assign_tiers(_profile(10), {f"T{i}" for i in range(9)})
    assert "T9" not in t.index and len(t) == 9


def test_lower_epa_allowed_is_better_defense():
    t = assign_tiers(_profile(9), {f"T{i}" for i in range(9)})
    assert t.loc["T0", "pass_defense_rank"] == 1 and t.loc["T0", "pass_defense_tier"] == 1
    assert t.loc["T8", "pass_defense_tier"] == 3


def test_pass_rush_and_protection_directions():
    t = assign_tiers(_profile(9), {f"T{i}" for i in range(9)})
    assert t.loc["T0", "pass_rush_tier"] == 1 and t.loc["T0", "pass_protection_tier"] == 1
    assert t.loc["T8", "pass_rush_tier"] == 3


def test_nan_score_gets_no_tier():
    p = _profile(9)
    p.loc["T4", "def_epa_per_db"] = np.nan
    t = assign_tiers(p, {f"T{i}" for i in range(9)})
    assert math.isnan(t.loc["T4", "pass_defense_tier"])
    assert t["pass_defense_tier"].notna().sum() == 8


def test_metric_rank_and_pct_respect_direction():
    t = assign_tiers(_profile(9), {f"T{i}" for i in range(9)})
    assert METRIC_DIRECTION["off_sack_rate"] == -1
    assert t.loc["T0", "off_sack_rate_rank"] == 1 and t.loc["T0", "off_sack_rate_pct"] == 100
    assert t.loc["T8", "off_sack_rate_pct"] == 0
    assert t.loc["T0", "def_sack_rate_rank"] == 1
