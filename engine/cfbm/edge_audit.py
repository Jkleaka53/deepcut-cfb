"""How the edge model compares with the betting market on held-out seasons. Backtest only: the market's
chance comes from the closing spread and never reaches the site."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm.upset import fit_spread_scale, spread_of, spread_prob


def log_loss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def market_frame(games_by_id: dict[int, dict], lines_by_id: dict[int, dict],
                 fbs_by_season: dict[int, set[str]]) -> pd.DataFrame:
    """One row per decided FBS-vs-FBS game with a spread; book_home from a curve fitted on these rows."""
    rows = []
    for gid, g in games_by_id.items():
        fbs = fbs_by_season.get(g.get("season"), set())
        hp, ap = g.get("homePoints"), g.get("awayPoints")
        ln = lines_by_id.get(gid)
        sp = spread_of(ln) if ln else None
        if g.get("homeTeam") not in fbs or g.get("awayTeam") not in fbs or hp is None or ap is None or hp == ap \
                or sp is None:
            continue
        rows.append({"game_id": int(gid), "season": g["season"], "home_win": int(hp > ap), "spread": sp})
    df = pd.DataFrame(rows, columns=["game_id", "season", "home_win", "spread"])
    if df.empty:
        return df.assign(book_home=[])
    k = fit_spread_scale(df["spread"].to_numpy(), df["home_win"].to_numpy())
    df["book_home"] = [spread_prob(s, k) for s in df["spread"]]
    df.attrs["k"] = k
    return df


def compare(held: pd.DataFrame, market: pd.DataFrame, subset: pd.Series | None = None) -> dict:
    """Model (from held-out linear scores) against the market on the games both have."""
    h = held if subset is None else held[subset.to_numpy(bool)]
    j = h[["game_id", "lin"]].merge(market, on="game_id")
    if j.empty:
        return {"games": 0, "modelLogLoss": None, "modelPicks": None, "marketLogLoss": None, "marketPicks": None}
    y = j["home_win"].to_numpy(float)
    ours = 1 / (1 + np.exp(-j["lin"].to_numpy(float)))
    book = j["book_home"].to_numpy(float)
    return {"games": int(len(j)),
            "modelLogLoss": round(log_loss(ours, y), 4), "modelPicks": round(float(((ours > 0.5) == (y == 1)).mean()), 3),
            "marketLogLoss": round(log_loss(book, y), 4), "marketPicks": round(float(((book > 0.5) == (y == 1)).mean()), 3)}


def elo_continuity(games: list[dict], fbs: set[str] | None = None) -> float:
    """Share of consecutive same-season games per team where the pregame Elo equals the team's previous
    postgame Elo. Near 1.0 means a pregame value holds nothing from the game it belongs to. With fbs,
    only games between two of those teams count: the only rows whose Elo the edge model reads."""
    by_team: dict[tuple, list[tuple]] = {}
    for g in games:
        if fbs is not None and (g.get("homeTeam") not in fbs or g.get("awayTeam") not in fbs):
            continue
        for side in ("home", "away"):
            pre, post = g.get(f"{side}PregameElo"), g.get(f"{side}PostgameElo")
            if pre is None or post is None:
                continue
            by_team.setdefault((g.get("season"), g[f"{side}Team"]), []).append((g.get("startDate") or "", pre, post))
    hits = total = 0
    for rows in by_team.values():
        rows.sort()
        for (_, _, prev_post), (_, pre, _) in zip(rows, rows[1:]):
            total += 1
            hits += int(pre == prev_post)
    return hits / total if total else float("nan")
