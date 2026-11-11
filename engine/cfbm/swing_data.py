"""Team-level game stats for the swing-factor model, and matchup features known before kickoff."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm.plays import game_orders, order_key

# (key, CFBD advanced-stats path, direction for the offense (+1 higher is better), label)
FEATURES: list[tuple[str, str, int, str]] = [
    ("pass_ppa", "passingPlays.ppa", 1, "Points added per pass"),
    ("pass_sr", "passingPlays.successRate", 1, "Successful passes"),
    ("pd_sr", "passingDowns.successRate", 1, "Passing-down success"),
    ("rush_ppa", "rushingPlays.ppa", 1, "Points added per run"),
    ("rush_sr", "rushingPlays.successRate", 1, "Successful runs"),
    ("sd_sr", "standardDowns.successRate", 1, "Early-down success"),
    ("explosive", "explosiveness", 1, "Big plays"),
    ("stuff", "stuffRate", -1, "Runs stuffed"),
    ("line_yards", "lineYards", 1, "Yards the line creates"),
]
KEYS = [k for k, *_ in FEATURES]
DIRECTION = {k: d for k, _, d, _ in FEATURES}
MIN_PRIOR = 3


def _get(obj: dict, path: str):
    for part in path.split("."):
        if not isinstance(obj, dict):
            return np.nan
        obj = obj.get(part)
    try:
        return float(obj)
    except (TypeError, ValueError):
        return np.nan


def team_games(adv: list[dict]) -> pd.DataFrame:
    rows = []
    for r in adv:
        row = {"game_id": r["gameId"], "season": r["season"], "order": order_key(r.get("seasonType", "regular"), r["week"]),
               "team": r["team"], "opponent": r["opponent"]}
        for k, path, _, _ in FEATURES:
            row[f"off_{k}"] = _get(r.get("offense") or {}, path)
            row[f"def_{k}"] = _get(r.get("defense") or {}, path)
        rows.append(row)
    cols = ["game_id", "season", "order", "team", "opponent"] + [f"{s}_{k}" for k in KEYS for s in ("off", "def")]
    return pd.DataFrame(rows, columns=cols)


def _stat_cols() -> list[str]:
    return [f"{s}_{k}" for k in KEYS for s in ("off", "def")]


def pregame(tg: pd.DataFrame, season: int, before_order: int) -> pd.DataFrame:
    """Season-to-date means per team from games before kickoff."""
    rows = tg[(tg["season"] == season) & (tg["order"] < before_order)]
    out = rows.groupby("team")[_stat_cols()].mean()
    out.insert(0, "games", rows.groupby("team").size())
    return out


def _priors(tg: pd.DataFrame) -> pd.DataFrame:
    """Per team-game: mean of that team's earlier games this season, and how many there were."""
    t = tg.sort_values(["season", "team", "order", "game_id"]).copy()
    g = t.groupby(["season", "team"])
    cols = _stat_cols()
    csum = g[cols].cumsum() - t[cols].fillna(0)
    cnt = g.cumcount()
    out = t[["game_id", "team"]].copy()
    out["prior_games"] = cnt
    for c in cols:
        out[c] = csum[c] / cnt.replace(0, np.nan)
    return out


def side_advantage(off: pd.Series | float, dfn: pd.Series | float, key: str):
    """Direction-adjusted matchup level: the offense's average plus what the defense allows (both
    measure the same stat from each side; a defense that allows a high number is a weak one)."""
    return DIRECTION[key] * (off + dfn)


def apply_orders(tg: pd.DataFrame, orders: dict[int, int]) -> pd.DataFrame:
    """Chronological order per game. CFBD labels every postseason game week 1, so postseason order
    must come from kickoff dates (plays.game_orders), or a bowl's own stats leak into its features."""
    out = tg.copy()
    out["order"] = [orders.get(int(g), o) for g, o in zip(out["game_id"], out["order"])]
    return out


def training_frame(tg: pd.DataFrame, games_by_id: dict[int, dict], fbs_by_season: dict[int, set[str]]) -> pd.DataFrame:
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
    cols = ["game_id", "season", "home_win", "home"] + [f"{p}_{k}" for k in KEYS for p in ("f", "ha", "aa")]
    if fbs_rows.empty:
        return pd.DataFrame(columns=cols)
    pri = _priors(fbs_rows).set_index(["game_id", "team"])
    rows = []
    for gid, g in games_by_id.items():
        h, a = g.get("homeTeam"), g.get("awayTeam")
        hp, ap = g.get("homePoints"), g.get("awayPoints")
        if hp is None or ap is None or hp == ap or (gid, h) not in pri.index or (gid, a) not in pri.index:
            continue
        H, A = pri.loc[(gid, h)], pri.loc[(gid, a)]
        if H["prior_games"] < MIN_PRIOR or A["prior_games"] < MIN_PRIOR:
            continue
        row = {"game_id": gid, "season": g["season"], "home_win": int(hp > ap), "home": 0 if g.get("neutralSite") else 1}
        for k in KEYS:
            ha = side_advantage(H[f"off_{k}"], A[f"def_{k}"], k)
            aa = side_advantage(A[f"off_{k}"], H[f"def_{k}"], k)
            row[f"f_{k}"], row[f"ha_{k}"], row[f"aa_{k}"] = ha - aa, ha, aa
        rows.append(row)
    return pd.DataFrame(rows, columns=cols).dropna()
