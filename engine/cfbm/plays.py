"""Turn raw CFBD play-by-play into a normalized PlayFrame."""

from __future__ import annotations

import pandas as pd

from cfbm import config

COLUMNS = ["play_id", "game_id", "season", "week", "season_type", "offense", "defense", "period",
           "down", "distance", "play_type", "play_text", "ppa", "margin_pre", "is_dropback", "is_sack",
           "is_int", "is_pressure_est", "is_passing_down", "is_garbage"]

_DROPBACK = config.PLAY_TYPES["pass"] | config.PLAY_TYPES["sack"] | config.PLAY_TYPES["interception"]


def order_key(season_type: str, week: int) -> int:
    return 100 + int(week) if season_type == "postseason" else int(week)


def _pre_play_margins(raw: list[dict]) -> dict[str, int]:
    """CFBD scores are post-play. Pre-play margin = the previous play's score, offense-oriented."""
    by_game: dict = {}
    for p in raw:
        by_game.setdefault(p["gameId"], []).append(p)
    margins: dict[str, int] = {}
    for plays in by_game.values():
        plays.sort(key=lambda p: int(p["id"]))
        home_score = away_score = 0
        for p in plays:
            pre = home_score - away_score
            margins[str(p["id"])] = pre if p["offense"] == p["home"] else -pre
            off, dfn = p.get("offenseScore") or 0, p.get("defenseScore") or 0
            if p["offense"] == p["home"]:
                home_score, away_score = off, dfn
            else:
                home_score, away_score = dfn, off
    return margins


def _is_passing_down(down, distance) -> bool:
    if down is None or distance is None:
        return False
    return (down == 2 and distance >= 8) or (down in (3, 4) and distance >= 5)


def _is_garbage(period, margin) -> bool:
    limit = config.GARBAGE_MARGIN.get(period)
    return limit is not None and abs(margin) > limit


def normalize_plays(raw: list[dict], season: int, season_type: str, week: int) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=COLUMNS)
    margins = _pre_play_margins(raw)
    rows = []
    for p in raw:
        ptype = p.get("playType")
        margin = margins[str(p["id"])]
        rows.append({
            "play_id": int(p["id"]),
            "game_id": p["gameId"],
            "season": season,
            "week": week,
            "season_type": season_type,
            "offense": p["offense"],
            "defense": p["defense"],
            "period": p.get("period"),
            "down": p.get("down"),
            "distance": p.get("distance"),
            "play_type": ptype,
            "play_text": p.get("playText") or "",
            "ppa": p.get("ppa"),
            "margin_pre": margin,
            "is_dropback": ptype in _DROPBACK,
            "is_sack": ptype in config.PLAY_TYPES["sack"],
            "is_int": ptype in config.PLAY_TYPES["interception"],
            # Pressure is not identifiable in free data (see docs/spike-notes.md).
            "is_pressure_est": False,
            "is_passing_down": _is_passing_down(p.get("down"), p.get("distance")),
            "is_garbage": _is_garbage(p.get("period"), margin),
        })
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["ppa"] = pd.to_numeric(df["ppa"], errors="coerce")
    return df
