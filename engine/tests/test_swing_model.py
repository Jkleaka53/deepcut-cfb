import numpy as np
import pandas as pd
import pytest

from cfbm.swing_model import fit_logit, train


def _synthetic(n=4000, seed=1):
    rng = np.random.default_rng(seed)
    a, b = rng.normal(0, 2.0, n), rng.normal(0, 1.0, n)
    home = rng.integers(0, 2, n)
    logit = 1.0 * (a / 2.0) + 0.3 * home
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    fr = pd.DataFrame({"game_id": range(n), "season": 2019, "home_win": y, "home": home,
                       "f_a": a, "f_b": b, "ha_a": a / 2, "aa_a": -a / 2, "ha_b": b / 2, "aa_b": -b / 2})
    teams = np.repeat([f"T{i}" for i in range(50)], 10)
    tg = pd.DataFrame({"season": 2019, "team": teams,
                       "off_a": np.repeat(rng.normal(0, 1, 50), 10) + rng.normal(0, 1, 500),
                       "def_a": np.repeat(rng.normal(0, 1, 50), 10) + rng.normal(0, 1, 500),
                       "off_b": np.repeat(rng.normal(0, 1, 50), 10), "def_b": np.repeat(rng.normal(0, 1, 50), 10)})
    return fr, tg


def test_fit_logit_recovers_known_coefficients():
    rng = np.random.default_rng(3)
    X = np.column_stack([np.ones(5000), rng.normal(size=5000)])
    y = (rng.random(5000) < 1 / (1 + np.exp(-(0.2 + 1.5 * X[:, 1])))).astype(int)
    beta = fit_logit(X, y)
    assert beta[1] == pytest.approx(1.5, abs=0.15) and beta[0] == pytest.approx(0.2, abs=0.15)


def test_train_finds_the_real_driver_and_rejects_noise():
    fr, tg = _synthetic()
    m = train(fr, tg, keys=["a", "b"], resamples=60)
    a, b = m["features"]["a"], m["features"]["b"]
    assert a["coef"] == pytest.approx(1.0, abs=0.15) and a["proven"] is True
    assert b["proven"] is False
    assert a["importance"] == abs(a["coef"])
    assert m["games"] == 4000 and m["seasons"] == [2019]


def test_volatility_zero_when_stat_never_moves_within_a_team():
    fr, tg = _synthetic()
    m = train(fr, tg, keys=["a", "b"], resamples=10)
    assert m["features"]["b"]["volatility"] == pytest.approx(0.0, abs=1e-9)
    assert m["features"]["a"]["volatility"] > 0.5


def test_side_stats_and_determinism():
    fr, tg = _synthetic()
    m1 = train(fr, tg, keys=["a", "b"], resamples=20)
    m2 = train(fr, tg, keys=["a", "b"], resamples=20)
    assert m1 == m2
    assert m1["features"]["a"]["sideSd"] > 0


def test_negative_weight_is_never_a_driver():
    fr, tg = _synthetic()
    fr["f_a"] = -fr["f_a"]  # now a better 'a' means losing: an artifact, not a driver
    m = train(fr, tg, keys=["a", "b"], resamples=30)
    a = m["features"]["a"]
    assert a["coef"] < 0 and a["proven"] is False and a["importance"] == 0


def test_train_keeps_intercept():
    fr, tg = _synthetic()
    m = train(fr, tg, keys=["a", "b"], resamples=5)
    assert isinstance(m["intercept"], float) and abs(m["intercept"]) < 0.5


def test_scale_quantiles_shape():
    fr, tg = _synthetic()
    m = train(fr, tg, keys=["a", "b"], resamples=5)
    for name in ("overall",):
        q = m["scale"][name]
        assert len(q) == 101 and q[0] >= 0 and all(x <= y for x, y in zip(q, q[1:]))


def test_overall_scale_matches_linear():
    fr, tg = _synthetic()
    m = train(fr, tg, keys=["a", "b"], resamples=5)
    L = m["intercept"] + m["home"]["coef"] * fr["home"]
    for k in ("a", "b"):
        f = m["features"][k]
        L = L + f["coef"] * (fr[f"f_{k}"] - f["mean"]) / f["sd"]
    assert float(np.median(np.abs(L))) == pytest.approx(m["scale"]["overall"][50], rel=1e-3)


def test_resamples_zero_skips_bootstrap():
    fr, tg = _synthetic()
    m = train(fr, tg, keys=["a", "b"], resamples=0)
    assert m["features"]["a"]["lo"] == m["features"]["a"]["coef"]
