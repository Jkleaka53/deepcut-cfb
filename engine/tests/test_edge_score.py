import numpy as np
import pandas as pd
import pytest

from cfbm.edge_score import band, edge, linear, overall_linear, to_score
from cfbm.swing_data import KEYS

Q = list(np.linspace(0, 2, 101))


def model(coefs=None):
    coefs = coefs or {"pass_ppa": 1.0}
    return {"intercept": 0.0, "home": {"coef": 0.3},
            "scale": {"overall": Q},
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


def test_linear_drops_home_field_on_neutral_site_and_skips_nan():
    p = pre(Home={}, Away={})
    assert overall_linear(model(), p, "Home", "Away", neutral=False) == pytest.approx(0.3)
    assert overall_linear(model(), p, "Home", "Away", neutral=True) == pytest.approx(0.0)
    m = model({"pass_ppa": 1.0, "pass_sr": 1.0})
    p = pre(Home={"pass_ppa": (np.nan, 0.0), "pass_sr": (0.5, 0.0)}, Away={})
    assert overall_linear(m, p, "Home", "Away", neutral=True) == pytest.approx(0.5)
    assert overall_linear(model(), pre(Home={}), "Home", "Nobody", neutral=False) is None


# --- the edge model's score (nine stats + Elo + margin) ----------------------------------------------------
EDGE_MODEL = {"intercept": 0.0, "home": {"coef": 0.3}, "scale": {"overall": Q},
              "features": {**{k: {"coef": 0.2, "mean": 0.0, "sd": 1.0} for k in KEYS},
                           "elo": {"coef": 0.5, "mean": 0.0, "sd": 200.0}, "margin": {"coef": 0.1, "mean": 0.0, "sd": 10.0}}}


def feats(**over):
    return {**{k: 0.0 for k in KEYS}, "elo": 0.0, "margin": 0.0, **over}


def test_linear_sums_standardized_inputs_and_home_field():
    assert linear(EDGE_MODEL, feats(elo=400.0, margin=10.0, pass_ppa=1.0), neutral=True) == pytest.approx(1.0 + 0.1 + 0.2)
    assert linear(EDGE_MODEL, feats(), neutral=False) == pytest.approx(0.3)


def test_edge_uses_elo_when_stats_are_empty():
    e = edge(EDGE_MODEL, feats(elo=400.0), "H", "A", neutral=True)
    assert e == {"edge": "slight", "team": "H", "score": 5.0}


def test_edge_favors_away_and_bands_even():
    assert edge(EDGE_MODEL, feats(elo=-400.0), "H", "A", neutral=True)["team"] == "A"
    assert edge(EDGE_MODEL, feats(), "H", "A", neutral=True) == {"edge": "even", "team": None, "score": 0.0}


def test_edge_none_without_features():
    assert edge(EDGE_MODEL, None, "H", "A", False) is None
