"""Rank FBS teams into thirds for each pass skill, plus per-metric ranks and percentiles."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from cfbm import config

SKILLS = ("pass_defense", "pass_rush", "pass_offense", "pass_protection")

# +1: higher is better for that side. -1: lower is better.
METRIC_DIRECTION = {
    "off_epa_per_db": 1, "off_success_rate": 1, "off_sack_rate": -1, "off_int_rate": -1,
    "off_pressure_rate": -1, "off_pd_epa": 1, "off_pd_sack_rate": -1,
    "def_epa_per_db": -1, "def_success_rate": -1, "def_sack_rate": 1, "def_int_rate": 1,
    "def_pressure_rate": 1, "def_pd_epa": -1, "def_pd_sack_rate": 1, "def_front7_havoc": 1,
    # Run phase (Slice 4)
    "off_rush_epa": 1, "off_line_yards": 1, "off_stuff_rate": -1, "off_power_success": 1,
    "off_second_level": 1, "off_open_field": 1,
    "def_rush_epa": -1, "def_line_yards": -1, "def_stuff_rate": 1, "def_power_success": -1,
    "def_second_level": -1, "def_open_field": -1,
}


def _z(s: pd.Series) -> pd.Series:
    sd = s.std()
    if not sd or math.isnan(sd):
        return s * 0
    return (s - s.mean()) / sd


def _col(p: pd.DataFrame, name: str) -> pd.Series:
    return p[name] if name in p else pd.Series(np.nan, index=p.index)


def _scores(p: pd.DataFrame) -> dict[str, pd.Series]:
    if config.PRESSURE_PROXY == "pressure_est":
        rush_parts = [_z(_col(p, "def_sack_rate")), _z(_col(p, "def_pressure_rate"))]
        prot_parts = [-_z(_col(p, "off_sack_rate")), -_z(_col(p, "off_pressure_rate"))]
    else:
        rush_parts = [_z(_col(p, "def_sack_rate")), _z(_col(p, "def_front7_havoc"))]
        prot_parts = [-_z(_col(p, "off_sack_rate"))]

    def mean_parts(parts):
        # A team needs its first part (sack rate); missing secondary parts fall back to the first.
        df = pd.concat(parts, axis=1)
        return df.mean(axis=1, skipna=True).where(df.iloc[:, 0].notna())

    return {
        "pass_defense": -_col(p, "def_epa_per_db"),
        "pass_offense": _col(p, "off_epa_per_db"),
        "pass_rush": mean_parts(rush_parts),
        "pass_protection": mean_parts(prot_parts),
    }


def _thirds(rank: pd.Series, n: int) -> pd.Series:
    size = math.ceil(n / 3) if n else 0
    return rank.apply(lambda r: np.nan if pd.isna(r) else (1 if r <= size else 2 if r <= 2 * size else 3))


def assign_tiers(profile: pd.DataFrame, fbs: set[str]) -> pd.DataFrame:
    p = profile[profile.index.isin(fbs)]
    out = pd.DataFrame(index=p.index)
    for skill, score in _scores(p).items():
        out[f"{skill}_score"] = score
        rank = score.rank(ascending=False, method="first")
        out[f"{skill}_rank"] = rank
        out[f"{skill}_tier"] = _thirds(rank, int(score.notna().sum()))
    for metric, direction in METRIC_DIRECTION.items():
        if metric not in p:
            continue
        vals = p[metric] * direction
        n = int(vals.notna().sum())
        rank = vals.rank(ascending=False, method="min")
        out[f"{metric}_rank"] = rank
        out[f"{metric}_pct"] = (n - rank) / (n - 1) * 100 if n > 1 else np.where(rank.notna(), 50.0, np.nan)
    return out
