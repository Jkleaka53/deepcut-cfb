"""A quarterback's game log against pass defenses, each opponent tagged with its pass-defense rank that season."""

from __future__ import annotations

import math

import pandas as pd

SKILL = "pass_defense"


def rank_lookup(frames: dict[int, pd.DataFrame]) -> tuple[dict[tuple[int, str], int], dict[int, int]]:
    """{(season, team): pass-defense rank} and {season: teams ranked}. Past seasons use full-season
    frames; the game's own season uses the frame as of kickoff, so past pages show what we'd have shown."""
    ranks: dict[tuple[int, str], int] = {}
    sizes: dict[int, int] = {}
    for season, df in frames.items():
        col = f"{SKILL}_rank"
        if col not in df:
            continue
        n = 0
        for team, v in df[col].items():
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            ranks[(season, team)] = int(v)
            n += 1
        sizes[season] = n
    return ranks, sizes


def _stage(g: dict, season_type: str) -> str | None:
    if season_type != "postseason":
        return None
    notes = (g.get("notes") or "").lower()
    return "CFP" if "playoff" in notes or "cfp" in notes else "Bowl"


def qb_log(rows: pd.DataFrame, games: dict[int, dict], ranks: dict[tuple[int, str], int]) -> list[dict]:
    """rows: the QB's team-game rows (one per game he was the primary passer)."""
    out = []
    for r in rows.itertuples(index=False):
        rank = ranks.get((int(r.season), r.opponent))
        if rank is None:
            continue
        g = games.get(int(r.game_id), {})
        home = g.get("homeTeam") == r.team
        pf, pa = (g.get("homePoints"), g.get("awayPoints")) if home else (g.get("awayPoints"), g.get("homePoints"))
        result = None if pf is None or pa is None else ("W" if pf > pa else "L" if pf < pa else "T")
        epa = None if not r.epa_n else round(float(r.epa_sum) / float(r.epa_n), 2)
        out.append({"gameId": int(r.game_id), "season": int(r.season), "opponent": r.opponent, "oppRank": rank,
                    "stage": _stage(g, r.season_type), "result": result,
                    "pf": None if pf is None else int(pf), "pa": None if pa is None else int(pa),
                    "epaPerDb": epa, "dropbacks": int(r.dropbacks)})
    out.sort(key=lambda x: (x["oppRank"], -x["season"], x["gameId"]))
    return out
