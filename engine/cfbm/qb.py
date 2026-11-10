"""Primary passer per team-game, and career game logs keyed on CFBD athlete id."""

from __future__ import annotations

import pandas as pd

from cfbm import config
from cfbm.plays import order_key

COLUMNS = ["game_id", "season", "season_type", "week", "order", "team", "athlete_id", "name",
           "attempts", "team_attempts", "share", "is_primary"]


def _attempts(stat: str) -> int | None:
    try:
        return int(str(stat).split("/")[1])
    except (IndexError, ValueError):
        return None


def passer_games(box: list[dict], season: int, season_type: str, week: int) -> pd.DataFrame:
    rows = []
    for game in box:
        for team in game.get("teams", []):
            passers = []
            for cat in team.get("categories", []):
                if cat.get("name") != "passing":
                    continue
                for t in cat.get("types", []):
                    if t.get("name") != "C/ATT":
                        continue
                    for a in t.get("athletes", []):
                        att = _attempts(a.get("stat"))
                        if att is None or not str(a.get("id", "")).lstrip("-").isdigit() or int(a["id"]) <= 0:
                            continue
                        passers.append((int(a["id"]), a.get("name", ""), att))
            total = sum(p[2] for p in passers)
            for aid, name, att in passers:
                share = att / total if total else 0.0
                rows.append({"game_id": game["id"], "season": season, "season_type": season_type,
                             "week": week, "order": order_key(season_type, week), "team": team["team"],
                             "athlete_id": aid, "name": name, "attempts": att, "team_attempts": total,
                             "share": share, "is_primary": total > 0 and share >= config.PRIMARY_QB_SHARE})
    return pd.DataFrame(rows, columns=COLUMNS)


def career(passers: pd.DataFrame, athlete_id: int) -> pd.DataFrame:
    return passers[(passers["athlete_id"] == athlete_id) & passers["is_primary"]].copy()


def current_starter(passers: pd.DataFrame, team: str, season: int, before_order: int) -> tuple[int, str] | None:
    prior = passers[(passers["team"] == team) & (passers["season"] == season) & (passers["order"] < before_order)]
    if prior.empty:
        return None
    last_order = prior["order"].max()
    last_primary = prior[(prior["order"] == last_order) & prior["is_primary"]]
    if not last_primary.empty:
        r = last_primary.iloc[0]
        return int(r["athlete_id"]), str(r["name"])
    totals = prior.groupby(["athlete_id", "name"])["attempts"].sum().sort_values(ascending=False)
    aid, name = totals.index[0]
    return int(aid), str(name)
