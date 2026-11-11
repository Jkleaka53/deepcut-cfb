"""Would Upset Watch have found real upsets? For each training season, our pregame chance comes from a model
that never saw that season (edge_backtest.held_out); the pros' chance comes from the spread (old seasons have
no moneylines), on a curve fitted to the history. Each week's pick is the biggest gap (upset.gap)."""

from __future__ import annotations

import math

import pandas as pd

from cfbm.gotw import _week
from cfbm.upset import gap, spread_of, spread_prob


def covered(dog: str, spread: float, home_margin: float) -> bool:
    """Underdog won outright or lost by less than the spread. spread is home-side (negative = home favored)."""
    return home_margin + spread > 0 if dog == "home" else home_margin + spread < 0


def join(held: pd.DataFrame, lines_by_id: dict[int, dict], games_by_id: dict[int, dict], k: float) -> pd.DataFrame:
    rows = []
    for gid, lin in zip(held["game_id"], held["lin"]):
        g, ln = games_by_id.get(int(gid)), lines_by_id.get(int(gid))
        if g is None or ln is None or g.get("homePoints") is None or g.get("awayPoints") is None:
            continue
        sp = spread_of(ln)
        if sp is None:
            continue
        rows.append({"season": g["season"], "week_key": _week(g), "game_id": int(gid),
                     "our_home": 1 / (1 + math.exp(-lin)), "book_home": spread_prob(sp, k), "spread": sp,
                     "home_margin": g["homePoints"] - g["awayPoints"]})
    return pd.DataFrame(rows, columns=["season", "week_key", "game_id", "our_home", "book_home", "spread", "home_margin"])


def weekly_picks(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (season, wk), w in df.groupby(["season", "week_key"]):
        best = None
        for r in w.itertuples():
            gp = gap(r.our_home, r.book_home)
            if gp and (best is None or gp[1] > best[1][1]):
                best = (r, gp)
        if best is None:
            continue
        r, (dog, g) = best
        won = r.home_margin > 0 if dog == "home" else r.home_margin < 0
        out.append({"season": season, "week_key": wk, "game_id": r.game_id, "dog": dog, "gap": g,
                    "book_dog": r.book_home if dog == "home" else 1 - r.book_home,
                    "dog_won": int(won), "dog_covered": int(covered(dog, r.spread, r.home_margin))})
    return pd.DataFrame(out)


def summary(picks: pd.DataFrame) -> dict:
    n = len(picks)
    return {"weeks": n, "coverRate": round(float(picks["dog_covered"].mean()), 3) if n else None,
            "upsetRate": round(float(picks["dog_won"].mean()), 3) if n else None,
            "bookUpsetRate": round(float(picks["book_dog"].mean()), 3) if n else None}
