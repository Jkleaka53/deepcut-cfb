"""Receiving and rushing box scores: one row per player per game."""

from __future__ import annotations

import pandas as pd

from cfbm.plays import order_key

SKILL_COLUMNS = ["game_id", "season", "order", "team", "athlete_id", "name", "category", "count", "yards"]
COUNT_TYPE = {"receiving": "REC", "rushing": "CAR"}


def _int(v) -> int:
    try:
        return int(float(str(v)))
    except (TypeError, ValueError):
        return 0


def skill_games(box: list[dict], season: int, season_type: str, week: int, category: str) -> pd.DataFrame:
    rows = []
    for game in box:
        for team in game.get("teams", []):
            for cat in team.get("categories", []):
                if cat.get("name") != category:
                    continue
                stats: dict[int, dict] = {}
                for t in cat.get("types", []):
                    key = {"YDS": "yards", COUNT_TYPE[category]: "count"}.get(t.get("name"))
                    if key is None:
                        continue
                    for a in t.get("athletes", []):
                        aid = str(a.get("id", ""))
                        if not aid.isdigit() or int(aid) <= 0:
                            continue
                        s = stats.setdefault(int(aid), {"name": a.get("name", ""), "count": 0, "yards": 0})
                        s[key] = _int(a.get("stat"))
                for aid, s in stats.items():
                    rows.append({"game_id": game["id"], "season": season, "order": order_key(season_type, week),
                                 "team": team["team"], "athlete_id": aid, "name": s["name"], "category": category,
                                 "count": s["count"], "yards": s["yards"]})
    return pd.DataFrame(rows, columns=SKILL_COLUMNS)
