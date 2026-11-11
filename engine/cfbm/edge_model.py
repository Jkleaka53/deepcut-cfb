"""The edge score's model: the nine pregame matchup stats plus prior team strength (pregame Elo) and
scoring margin to date. Every FBS-vs-FBS game is scored, week 1 included: a team's season-to-date numbers
are pulled toward the league average while its sample is thin, so early games lean on Elo and home field.
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
        if hp is None or ap is None or h not in fbs or a not in fbs or g["id"] not in orders:
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
