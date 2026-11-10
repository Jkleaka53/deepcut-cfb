"""Unit-vs-unit tables with a plain-words edge per row."""

from __future__ import annotations

import math

import pandas as pd

from cfbm import config
from cfbm.tiers import METRIC_DIRECTION

# (key, label, format, offense metric or None, defense metric)
TABLES = [
    ("Pass protection vs. pass rush", [
        ("sack_rate", "Sacks", "pct", "off_sack_rate", "def_sack_rate"),
        ("pd_sack_rate", "Sacks on 3rd-and-long", "pct", "off_pd_sack_rate", "def_pd_sack_rate"),
        ("front7_havoc", "Front-seven disruption", "pct", None, "def_front7_havoc"),
    ]),
    ("Passing offense vs. pass defense", [
        ("epa_per_db", "Points added per pass", "epa", "off_epa_per_db", "def_epa_per_db"),
        ("success_rate", "Successful passes", "pct", "off_success_rate", "def_success_rate"),
        ("int_rate", "Interceptions", "pct", "off_int_rate", "def_int_rate"),
        ("pd_epa", "Passing on 3rd-and-long", "epa", "off_pd_epa", "def_pd_epa"),
    ]),
]

RUN_TABLES = [
    ("Run blocking vs. run defense front", [
        ("line_yards", "Yards the line creates", "yds", "off_line_yards", "def_line_yards"),
        ("stuff_rate", "Runs stuffed", "pct", "off_stuff_rate", "def_stuff_rate"),
        ("power_success", "Short-yardage runs converted", "pct", "off_power_success", "def_power_success"),
    ]),
    ("Running game vs. run defense", [
        ("rush_epa", "Points added per run", "epa", "off_rush_epa", "def_rush_epa"),
        ("second_level", "Yards past the line (5 to 10)", "yds", "off_second_level", "def_second_level"),
        ("open_field", "Breakaway yards (past 10)", "yds", "off_open_field", "def_open_field"),
    ]),
]

EXPLAIN = {
    "line_yards": "Run yards credited to the blocking up front, per carry",
    "stuff_rate": "Runs stopped at or behind the line",
    "power_success": "3rd or 4th and 2 or less, or at the goal line: how often the run gets it",
    "rush_epa": "How much each run helps the offense score",
    "second_level": "Yards a back gains 5 to 10 yards downfield, per carry",
    "open_field": "Yards past 10 on a run, per carry: the big runs",
    "int_rate": "How often a pass gets picked off",
    "epa_per_db": "How much each pass play helps the offense score",
    "success_rate": "Passes that keep the offense on schedule",
    "sack_rate": "How often the QB goes down",
    "pd_sack_rate": "Sacks when everyone knows a pass is coming",
    "pd_epa": "How well the offense passes in those spots",
    "front7_havoc": "Tackles for loss, sacks and batted passes by the front seven",
}


def hint(off_metric: str | None, def_metric: str | None) -> str | None:
    word = {1: "higher", -1: "lower"}
    o = METRIC_DIRECTION.get(off_metric) if off_metric else None
    d = METRIC_DIRECTION.get(def_metric) if def_metric else None
    if o == -1 and d == -1:
        return "Lower is better for both"
    if o is None or d is None:
        return "Defense: lower is better" if d == -1 else None
    if o == 1 and d == 1:
        return None
    return f"Offense: {word[o]} is better · Defense: {word[d]} is better"


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def edge(off_pct: float | None, def_pct: float | None) -> str | None:
    a, b = _num(off_pct), _num(def_pct)
    if a is None or b is None:
        return None
    gap = a - b
    if abs(gap) < config.EDGE_SLIGHT:
        return "even"
    side = "offense" if gap > 0 else "defense"
    return f"{'slight' if abs(gap) < config.EDGE_CLEAR else 'clear'}-{side}"


def _cell(team: str, metric: str | None, profile: pd.DataFrame, ranked: pd.DataFrame):
    if metric is None or team not in profile.index or metric not in profile:
        return {"value": None, "rank": None, "pct": None}, None
    value = _num(profile.loc[team, metric])
    rank = _num(ranked.loc[team, f"{metric}_rank"]) if team in ranked.index and f"{metric}_rank" in ranked else None
    pct = _num(ranked.loc[team, f"{metric}_pct"]) if team in ranked.index and f"{metric}_pct" in ranked else None
    pct = pct if value is not None else None
    return {"value": value, "rank": int(rank) if rank is not None and value is not None else None,
            "pct": None if pct is None else round(pct, 1)}, pct


def unit_tables(off_team: str, def_team: str, profile: pd.DataFrame, ranked: pd.DataFrame,
                tables: list = TABLES) -> list[dict]:
    out = []
    for title, rows in tables:
        built = []
        for key, label, fmt, off_metric, def_metric in rows:
            off_cell, off_pct = _cell(off_team, off_metric, profile, ranked)
            def_cell, def_pct = _cell(def_team, def_metric, profile, ranked)
            built.append({"key": key, "label": label, "explain": EXPLAIN[key], "hint": hint(off_metric, def_metric),
                          "format": fmt, "offense": off_cell, "defense": def_cell, "edge": edge(off_pct, def_pct)})
        out.append({"title": title, "offenseTeam": off_team, "defenseTeam": def_team, "rows": built})
    return out


def _gaps(rows: list[dict]) -> list[tuple[float, dict]]:
    out = []
    for r in rows:
        a, b = _num(r["offense"].get("pct")), _num(r["defense"].get("pct"))
        if a is not None and b is not None:
            out.append((a - b, r))
    return out


def side_edge(rows: list[dict]) -> str | None:
    g = _gaps(rows)
    if not g:
        return None
    mean = sum(x for x, _ in g) / len(g)
    return edge(50 + mean / 2, 50 - mean / 2)


def biggest_gap(rows: list[dict]) -> str | None:
    g = _gaps(rows)
    if not g:
        return None
    best = g[0]
    for item in g[1:]:
        if abs(item[0]) > abs(best[0]):
            best = item
    return best[1]["key"]
