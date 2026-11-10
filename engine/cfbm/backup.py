"""The backup QB's own numbers from the games he started, ranked against this season's FBS offenses.

Used by the Availability watch: when the starter is set Out, the page swaps these in for the team's
offense numbers. Nothing here is a projection; it is what happened in his starts.
"""

from __future__ import annotations

import pandas as pd

from cfbm.qblog import qb_log
from cfbm.team_stats import _side
from cfbm.tiers import METRIC_DIRECTION
from cfbm.units import TABLES, _num

SMALL_SAMPLE = 3
_EMPTY = {"value": None, "rank": None, "pct": None}


def rank_against(value: float | None, field: pd.Series, direction: int) -> tuple[int | None, float | None]:
    """Where value would rank in field (1 = best), matching assign_tiers' method="min" and pct formula."""
    if value is None:
        return None, None
    vals = field.dropna() * direction
    n = len(vals)
    if n == 0:
        return None, None
    rank = min(n, 1 + int((vals > value * direction).sum()))
    pct = (n - rank) / (n - 1) * 100 if n > 1 else 50.0
    return rank, round(min(100.0, max(0.0, pct)), 1)


def backup_block(rows: pd.DataFrame, name: str, athlete_id: int, profile: pd.DataFrame, ranked_index,
                 games_by_id: dict[int, dict], ranks: dict[tuple[int, str], int]) -> dict:
    """rows: the backup's career team-game rows before kickoff (games he was the primary passer)."""
    games = int(rows["game_id"].nunique()) if not rows.empty else 0
    agg = _side(rows.assign(team="__backup__"), "team", "off") if games else None
    field = profile[profile.index.isin(ranked_index)]
    cells = {}
    for _, table_rows in TABLES:
        for key, _label, _fmt, off_metric, _def in table_rows:
            if off_metric is None:
                continue
            if agg is None or off_metric not in agg or off_metric not in field:
                cells[key] = dict(_EMPTY)
                continue
            value = _num(agg.loc["__backup__", off_metric])
            rank, pct = rank_against(value, field[off_metric], METRIC_DIRECTION[off_metric])
            cells[key] = {"value": value, "rank": rank, "pct": pct}
    return {"athleteId": int(athlete_id), "name": name, "games": games, "smallSample": games < SMALL_SAMPLE,
            "cells": cells,
            "qbVs": {"name": name, "opponent": None, "oppRank": None, "of": None,
                     "games": qb_log(rows, games_by_id, ranks) if games else []}}
