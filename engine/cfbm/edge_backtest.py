"""Pick the edge-score cutoffs honestly: score each training season with a model that never saw it
(leave one season out), then find where the favored team's win rate stops being a coin flip (Even)
and where it almost always holds (Big)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm.edge_score import to_score
from cfbm.swing_data import KEYS
from cfbm.swing_model import train

EVEN_MAX_RATE = 0.58
BIG_MIN_RATE = 0.85
BIG_MIN_GAMES = 200
BIG_FALLBACK = 9.0
GRID = np.arange(0.5, 10.01, 0.5)


def frame_linear(model: dict, frame: pd.DataFrame, keys=KEYS) -> np.ndarray:
    """Home-perspective linear score for training-frame rows (they already carry f_k and home)."""
    lin = model["intercept"] + model["home"]["coef"] * frame["home"].to_numpy(float)
    for k in keys:
        f = model["features"][k]
        lin = lin + f["coef"] * (frame[f"f_{k}"].to_numpy(float) - f["mean"]) / f["sd"]
    return lin


def held_out(frame: pd.DataFrame, tg: pd.DataFrame, keys=KEYS) -> pd.DataFrame:
    parts = []
    for s in sorted(frame["season"].unique()):
        test = frame[frame["season"] == s]
        m = train(frame[frame["season"] != s], tg, keys=keys, resamples=0)
        lin = frame_linear(m, test, keys)
        won = test["home_win"].to_numpy(int)
        parts.append(pd.DataFrame({
            "season": s,
            "score": [to_score(v, m["scale"]["overall"]) for v in lin],
            "favored_won": np.where(lin >= 0, won, 1 - won),
        }))
    return pd.concat(parts, ignore_index=True)


def _rate(df: pd.DataFrame) -> float:
    return float(df["favored_won"].mean()) if len(df) else float("nan")


def pick_cutoffs(df: pd.DataFrame) -> tuple[float, float]:
    # Even ends where games stop being a coin flip locally: the first half-point score window
    # whose favored-team win rate tops EVEN_MAX_RATE. (A cumulative rate below c would let a big
    # pile of true coin flips hide clearly lopsided games, which is the bug this score fixes.)
    slight = GRID[-1]
    for c in np.concatenate([[0.0], GRID]):
        window = df[(df["score"] >= c) & (df["score"] < c + 0.5)]
        if len(window) and _rate(window) > EVEN_MAX_RATE:
            slight = max(c, GRID[0])
            break
    big = BIG_FALLBACK
    for c in GRID:
        above = df[df["score"] >= c]
        if c > slight and len(above) >= BIG_MIN_GAMES and _rate(above) >= BIG_MIN_RATE:
            big = c
            break
    return float(slight), float(max(big, slight + 0.5))


def band_table(df: pd.DataFrame, slight: float, big: float) -> list[dict]:
    parts = {"even": df[df["score"] < slight], "slight": df[(df["score"] >= slight) & (df["score"] < big)],
             "clear": df[df["score"] >= big]}
    return [{"band": b, "games": int(len(p)), "favoredWinRate": round(_rate(p), 3) if len(p) else None}
            for b, p in parts.items()]
