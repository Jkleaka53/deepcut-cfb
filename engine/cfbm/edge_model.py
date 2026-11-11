"""The edge score's model: the nine pregame matchup stats plus prior team strength (pregame Elo) and
scoring margin to date. Every FBS-vs-FBS game is scored, week 1 included: a team's season-to-date numbers
are measured from the league average and a team that has not played sits at the average, so early games
lean on Elo and home field. (shrunk_pregame can also pull thin samples toward the average, but the held-out
check picked no shrinking: config.EDGE_SHRINK_K = 0.)
Internal only: nothing here is published (the swing-factor card keeps its own nine-stat fit)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm import config
from cfbm.swing_data import DIRECTION, KEYS, stat_cols

EDGE_KEYS: list[str] = KEYS + ["elo", "margin"]


def team_margins(games: list[dict], fbs_by_season: dict[int, set[str]], orders: dict[int, int],
                 cap: float = config.EDGE_MARGIN_CAP) -> pd.DataFrame:
    """Two rows per played FBS-vs-FBS game: each team's points margin, capped so blowouts count once."""
    rows = []
    for g in games:
        s, h, a = g.get("season"), g.get("homeTeam"), g.get("awayTeam")
        hp, ap = g.get("homePoints"), g.get("awayPoints")
        fbs = fbs_by_season.get(s, set())
        if hp is None or ap is None or h not in fbs or a not in fbs or g["id"] not in orders \
                or g.get("completed") is False:  # a game in progress has points but no result yet
            continue
        m = float(np.clip(hp - ap, -cap, cap))
        rows.append({"game_id": g["id"], "season": s, "team": h, "order": orders[g["id"]], "margin": m})
        rows.append({"game_id": g["id"], "season": s, "team": a, "order": orders[g["id"]], "margin": -m})
    return pd.DataFrame(rows, columns=["game_id", "season", "team", "order", "margin"])


def margin_before(tm: pd.DataFrame, season: int, before_order: int) -> pd.DataFrame:
    """Per team: games played and mean capped margin, from games before kickoff."""
    rows = tm[(tm["season"] == season) & (tm["order"] < before_order)]
    g = rows.groupby("team")["margin"]
    out = pd.DataFrame({"games": g.size(), "margin": g.mean()})
    out.index.name = "team"
    return out


def shrunk_pregame(pre: pd.DataFrame, margin: pd.DataFrame, k: float) -> pd.DataFrame:
    """Each team's pregame numbers as a distance from the league average, scaled by n / (n + k) where n is
    the team's games so far. pre: swing_data.pregame_adjusted output; margin: margin_before output.
    A missing number counts as league average (0.0)."""
    cols = stat_cols()
    out = pd.DataFrame(0.0, index=pre.index.union(margin.index), columns=cols + ["margin"])
    for src, names in ((pre, cols), (margin, ["margin"])):
        if src.empty:
            continue
        n = src["games"].astype(float)
        weight = n / (n + k) if k > 0 else (n > 0).astype(float)
        for c in names:
            v = src[c].astype(float)
            out.loc[src.index, c] = ((v - v.mean()) * weight).fillna(0.0)
    out.index.name = "team"
    return out


def features(sp: pd.DataFrame, home: str, away: str, elo_home: float | None,
             elo_away: float | None) -> dict[str, float] | None:
    """Home-minus-away inputs for one game, keyed by EDGE_KEYS. None without both Elo ratings.
    A team that has not played sits at league average on everything but Elo."""
    if elo_home is None or elo_away is None or pd.isna(elo_home) or pd.isna(elo_away):
        return None

    def val(team: str, col: str) -> float:
        return float(sp.at[team, col]) if team in sp.index else 0.0

    out = {}
    for k in KEYS:
        out[k] = DIRECTION[k] * ((val(home, f"off_{k}") + val(away, f"def_{k}"))
                                 - (val(away, f"off_{k}") + val(home, f"def_{k}")))
    out["elo"] = float(elo_home) - float(elo_away)
    out["margin"] = val(home, "margin") - val(away, "margin")
    return out


def pregame_tables(tg: pd.DataFrame, games_by_id: dict[int, dict], fbs_by_season: dict[int, set[str]]) -> dict:
    """{(season, order): (adjusted pregame stats, margin so far)} for every kickoff slot with a game, plus
    {"orders": {game_id: order}}. The same two calls the live build makes, so training cannot drift from it.
    Shrinking is left out so several shrink strengths can share one (slow) pass."""
    from cfbm.plays import game_orders
    from cfbm.swing_data import apply_orders, pregame_adjusted

    by_season: dict[int, list[dict]] = {}
    for g in games_by_id.values():
        by_season.setdefault(g.get("season"), []).append(g)
    orders: dict[int, int] = {}
    for gs in by_season.values():
        orders.update(game_orders(gs))
    tg = apply_orders(tg, orders)
    mask = pd.Series([t in fbs_by_season.get(s, set()) and o in fbs_by_season.get(s, set())
                      for s, t, o in zip(tg["season"], tg["team"], tg["opponent"])], index=tg.index, dtype=bool)
    tg = tg[mask]
    tm = team_margins(list(games_by_id.values()), fbs_by_season, orders)
    out: dict = {"orders": orders}
    for s, gs in by_season.items():
        fbs = fbs_by_season.get(s, set())
        tgs = tg[tg["season"] == s]
        for o in sorted({orders[g["id"]] for g in gs if g.get("homeTeam") in fbs and g.get("awayTeam") in fbs}):
            out[(s, o)] = (pregame_adjusted(tgs, s, o, w=config.OPP_ADJUST), margin_before(tm, s, o))
    return out


def frame(tg: pd.DataFrame, games_by_id: dict[int, dict], fbs_by_season: dict[int, set[str]],
          k: float = config.EDGE_SHRINK_K, tables: dict | None = None) -> pd.DataFrame:
    """One row per decided FBS-vs-FBS game with both Elo ratings: the result, home field, the EDGE_KEYS
    inputs as of kickoff, and scored_before (both teams had MIN_PRIOR games: the set the nine-stat model scores)."""
    from cfbm.swing_data import MIN_PRIOR

    tables = tables or pregame_tables(tg, games_by_id, fbs_by_season)
    orders = tables["orders"]
    cols = ["game_id", "season", "home_win", "home", "scored_before"] + [f"f_{key}" for key in EDGE_KEYS]
    shrunk: dict = {}
    rows = []
    for gid, g in games_by_id.items():
        s, h, a = g.get("season"), g.get("homeTeam"), g.get("awayTeam")
        hp, ap = g.get("homePoints"), g.get("awayPoints")
        fbs = fbs_by_season.get(s, set())
        slot = (s, orders.get(gid))
        if h not in fbs or a not in fbs or hp is None or ap is None or hp == ap or slot not in tables:
            continue
        pre, mb = tables[slot]
        if slot not in shrunk:
            shrunk[slot] = shrunk_pregame(pre, mb, k)
        feats = features(shrunk[slot], h, a, g.get("homePregameElo"), g.get("awayPregameElo"))
        if feats is None:
            continue
        games = pre["games"].reindex([h, a]).fillna(0)
        rows.append({"game_id": gid, "season": s, "home_win": int(hp > ap), "home": 0 if g.get("neutralSite") else 1,
                     "scored_before": bool((games >= MIN_PRIOR).all()), **{f"f_{key}": v for key, v in feats.items()}})
    return pd.DataFrame(rows, columns=cols)


def train(frame: pd.DataFrame, keys: list[str] = EDGE_KEYS) -> dict:
    """Logistic fit on standardized inputs. Returns what edge_score needs: weights, and how lopsided training
    games were (quantiles of the absolute linear score), so a game's edge can be scored 0-10 by percentile."""
    from cfbm.swing_model import _quantiles, fit_logit

    means = {key: float(frame[f"f_{key}"].mean()) for key in keys}
    sds = {key: float(frame[f"f_{key}"].std()) or 1.0 for key in keys}
    X = np.column_stack([np.ones(len(frame)), frame["home"].to_numpy(float)] +
                        [((frame[f"f_{key}"] - means[key]) / sds[key]).to_numpy(float) for key in keys])
    beta = fit_logit(X, frame["home_win"].to_numpy(float))
    feats = {key: {"coef": round(float(beta[i]), 4), "mean": round(means[key], 6), "sd": round(sds[key], 6)}
             for i, key in enumerate(keys, start=2)}
    # Built from the stored (rounded) values so runtime scoring matches exactly.
    intercept, home = round(float(beta[0]), 4), round(float(beta[1]), 4)
    lin = intercept + home * frame["home"].to_numpy(float)
    for key in keys:
        f = feats[key]
        lin = lin + f["coef"] * (frame[f"f_{key}"].to_numpy(float) - f["mean"]) / f["sd"]
    return {"seasons": sorted(int(s) for s in frame["season"].unique()), "games": int(len(frame)),
            "intercept": intercept, "home": {"coef": home}, "features": feats, "scale": {"overall": _quantiles(lin)}}
