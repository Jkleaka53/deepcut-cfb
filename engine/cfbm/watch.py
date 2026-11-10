"""Who the Availability watch lists for a team, with each player's share of team production.

Facts from our own box scores only: "no stats last game" means the player has no box-score line in
the team's most recent game. It never claims an injury.
"""

from __future__ import annotations

import pandas as pd

SHARE_OF = {"receiving": "receiving yards", "rushing": "rushing yards"}


def _player(aid, name, role, share=None, share_of=None, absent=False) -> dict:
    return {"athleteId": int(aid), "name": str(name), "role": role, "share": share, "shareOf": share_of,
            "noStatsLastGame": bool(absent)}


def watch_list(passers: pd.DataFrame, skill: pd.DataFrame, team: str, season: int, before_order: int,
               starter: tuple[int, str] | None, positions: dict[int, str] | None = None) -> dict:
    """positions: CFBD roster position by athlete id. Unknown position: a passer counts as a QB unless
    he caught a pass this season (trick-play throwers are receivers or backs)."""
    positions = positions or {}
    p = passers[(passers["team"] == team) & (passers["season"] == season) & (passers["order"] < before_order)]
    k = skill[(skill["team"] == team) & (skill["season"] == season) & (skill["order"] < before_order)]
    orders = pd.concat([p[["game_id", "order"]], k[["game_id", "order"]]])
    last = orders.sort_values("order")["game_id"].iloc[-1] if not orders.empty else None
    played_last = set(p.loc[p["game_id"] == last, "athlete_id"]) | set(k.loc[k["game_id"] == last, "athlete_id"])

    def absent(aid) -> bool:
        return last is not None and int(aid) not in played_last

    players: list[dict] = []
    backup_id = None
    catchers = {int(a) for a in k.loc[(k["category"] == "receiving") & (k["count"] > 0), "athlete_id"]}

    def is_qb(aid) -> bool:
        pos = positions.get(int(aid))
        return pos == "QB" if pos else int(aid) not in catchers

    qbs = {int(a) for a in set(p["athlete_id"]) if is_qb(a)}
    if starter is not None:
        players.append(_player(starter[0], starter[1], "QB", absent=absent(starter[0])))
        others = p[(p["athlete_id"] != starter[0]) & p["athlete_id"].isin(qbs)]
        if not others.empty:
            att = others.groupby(["athlete_id", "name"])["attempts"].sum().reset_index()
            att = att.sort_values(["attempts", "name"], ascending=[False, True])
            b = att.iloc[0]
            backup_id = int(b["athlete_id"])
            players.append(_player(b["athlete_id"], b["name"], "QB2", absent=absent(b["athlete_id"])))
    listed = {x["athleteId"] for x in players}

    def leaders(cat: str, by: str, n: int, role: str):
        rows = k[(k["category"] == cat)]
        total = rows["yards"].sum()
        sums = rows.groupby(["athlete_id", "name"])[["count", "yards"]].sum().reset_index()
        sums = sums[~sums["athlete_id"].isin(qbs | listed)]
        if role == "RB":
            sums = sums[sums["athlete_id"].map(lambda a: positions.get(int(a)) in (None, "", "RB", "FB")).astype(bool)]
        sums = sums.sort_values([by, "name"], ascending=[False, True]).head(n)
        for _, r in sums.iterrows():
            share = round(float(r["yards"]) / float(total), 3) if total > 0 else None
            players.append(_player(r["athlete_id"], r["name"], role, share, SHARE_OF[cat], absent(r["athlete_id"])))
            listed.add(int(r["athlete_id"]))

    leaders("receiving", "yards", 3, "WR")
    leaders("rushing", "count", 1, "RB")
    return {"players": players, "backupId": backup_id}
