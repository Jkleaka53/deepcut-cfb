"""What our own box scores say about each team's quarterback. Describes what happened; never claims why."""

from __future__ import annotations

import pandas as pd

from cfbm import config


def qb_flags(passers: pd.DataFrame, team: str, season: int, before_order: int) -> list[dict]:
    p = passers[(passers["team"] == team) & (passers["season"] == season) & (passers["order"] < before_order)]
    prim = p[p["is_primary"]]
    if prim.empty:
        return []
    game_order = p.groupby("game_id")["order"].max().sort_values()
    last_gid = game_order.index[-1]
    starters = prim.drop_duplicates("game_id").set_index("game_id")
    flags: list[dict] = []
    if last_gid in starters.index:
        now_name = str(starters.loc[last_gid, "name"])
        earlier = [g for g in game_order.index[:-1] if g in starters.index]
        prev = starters.loc[earlier[-1]] if earlier else None
        if prev is not None and int(prev["athlete_id"]) != int(starters.loc[last_gid, "athlete_id"]):
            flags.append({"kind": "warn",
                          "text": f"QB change: {now_name} started last game after {prev['name']} the game before."})
        else:
            flags.append({"kind": "ok", "text": f"{now_name} started last game."})
    counts = prim.groupby(["athlete_id", "name"]).size().sort_values(ascending=False)
    leader_id, leader_name = counts.index[0]
    if not ((p["game_id"] == last_gid) & (p["athlete_id"] == leader_id)).any():
        flags.append({"kind": "warn", "text": f"{leader_name} did not play last game."})
    return flags


def report_for(conference: str | None) -> dict:
    r = config.AVAILABILITY_REPORTS.get(conference or "")
    return {"conference": conference, "url": r["url"] if r else None, "when": r["when"] if r else None,
            "publishes": r is not None}
