"""Shootout of the Week: the game most likely to be pure offense on both sides. A ridge regression of one
team's points from that offense against that defense (pregame season-to-date means); a game's score is the
WEAKER side's prediction, so both offenses must qualify. Predicted points never leave the engine."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from cfbm.gotw import _week
from cfbm.plays import game_orders
from cfbm.swing_data import MIN_PRIOR, _priors, apply_orders, stat_cols

SHOOT_FEATURES = [("ppa", "ppa", 1, "Points added per play"), ("sr", "successRate", 1, "Success rate"),
                  ("expl", "explosiveness", 1, "Explosiveness"), ("plays", "plays", 1, "Plays per game")]
SHOOT_COLS = stat_cols(SHOOT_FEATURES)
X_KEYS = ("x_ppa", "x_sr", "x_expl", "x_pace", "home")


def _f(v) -> float:
    return math.nan if v is None or pd.isna(v) else float(v)


def side_features(pre: pd.DataFrame, off: str, dfn: str, home: int) -> dict[str, float]:
    """One offense against one defense: the offense's average plus what the defense allows."""
    o, d = pre.loc[off], pre.loc[dfn]
    return {"x_ppa": _f(o["off_ppa"]) + _f(d["def_ppa"]), "x_sr": _f(o["off_sr"]) + _f(d["def_sr"]),
            "x_expl": _f(o["off_expl"]) + _f(d["def_expl"]), "x_pace": _f(o["off_plays"]) + _f(d["def_plays"]),
            "home": float(home)}


def training_rows(tg: pd.DataFrame, games_by_id: dict[int, dict], fbs_by_season: dict[int, set[str]]) -> pd.DataFrame:
    cols = ["game_id", "season", "order", "week_key", "side", "points", "total", *X_KEYS]
    by_season: dict[int, list[dict]] = {}
    for g in games_by_id.values():
        by_season.setdefault(g.get("season"), []).append(g)
    orders: dict[int, int] = {}
    for gs in by_season.values():
        orders.update(game_orders(gs))
    tg = apply_orders(tg, orders)
    mask = pd.Series([t in fbs_by_season.get(s, set()) and o in fbs_by_season.get(s, set())
                      for s, t, o in zip(tg["season"], tg["team"], tg["opponent"])], index=tg.index, dtype=bool)
    fbs_rows = tg[mask]
    if fbs_rows.empty:
        return pd.DataFrame(columns=cols)
    pri = _priors(fbs_rows, SHOOT_COLS).set_index(["game_id", "team"])
    pri = pri.rename(columns={"prior_games": "games"})
    rows = []
    for gid, g in games_by_id.items():
        h, a = g.get("homeTeam"), g.get("awayTeam")
        hp, ap = g.get("homePoints"), g.get("awayPoints")
        if hp is None or ap is None or (gid, h) not in pri.index or (gid, a) not in pri.index:
            continue
        pre = pd.DataFrame([pri.loc[(gid, h)], pri.loc[(gid, a)]], index=[h, a])
        if (pre["games"] < MIN_PRIOR).any():
            continue
        neutral = bool(g.get("neutralSite"))
        for side, off, dfn, pts in (("home", h, a, hp), ("away", a, h, ap)):
            x = side_features(pre, off, dfn, int(side == "home" and not neutral))
            rows.append({"game_id": gid, "season": g["season"], "order": orders.get(gid, 0), "week_key": _week(g),
                         "side": side, "points": pts, "total": hp + ap, **x})
    return pd.DataFrame(rows, columns=cols)


def fit(rows: pd.DataFrame, l2: float = 1.0) -> dict:
    """Ridge regression of one team's points on standardized side features (intercept unpenalized)."""
    r = rows.dropna(subset=list(X_KEYS) + ["points"])
    means = {k: float(r[k].mean()) for k in X_KEYS}
    sds = {k: float(r[k].std()) or 1.0 for k in X_KEYS}
    X = np.column_stack([np.ones(len(r))] + [((r[k] - means[k]) / sds[k]).to_numpy(float) for k in X_KEYS])
    y = r["points"].to_numpy(float)
    pen = np.full(X.shape[1], l2)
    pen[0] = 0.0
    beta = np.linalg.solve(X.T @ X + np.diag(pen), X.T @ y)
    return {"means": means, "sds": sds, "intercept": float(beta[0]),
            "coef": {k: float(b) for k, b in zip(X_KEYS, beta[1:])}}


def predict_side(model: dict, x: dict[str, float]) -> float | None:
    if any(math.isnan(_f(x.get(k))) for k in X_KEYS):
        return None
    return model["intercept"] + sum(model["coef"][k] * (x[k] - model["means"][k]) / model["sds"][k] for k in X_KEYS)


def _sides(model: dict, pre: pd.DataFrame, home: str, away: str, neutral: bool) -> tuple[float, float] | None:
    if home not in pre.index or away not in pre.index or (pre.loc[[home, away], "games"] < MIN_PRIOR).any():
        return None
    h = predict_side(model, side_features(pre, home, away, int(not neutral)))
    a = predict_side(model, side_features(pre, away, home, 0))
    return None if h is None or a is None else (h, a)


def game_score(model: dict, pre: pd.DataFrame, home: str, away: str, neutral: bool) -> float | None:
    """The weaker offense's predicted points: both sides must score for a shootout. Internal only."""
    s = _sides(model, pre, home, away, neutral)
    return None if s is None else min(s)


def predicted_total(model: dict, pre: pd.DataFrame, home: str, away: str, neutral: bool) -> float | None:
    """Backtest comparison only; never exported."""
    s = _sides(model, pre, home, away, neutral)
    return None if s is None else sum(s)
