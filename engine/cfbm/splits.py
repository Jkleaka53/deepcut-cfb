"""Opponent-tier split tables (the SplitTable shape of the JSON contract)."""

from __future__ import annotations

import math
from typing import Literal

import pandas as pd

from cfbm import config
from cfbm.tiers import SKILLS

TierLookup = dict[tuple[int, str], dict[str, int]]

OFFENSE_METRICS = {
    "epa_per_db": ("EPA/dropback", "epa"),
    "success_rate": ("Success %", "pct"),
    "sack_rate": ("Sack %", "pct"),
    "int_rate": ("INT %", "pct"),
    "pd_epa_per_db": ("Passing-down EPA", "epa"),
}
DEFENSE_METRICS = {
    "epa_allowed_per_db": ("EPA allowed/dropback", "epa"),
    "sack_rate": ("Sack %", "pct"),
    "int_rate": ("INT %", "pct"),
    "pd_sack_rate": ("Passing-down sack %", "pct"),
}


def tier_lookup(tiers_by_season: dict[int, pd.DataFrame]) -> TierLookup:
    out: TierLookup = {}
    for season, df in tiers_by_season.items():
        for team, row in df.iterrows():
            entry = {}
            for skill in SKILLS:
                v = row.get(f"{skill}_tier")
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    entry[skill] = int(v)
            out[(season, team)] = entry
    return out


def _ratio(a: float, b: float) -> float | None:
    return float(a) / float(b) if b else None


def _metrics(g: pd.DataFrame, side: str) -> dict[str, float | None]:
    s = g[["dropbacks", "epa_sum", "epa_n", "success", "sacks", "ints", "pd_epa_sum", "pd_epa_n",
           "pd_dropbacks", "pd_sacks"]].sum()
    if side == "offense":
        return {"epa_per_db": _ratio(s.epa_sum, s.epa_n), "success_rate": _ratio(s.success, s.epa_n),
                "sack_rate": _ratio(s.sacks, s.dropbacks), "int_rate": _ratio(s.ints, s.dropbacks),
                "pd_epa_per_db": _ratio(s.pd_epa_sum, s.pd_epa_n)}
    return {"epa_allowed_per_db": _ratio(s.epa_sum, s.epa_n), "sack_rate": _ratio(s.sacks, s.dropbacks),
            "int_rate": _ratio(s.ints, s.dropbacks), "pd_sack_rate": _ratio(s.pd_sacks, s.pd_dropbacks)}


def split_table(rows: pd.DataFrame, side: Literal["offense", "defense"], opp_skill: str, tiers: TierLookup,
                highlight: int | None, title: str, subject: str) -> dict:
    spec = OFFENSE_METRICS if side == "offense" else DEFENSE_METRICS
    opp_col = "opponent" if side == "offense" else "team"
    df = rows.copy()
    df["tier"] = [tiers.get((int(s), o), {}).get(opp_skill) for s, o in zip(df["season"], df[opp_col])] if len(df) else []
    df = df[df["tier"].notna()] if len(df) else df
    out_rows = []
    for t in (1, 2, 3):
        g = df[df["tier"] == t] if len(df) else df
        games = int(g["game_id"].nunique()) if len(g) else 0
        plays = int(g["dropbacks"].sum()) if len(g) else 0
        metrics = _metrics(g, side) if games else {k: None for k in spec}
        out_rows.append({"tier": t, "games": games, "plays": plays,
                         "smallSample": games < config.MIN_SAMPLE_GAMES or plays < config.MIN_SAMPLE_PLAYS,
                         "metrics": metrics})
    return {
        "title": title,
        "subject": subject,
        "tierSkill": opp_skill,
        "seasons": sorted(int(s) for s in df["season"].unique()) if len(df) else [],
        "highlightTier": None if highlight is None or (isinstance(highlight, float) and math.isnan(highlight)) else int(highlight),
        "metricLabels": {k: v[0] for k, v in spec.items()},
        "metricFormats": {k: v[1] for k, v in spec.items()},
        "rows": out_rows,
    }
