"""Edge score: how lopsided a matchup is, 0 to 10, from the edge model (edge_model.py: nine pregame stats,
prior strength, scoring margin, home field). overall_linear is the nine-stat score (plus extra inputs for
the Upset Watch model, which failed its backtest on the edge model, owner 2026-11-10). The number is a percentile against training games (2015-2025), never a win %. The
model itself is never published (export.py), so a score can't be read back as odds. Labels (Even / Slight / Big) come from backtested cutoffs."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from cfbm import config
from cfbm.swing_data import KEYS, side_advantage


def _adv(pre: pd.DataFrame, off: str, dfn: str, k: str) -> float:
    v = side_advantage(pre.loc[off, f"off_{k}"], pre.loc[dfn, f"def_{k}"], k)
    return float(v) if v is not None and not pd.isna(v) else math.nan


def overall_linear(model: dict, pre: pd.DataFrame, home: str, away: str, neutral: bool,
                   extra: dict | None = None) -> float | None:
    """Nine-stat swing model, or the Upset Watch model (nine stats plus the inputs in extra, e.g.
    team_prior.diffs; a missing one counts as no difference). Home-perspective linear score (>0 favors home).
    None if a team is missing or no stat is usable."""
    if home not in pre.index or away not in pre.index:
        return None
    terms = []
    for k in KEYS:
        f = model["features"].get(k)
        if f is None:
            continue
        diff = _adv(pre, home, away, k) - _adv(pre, away, home, k)
        if not math.isnan(diff):
            terms.append(f["coef"] * (diff - f["mean"]) / f["sd"])
    if not terms:
        return None
    for k, f in model["features"].items():
        if k not in KEYS:
            terms.append(f["coef"] * ((extra or {}).get(k, 0.0) - f["mean"]) / f["sd"])
    return model["intercept"] + (0.0 if neutral else model["home"]["coef"]) + sum(terms)


def to_score(value: float, quantiles: list[float]) -> float:
    return round(float(np.interp(abs(value), quantiles, np.linspace(0, 10, len(quantiles)))), 1)


def band(score: float, slight: float = config.EDGE_SCORE_SLIGHT, big: float = config.EDGE_SCORE_BIG) -> str:
    return "even" if score < slight else ("clear" if score >= big else "slight")


def linear(model: dict, feats: dict[str, float], neutral: bool) -> float:
    """Home-perspective linear score (>0 favors home) from the edge model and one game's inputs
    (edge_model.features)."""
    lin = model["intercept"] + (0.0 if neutral else model["home"]["coef"])
    for k, f in model["features"].items():
        lin += f["coef"] * (feats[k] - f["mean"]) / f["sd"]
    return lin


def edge(model: dict, feats: dict[str, float] | None, home: str, away: str, neutral: bool) -> dict | None:
    """The game's edge: band, favored team and 0-10 score. None when the game has no inputs (no Elo rating)."""
    if feats is None:
        return None
    lin = linear(model, feats, neutral)
    score = to_score(lin, model["scale"]["overall"])
    b = band(score)
    return {"edge": b, "team": None if b == "even" else (home if lin > 0 else away), "score": score}
