import numpy as np
import pandas as pd
import pytest

from cfbm.edge_score import band, overall_edge, overall_linear, section_edge, section_linear, to_score
from cfbm.swing_data import KEYS, PASS_KEYS

Q = list(np.linspace(0, 2, 101))


def model(coefs=None):
    coefs = coefs or {"pass_ppa": 1.0}
    return {"intercept": 0.0, "home": {"coef": 0.3},
            "scale": {"overall": Q, "pass": Q, "run": Q},
            "features": {k: {"coef": coefs.get(k, 0.0), "mean": 0.0, "sd": 1.0, "sideMean": 0.0} for k in KEYS}}


def pre(**teams):
    """teams: name -> {key: (off, def_allowed)}; unspecified keys 0/0."""
    rows = {}
    for t, vals in teams.items():
        row = {"games": 6}
        for k in KEYS:
            o, d = vals.get(k, (0.0, 0.0))
            row[f"off_{k}"], row[f"def_{k}"] = o, d
        rows[t] = row
    return pd.DataFrame.from_dict(rows, orient="index")


def test_to_score_percentile():
    assert to_score(1.0, Q) == 5.0
    assert to_score(-1.0, Q) == 5.0
    assert to_score(5.0, Q) == 10.0
    assert to_score(0, Q) == 0.0


def test_band_cutoffs():
    assert band(0.9, 1, 5) == "even"
    assert band(1.0, 1, 5) == "slight"
    assert band(5.0, 1, 5) == "clear"


def test_overall_favors_better_passing_team():
    p = pre(Home={"pass_ppa": (0.6, 0.0)}, Away={})
    out = overall_edge(model(), p, "Home", "Away", neutral=True)
    assert out["team"] == "Home" and out["score"] > 0


def test_overall_away_side_favored():
    p = pre(Home={}, Away={"pass_ppa": (0.6, 0.0)})
    out = overall_edge(model(), p, "Home", "Away", neutral=True)
    assert out["team"] == "Away"


def test_neutral_drops_home_field():
    p = pre(Home={}, Away={})
    out = overall_edge(model(), p, "Home", "Away", neutral=True)
    assert out == {"edge": "even", "team": None, "score": 0.0}
    assert overall_linear(model(), p, "Home", "Away", neutral=False) == pytest.approx(0.3)


def test_section_edge_is_one_sided():
    p = pre(Off={"pass_ppa": (0.4, 0.0)}, Def={"pass_ppa": (0.0, 0.2)})
    e, s = section_edge(model(), p, "Off", "Def", "pass")
    assert e.endswith("-offense") and s > 0
    p2 = pre(Off={"pass_ppa": (-0.4, 0.0)}, Def={"pass_ppa": (0.0, -0.2)})
    e2, _ = section_edge(model(), p2, "Off", "Def", "pass")
    assert e2.endswith("-defense")


def test_nan_feature_skipped():
    m = model({"pass_ppa": 1.0, "pass_sr": 1.0})
    p = pre(Off={"pass_ppa": (np.nan, 0.0), "pass_sr": (0.5, 0.0)}, Def={})
    assert section_linear(m, p, "Off", "Def", PASS_KEYS) == pytest.approx(0.5)
    p2 = pre(Off={k: (np.nan, 0.0) for k in PASS_KEYS}, Def={})
    assert section_edge(m, p2, "Off", "Def", "pass") is None


def test_missing_team_returns_none():
    p = pre(Home={})
    assert overall_edge(model(), p, "Home", "Nobody", neutral=False) is None
