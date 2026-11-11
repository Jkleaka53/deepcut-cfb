"""Edge score: how lopsided a matchup is, 0 to 10, from the swing model's nine pregame stats plus
home field. The number is a percentile against training games (2015-2025), never a win %. The
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


def overall_linear(model: dict, pre: pd.DataFrame, home: str, away: str, neutral: bool) -> float | None:
    """Home-perspective linear score (>0 favors home). None if a team is missing or no stat is usable."""
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
    return model["intercept"] + (0.0 if neutral else model["home"]["coef"]) + sum(terms)


def to_score(value: float, quantiles: list[float]) -> float:
    return round(float(np.interp(abs(value), quantiles, np.linspace(0, 10, len(quantiles)))), 1)


def band(score: float, slight: float = config.EDGE_SCORE_SLIGHT, big: float = config.EDGE_SCORE_BIG) -> str:
    return "even" if score < slight else ("clear" if score >= big else "slight")


def overall_edge(model: dict, pre: pd.DataFrame, home: str, away: str, neutral: bool) -> dict | None:
    lin = overall_linear(model, pre, home, away, neutral)
    if lin is None:
        return None
    score = to_score(lin, model["scale"]["overall"])
    b = band(score)
    return {"edge": b, "team": None if b == "even" else (home if lin > 0 else away), "score": score}
