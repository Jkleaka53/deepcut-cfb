"""Team-level inputs known before a season starts: 247Sports' roster talent composite and returning production
(the share of last season's PPA that is back). Added to the edge model and the Upset Watch model on 2026-11-11
after the backtest (edge model 72.3% -> 72.7% winners, weeks 1-4 73.6% -> 75.7%; Upset Watch weekly pick
cover 52.7% -> 54.0%, outright 38.1% vs book 28.2%). Internal only: these numbers are never published.
Two CFBD calls per season; the live season is fetched fresh every build."""

from __future__ import annotations

import pandas as pd

PRIOR_KEYS: list[str] = ["talent", "ret"]


def load(client, seasons, live_season: int | None = None) -> dict[int, dict[str, dict[str, float]]]:
    """{season: {"talent": {team: v}, "ret": {team: v}}}."""
    out = {}
    for s in seasons:
        live = s == live_season
        talent = {r["team"]: float(r["talent"]) for r in client.get("/talent", {"year": s}, cacheable=not live) or []
                  if r.get("team") and r.get("talent") is not None}
        ret = {r["team"]: float(r["percentPPA"]) for r in client.get("/player/returning", {"year": s}, cacheable=not live) or []
               if r.get("team") and r.get("percentPPA") is not None}
        out[s] = {"talent": talent, "ret": ret}
    return out


def diffs(season_priors: dict | None, home: str, away: str) -> dict[str, float]:
    """Home minus away for each prior. 0.0 when either team has no number (the league-average rule the edge
    model uses for a team that has not played)."""
    out = {}
    for k in PRIOR_KEYS:
        vals = (season_priors or {}).get(k, {})
        out[k] = vals[home] - vals[away] if home in vals and away in vals else 0.0
    return out


def add_to_frame(frame: pd.DataFrame, games_by_id: dict[int, dict], priors: dict[int, dict]) -> pd.DataFrame:
    """A training frame (game_id, season) with an f_<key> column per prior."""
    d = [diffs(priors.get(s), games_by_id[gid]["homeTeam"], games_by_id[gid]["awayTeam"])
         for gid, s in zip(frame["game_id"], frame["season"])]
    return frame.assign(**{f"f_{k}": [x[k] for x in d] for k in PRIOR_KEYS})
