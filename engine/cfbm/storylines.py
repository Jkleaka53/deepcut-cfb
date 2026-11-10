"""Storylines to watch: real but small-sample situational facts, always with their sample size.
They never outrank the model's proven drivers."""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

NIGHT_HOUR = 19
BYE_DAYS = 13
SHORT_DAYS = 5
FAR_MILES = 1000
BIG_STADIUM = 80000
MIN_SAMPLE = 2


def _start(iso: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def _night(g: dict, venue: dict | None) -> bool | None:
    tz = (venue or {}).get("timezone")
    start = _start(g.get("startDate"))
    if g.get("startTimeTBD") or not tz or start is None:
        return None
    return start.astimezone(ZoneInfo(tz)).hour >= NIGHT_HOUR


def miles(a: dict | None, b: dict | None) -> float | None:
    try:
        la1, lo1, la2, lo2 = (math.radians(float(x)) for x in (a["latitude"], a["longitude"], b["latitude"], b["longitude"]))
    except (TypeError, KeyError, ValueError):
        return None
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def game_facts(game_ids, team: str, games_by_id: dict[int, dict], venues: dict[int, dict]) -> list[dict]:
    out = []
    for gid in game_ids:
        g = games_by_id.get(int(gid))
        if not g:
            continue
        home = g.get("homeTeam") == team
        pf, pa = (g.get("homePoints"), g.get("awayPoints")) if home else (g.get("awayPoints"), g.get("homePoints"))
        result = None if pf is None or pa is None else ("W" if pf > pa else "L" if pf < pa else "T")
        v = venues.get(int(g["venueId"])) if g.get("venueId") is not None else None
        site = "neutral" if g.get("neutralSite") else ("home" if home else "road")
        out.append({"gameId": int(gid), "site": site, "result": result, "night": _night(g, v),
                    "capacity": (v or {}).get("capacity")})
    return out


def _record(rows: list[dict]) -> tuple[str, int]:
    w = sum(r["result"] == "W" for r in rows)
    l = sum(r["result"] == "L" for r in rows)
    return f"{w}-{l}", w + l


def _qb_story(name: str, rows: list[dict], phrase: str) -> dict | None:
    rec, n = _record([r for r in rows if r["result"] in ("W", "L")])
    if n < MIN_SAMPLE:
        return None
    return {"text": f"{name} is {rec} {phrase} as a starter." if "stadiums" not in phrase else f"{name} is {rec} {phrase}.",
            "sample": f"{n} games", "kind": "storyline", "n": n}


def storylines(g: dict, qbs: dict, facts: dict[str, list[dict]], team_loc: dict[str, dict], venue: dict | None,
               prev_start: dict[str, str | None]) -> list[dict]:
    home, away = g["homeTeam"], g["awayTeam"]
    neutral = bool(g.get("neutralSite"))
    night = _night(g, venue)
    big = ((venue or {}).get("capacity") or 0) >= BIG_STADIUM
    kick = _start(g.get("startDate"))
    out: list[dict] = []
    for team in (away, home):
        qb = qbs.get(team)
        rows = facts.get(team, [])
        if qb:
            name = qb[1]
            if not neutral:
                site = "home" if team == home else "road"
                s = _qb_story(name, [r for r in rows if r["site"] == site], "at home" if site == "home" else "on the road")
                if s:
                    out.append(s)
            if night:
                s = _qb_story(name, [r for r in rows if r["night"]], "in night games")
                if s:
                    out.append(s)
            if big and (team != home or neutral):
                s = _qb_story(name, [r for r in rows if r["site"] != "home" and (r["capacity"] or 0) >= BIG_STADIUM],
                              "in road stadiums of 80,000 or more")
                if s:
                    out.append(s)
        prev = _start(prev_start.get(team))
        if prev and kick and g.get("seasonType") != "postseason":  # every bowl team has a long layoff
            days = int((kick - prev).total_seconds() // 86400)
            if days >= BYE_DAYS:
                out.append({"text": f"{team} is coming off a bye ({days} days of rest).", "sample": "schedule", "kind": "storyline", "n": 0})
            elif days <= SHORT_DAYS:
                out.append({"text": f"{team} is on a short week ({days} days of rest).", "sample": "schedule", "kind": "storyline", "n": 0})
        if team != home or neutral:
            d = miles(team_loc.get(team), venue)
            if d is not None and d >= FAR_MILES:
                out.append({"text": f"{team} travels about {round(d, -1):,.0f} miles for this one.", "sample": "schedule",
                            "kind": "storyline", "n": 0})
    out.sort(key=lambda s: -s["n"])
    return [{k: v for k, v in s.items() if k != "n"} for s in out]
