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


def team_games(adv: list[dict], features: list[tuple] = FEATURES) -> pd.DataFrame:
    rows = []
    for r in adv:
        row = {"game_id": r["gameId"], "season": r["season"], "order": order_key(r.get("seasonType", "regular"), r["week"]),
               "team": r["team"], "opponent": r["opponent"]}
        for k, path, _, _ in features:
            row[f"off_{k}"] = _get(r.get("offense") or {}, path)
            row[f"def_{k}"] = _get(r.get("defense") or {}, path)
        rows.append(row)
    return pd.DataFrame(rows, columns=["game_id", "season", "order", "team", "opponent"] + stat_cols(features))


def stat_cols(features: list[tuple] = FEATURES) -> list[str]:
    return [f"{s}_{k}" for k, *_ in features for s in ("off", "def")]


_stat_cols = stat_cols


def pregame(tg: pd.DataFrame, season: int, before_order: int, cols: list[str] | None = None) -> pd.DataFrame:
    """Season-to-date means per team from games before kickoff."""
    rows = tg[(tg["season"] == season) & (tg["order"] < before_order)]
    out = rows.groupby("team")[cols or stat_cols()].mean()
    out.insert(0, "games", rows.groupby("team").size())
    return out


def _priors(tg: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """Per team-game: mean of that team's earlier games this season, and how many there were."""
    t = tg.sort_values(["season", "team", "order", "game_id"]).copy()
    g = t.groupby(["season", "team"])
    cols = cols or stat_cols()
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
    from cfbm import config

    pri = adjusted_priors(fbs_rows, w=config.OPP_ADJUST).set_index(["game_id", "team"])
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


# --- Opponent adjustment (owner 2026-11-10) --------------------------------------------------------------
# A team's season-to-date stat, corrected for who it played, using only games before kickoff:
#   offense: mean over its earlier games of  off_k - w x (that opponent's defense average so far - league so far)
#   defense: mean over its earlier games of  def_k - w x (that opponent's offense average so far - league so far)
# "So far" = before the game being previewed. w = config.OPP_ADJUST, chosen by held-out log loss.


class _SeasonIndex:
    def __init__(self, s: pd.DataFrame, cols: list[str]):
        import bisect  # noqa: F401  (used by the methods below)

        s = s.sort_values(["order", "game_id"])
        self.cols = cols
        self.teams: dict[str, tuple] = {}
        for t, g in s.groupby("team", sort=False):
            orders = g["order"].to_numpy()
            vals = {c: g[c].to_numpy(float) for c in cols}
            cs = {c: np.concatenate([[0.0], np.nancumsum(v)]) for c, v in vals.items()}
            cn = {c: np.concatenate([[0], np.cumsum(~np.isnan(v))]) for c, v in vals.items()}
            self.teams[t] = (orders, cs, cn, g["opponent"].to_list(), vals)
        self.lo = s["order"].to_numpy()
        lv = {c: s[c].to_numpy(float) for c in cols}
        self.lcs = {c: np.concatenate([[0.0], np.nancumsum(v)]) for c, v in lv.items()}
        self.lcn = {c: np.concatenate([[0], np.cumsum(~np.isnan(v))]) for c, v in lv.items()}

    def _mean_before(self, t: str, c: str, d) -> float:
        import bisect

        orders, cs, cn, _, _ = self.teams[t]
        i = bisect.bisect_left(orders, d)
        return cs[c][i] / cn[c][i] if cn[c][i] else np.nan

    def _league_before(self, c: str, d) -> float:
        import bisect

        i = bisect.bisect_left(self.lo, d)
        return self.lcs[c][i] / self.lcn[c][i] if self.lcn[c][i] else np.nan

    def team(self, t: str, d, w: float) -> tuple[int, dict[str, float]]:
        """(games before d, adjusted means before d) for one team."""
        import bisect

        orders, _, _, opps, vals = self.teams[t]
        n = bisect.bisect_left(orders, d)
        out = {}
        for c in self.cols:
            side, k = c.split("_", 1)
            other = f"{'def' if side == 'off' else 'off'}_{k}"
            league = self._league_before(other, d)
            xs = []
            for i in range(n):
                v = vals[c][i]
                if np.isnan(v):
                    continue
                if w == 0:
                    xs.append(v)
                    continue
                opp = opps[i]
                if opp not in self.teams:
                    continue
                o = self._mean_before(opp, other, d)
                if np.isnan(o) or np.isnan(league):
                    continue
                xs.append(v - w * (o - league))
            out[c] = float(np.mean(xs)) if xs else np.nan
        return n, out


def adjusted_priors(tg: pd.DataFrame, cols: list[str] | None = None, w: float = 0.8) -> pd.DataFrame:
    """Opponent-adjusted version of _priors: per team-game, adjusted means of that team's earlier games."""
    cols = cols or stat_cols()
    out = []
    for _, s in tg.groupby("season"):
        idx = _SeasonIndex(s, cols)
        for gid, t, d in zip(s["game_id"], s["team"], s["order"]):
            n, means = idx.team(t, d, w)
            out.append({"game_id": gid, "team": t, "prior_games": n, **means})
    return pd.DataFrame(out, columns=["game_id", "team", "prior_games", *cols])


def pregame_adjusted(tg: pd.DataFrame, season: int, before_order: int, cols: list[str] | None = None,
                     w: float = 0.8) -> pd.DataFrame:
    """Opponent-adjusted version of pregame(): per team, adjusted means of games before kickoff."""
    cols = cols or stat_cols()
    s = tg[(tg["season"] == season) & (tg["order"] < before_order)]
    rows = {}
    if not s.empty:
        idx = _SeasonIndex(s, cols)
        for t in idx.teams:
            n, means = idx.team(t, before_order, w)
            rows[t] = {"games": n, **means}
    out = pd.DataFrame.from_dict(rows, orient="index", columns=["games", *cols])
    out.index.name = "team"
    return out
