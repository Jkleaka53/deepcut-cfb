"""Does the shootout pick find real shootouts? Score each training season with a model that never saw it
(leave one season out), then check how often each week's top pick was among that week's 3 highest-scoring
games, against the chance rate (3 / games that week)."""

from __future__ import annotations

import pandas as pd

from cfbm.shootout import fit, predict_side, X_KEYS

MIN_WEEK_GAMES = 4


def held_out(rows: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for s in sorted(rows["season"].unique()):
        m = fit(rows[rows["season"] != s])
        test = rows[rows["season"] == s].copy()
        test["pred"] = [predict_side(m, {k: r[k] for k in X_KEYS}) for _, r in test.iterrows()]
        test = test.dropna(subset=["pred"])
        g = test.groupby("game_id").agg(season=("season", "first"), week_key=("week_key", "first"),
                                        total=("total", "first"), sides=("pred", "size"),
                                        score_min=("pred", "min"), score_sum=("pred", "sum")).reset_index()
        parts.append(g[g["sides"] == 2].drop(columns="sides"))
    return pd.concat(parts, ignore_index=True)


def weekly_hits(df: pd.DataFrame, col: str) -> dict:
    weeks = hits = 0
    chance = 0.0
    for _, w in df.groupby(["season", "week_key"]):
        if len(w) < MIN_WEEK_GAMES:
            continue
        weeks += 1
        chance += 3 / len(w)
        pick = w.loc[w[col].idxmax()]
        rank = int((w["total"] > pick["total"]).sum()) + 1
        hits += rank <= 3
    rate = hits / weeks if weeks else 0.0
    ch = chance / weeks if weeks else 0.0
    return {"weeks": weeks, "hits": hits, "hitRate": round(rate, 3), "chance": round(ch, 3),
            "lift": round(rate / ch, 2) if ch else None}
