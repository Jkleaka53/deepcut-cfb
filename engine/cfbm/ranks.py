"""AP Top 25 rank for each game: the poll released before that game."""

from __future__ import annotations

AP = "AP Top 25"


def _ap(entry: dict) -> dict[str, int]:
    for p in entry.get("polls") or []:
        if p.get("poll") == AP:
            return {r["school"]: int(r["rank"]) for r in p.get("ranks") or [] if r.get("school")}
    return {}


def ap_poll_for(rankings: list[dict], season_type: str, week: int) -> dict[str, int]:
    """Regular week W: the regular AP poll with the largest week <= W (week 1 = preseason).
    Postseason: the latest regular-season AP poll (never the final poll released after the bowls)."""
    regular = [e for e in rankings if e.get("seasonType") == "regular" and _ap(e)]
    if season_type != "postseason":
        regular = [e for e in regular if e.get("week", 0) <= week]
    if not regular:
        return {}
    return _ap(max(regular, key=lambda e: e.get("week", 0)))
