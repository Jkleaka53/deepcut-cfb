"""Which stat gaps, known before kickoff, have tracked with winning. Logistic regression on
standardized matchup differentials (numpy IRLS), with bootstrap intervals and a volatility measure."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm.swing_data import KEYS

QUANTS = np.linspace(0, 1, 101)


def fit_logit(X: np.ndarray, y: np.ndarray, l2: float = 1e-3, iters: int = 50) -> np.ndarray:
    beta = np.zeros(X.shape[1])
    pen = np.full(X.shape[1], l2)
    pen[0] = 0.0  # no penalty on the intercept
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ beta)))
        w = p * (1 - p)
        grad = X.T @ (y - p) - pen * beta
        hess = (X * w[:, None]).T @ X + np.diag(pen)
        step = np.linalg.solve(hess, grad)
        beta += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return beta


def _volatility(tg: pd.DataFrame, key: str) -> float:
    ratios = []
    for side in ("off", "def"):
        col = f"{side}_{key}"
        if col not in tg:
            continue
        g = tg.groupby(["season", "team"])[col]
        within = float(g.std().mean())
        between = float(g.mean().std())
        if between > 0 and not np.isnan(within):
            ratios.append(within / between)
    return round(float(np.mean(ratios)), 4) if ratios else 0.0


def _quantiles(values: np.ndarray) -> list[float]:
    v = np.abs(values[~np.isnan(values)])
    return [round(float(x), 6) for x in np.quantile(v, QUANTS)]


def _side_win_rate(ha: pd.Series, aa: pd.Series, side_mean: float, home_win: pd.Series) -> float:
    """Per side of the ball (one offense against one defense, as each swing reason shows it): how often the
    team that was ahead in that matchup won. Home side: home offense vs away defense (ha); away side: aa.
    A description of past seasons, shown as text; never a probability for a game."""
    won = home_win.astype(int)
    parts = []
    for adv, team_won in ((ha, won), (aa, 1 - won)):
        ok = adv.notna() & (adv != side_mean)
        parts.append((adv[ok] > side_mean) == (team_won[ok] == 1))
    hits = pd.concat(parts)
    return round(float(hits.mean()), 3) if len(hits) else 0.5


def train(frame: pd.DataFrame, tg: pd.DataFrame, keys: list[str] = KEYS, resamples: int = 200, seed: int = 7) -> dict:
    means = {k: float(frame[f"f_{k}"].mean()) for k in keys}
    sds = {k: float(frame[f"f_{k}"].std()) or 1.0 for k in keys}
    X = np.column_stack([np.ones(len(frame)), frame["home"].to_numpy(float)] +
                        [((frame[f"f_{k}"] - means[k]) / sds[k]).to_numpy() for k in keys])
    y = frame["home_win"].to_numpy(float)
    beta = fit_logit(X, y)
    if resamples > 0:
        rng = np.random.default_rng(seed)
        boots = np.array([fit_logit(X[idx], y[idx]) for idx in (rng.integers(0, len(y), len(y)) for _ in range(resamples))])
        lo, hi = np.percentile(boots, 2.5, axis=0), np.percentile(boots, 97.5, axis=0)
    else:
        lo = hi = beta
    feats = {}
    for i, k in enumerate(keys, start=2):
        side = pd.concat([frame[f"ha_{k}"], frame[f"aa_{k}"]])
        feats[k] = {"coef": round(float(beta[i]), 4), "lo": round(float(lo[i]), 4), "hi": round(float(hi[i]), 4),
                    # Only a clearly positive effect counts: a negative weight on a stat whose
                    # better value means winning is overlap with other stats, not a driver.
                    "proven": bool(lo[i] > 0), "importance": round(max(0.0, float(beta[i])), 4),
                    "volatility": _volatility(tg, k), "mean": round(means[k], 6), "sd": round(sds[k], 6),
                    "sideMean": round(float(side.mean()), 6), "sideSd": round(float(side.std()) or 1.0, 6),
                    "matchupWinRate": _side_win_rate(frame[f"ha_{k}"], frame[f"aa_{k}"], float(side.mean()),
                                                     frame["home_win"])}
    # How lopsided training games were, so a game's edge can be scored 0-10 by percentile.
    # Built from the stored (rounded) values so runtime scoring matches exactly.
    intercept, home = round(float(beta[0]), 4), round(float(beta[1]), 4)
    lin = intercept + home * frame["home"].to_numpy(float)
    for k in keys:
        f = feats[k]
        lin = lin + f["coef"] * (frame[f"f_{k}"].to_numpy(float) - f["mean"]) / f["sd"]
    scale = {"overall": _quantiles(lin)}
    return {"seasons": sorted(int(s) for s in frame["season"].unique()), "games": int(len(frame)),
            "intercept": intercept, "scale": scale,
            "home": {"coef": home, "lo": round(float(lo[1]), 4), "hi": round(float(hi[1]), 4)},
            "features": feats}
