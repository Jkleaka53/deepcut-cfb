"""Incremental CFBD pulls. Completed weeks are cached forever; anything still in progress refetches."""

from __future__ import annotations


def week_complete(games_list: list[dict], season_type: str, week: int) -> bool:
    wk = [g for g in games_list if g.get("seasonType") == season_type and g.get("week") == week]
    return bool(wk) and all(g.get("completed") for g in wk)


def fbs_teams(client, season: int) -> set[str]:
    return {t["school"] for t in client.get("/teams/fbs", {"year": season})}


def games(client, season: int, live: bool) -> list[dict]:
    out: list[dict] = []
    for st in ("regular", "postseason"):
        out += client.get("/games", {"year": season, "seasonType": st}, cacheable=not live)
    return out


def plays(client, season: int, season_type: str, week: int, games_list: list[dict]) -> list[dict]:
    return client.get("/plays", {"year": season, "week": week, "seasonType": season_type},
                      cacheable=week_complete(games_list, season_type, week))


def player_box(client, season: int, season_type: str, week: int, games_list: list[dict]) -> list[dict]:
    return client.get("/games/players",
                      {"year": season, "week": week, "seasonType": season_type, "category": "passing"},
                      cacheable=week_complete(games_list, season_type, week))


def advanced_season(client, season: int, live: bool) -> list[dict]:
    return client.get("/stats/season/advanced", {"year": season}, cacheable=not live)


def front7_havoc(raw: list[dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in raw:
        havoc = (row.get("defense") or {}).get("havoc") or {}
        if havoc.get("frontSeven") is not None:
            out[row["team"]] = float(havoc["frontSeven"])
    return out
