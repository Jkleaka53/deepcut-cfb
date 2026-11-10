"""Unit-vs-unit tables with a plain-words edge per row."""

from __future__ import annotations

import math

import pandas as pd

from cfbm import config

# (key, label, format, offense metric or None, defense metric)
TABLES = [
    ("Pass protection vs. pass rush", [
        ("sack_rate", "Sack rate", "pct", "off_sack_rate", "def_sack_rate"),
        ("pd_sack_rate", "Passing-down sack rate", "pct", "off_pd_sack_rate", "def_pd_sack_rate"),
        ("front7_havoc", "Front-seven havoc", "pct", None, "def_front7_havoc"),
    ]),
    ("Passing offense vs. pass defense", [
        ("epa_per_db", "EPA/dropback", "epa", "off_epa_per_db", "def_epa_per_db"),
        ("success_rate", "Success rate", "pct", "off_success_rate", "def_success_rate"),
        ("int_rate", "INT rate", "pct", "off_int_rate", "def_int_rate"),
        ("pd_epa", "Passing-down EPA", "epa", "off_pd_epa", "def_pd_epa"),
    ]),
]


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
        return {"value": None, "rank": None}, None
    value = _num(profile.loc[team, metric])
    rank = _num(ranked.loc[team, f"{metric}_rank"]) if team in ranked.index and f"{metric}_rank" in ranked else None
    pct = _num(ranked.loc[team, f"{metric}_pct"]) if team in ranked.index and f"{metric}_pct" in ranked else None
    return {"value": value, "rank": int(rank) if rank is not None and value is not None else None}, pct


def unit_tables(off_team: str, def_team: str, profile: pd.DataFrame, ranked: pd.DataFrame) -> list[dict]:
    out = []
    for title, rows in TABLES:
        built = []
        for key, label, fmt, off_metric, def_metric in rows:
            off_cell, off_pct = _cell(off_team, off_metric, profile, ranked)
            def_cell, def_pct = _cell(def_team, def_metric, profile, ranked)
            built.append({"key": key, "label": label, "format": fmt, "offense": off_cell, "defense": def_cell,
                          "edge": edge(off_pct, def_pct)})
        out.append({"title": title, "offenseTeam": off_team, "defenseTeam": def_team, "rows": built})
    return out
