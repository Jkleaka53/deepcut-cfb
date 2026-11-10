"""Per-team-game pass stats and season profiles (with the early-season blend)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm import config
from cfbm.plays import order_key

TG_COLUMNS = ["game_id", "season", "season_type", "week", "order", "team", "opponent", "dropbacks",
              "epa_sum", "epa_n", "success", "sacks", "ints", "pressure_est", "pd_dropbacks",
              "pd_epa_sum", "pd_epa_n", "pd_sacks"]

COUNT_COLS = ["games", "off_dropbacks", "def_dropbacks"]


def team_game_pass(plays: pd.DataFrame) -> pd.DataFrame:
    db = plays[plays["is_dropback"] & ~plays["is_garbage"]].copy()
    if db.empty:
        return pd.DataFrame(columns=TG_COLUMNS)
    db["has_ppa"] = db["ppa"].notna()
    db["ppa0"] = db["ppa"].fillna(0.0)
    db["succ"] = db["ppa"] > 0
    db["pd"] = db["is_passing_down"]
    db["pd_ppa0"] = db["ppa0"].where(db["pd"], 0.0)
    db["pd_has_ppa"] = db["has_ppa"] & db["pd"]
    db["pd_sack"] = db["is_sack"] & db["pd"]
    g = db.groupby(["game_id", "season", "season_type", "week", "offense", "defense"], as_index=False).agg(
        dropbacks=("play_id", "size"), epa_sum=("ppa0", "sum"), epa_n=("has_ppa", "sum"),
        success=("succ", "sum"), sacks=("is_sack", "sum"), ints=("is_int", "sum"),
        pressure_est=("is_pressure_est", "sum"), pd_dropbacks=("pd", "sum"),
        pd_epa_sum=("pd_ppa0", "sum"), pd_epa_n=("pd_has_ppa", "sum"), pd_sacks=("pd_sack", "sum"))
    g = g.rename(columns={"offense": "team", "defense": "opponent"})
    g["order"] = [order_key(st, wk) for st, wk in zip(g["season_type"], g["week"])]
    return g[TG_COLUMNS]


def _div(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > 0, a / np.where(b > 0, b, 1), np.nan)


def _side(rows: pd.DataFrame, key: str, prefix: str) -> pd.DataFrame:
    s = rows.groupby(key)[["dropbacks", "epa_sum", "epa_n", "success", "sacks", "ints", "pressure_est",
                           "pd_dropbacks", "pd_epa_sum", "pd_epa_n", "pd_sacks"]].sum()
    out = pd.DataFrame(index=s.index)
    out[f"{prefix}_dropbacks"] = s["dropbacks"]
    out[f"{prefix}_epa_per_db"] = _div(s["epa_sum"], s["epa_n"])
    out[f"{prefix}_success_rate"] = _div(s["success"], s["epa_n"])
    out[f"{prefix}_sack_rate"] = _div(s["sacks"], s["dropbacks"])
    out[f"{prefix}_int_rate"] = _div(s["ints"], s["dropbacks"])
    out[f"{prefix}_pressure_rate"] = (_div(s["pressure_est"], s["dropbacks"])
                                      if config.PRESSURE_PROXY == "pressure_est" else np.nan)
    out[f"{prefix}_pd_epa"] = _div(s["pd_epa_sum"], s["pd_epa_n"])
    out[f"{prefix}_pd_sack_rate"] = _div(s["pd_sacks"], s["pd_dropbacks"])
    return out


def season_profile(tg: pd.DataFrame, season: int, before_order: int | None,
                   havoc: dict[str, float] | None = None) -> pd.DataFrame:
    rows = tg[tg["season"] == season]
    if before_order is not None:
        rows = rows[rows["order"] < before_order]
    teams = sorted(set(rows["team"]) | set(rows["opponent"]))
    prof = pd.DataFrame(index=pd.Index(teams, name="team"))
    if rows.empty:
        prof["games"] = 0
        return prof
    games = pd.concat([rows[["game_id", "team"]],
                       rows[["game_id", "opponent"]].rename(columns={"opponent": "team"})]
                      ).drop_duplicates().groupby("team").size()
    prof["games"] = games.reindex(prof.index).fillna(0).astype(int)
    prof = prof.join(_side(rows, "team", "off")).join(_side(rows, "opponent", "def"))
    prof["off_dropbacks"] = prof["off_dropbacks"].fillna(0).astype(int)
    prof["def_dropbacks"] = prof["def_dropbacks"].fillna(0).astype(int)
    prof["def_front7_havoc"] = [(havoc or {}).get(t, np.nan) for t in prof.index]
    return prof


def blended_profile(tg: pd.DataFrame, season: int, week: int, season_type: str,
                    havoc_this: dict[str, float] | None,
                    havoc_last: dict[str, float] | None) -> tuple[pd.DataFrame, bool]:
    this = season_profile(tg, season, order_key(season_type, week), havoc_this)
    if season_type != "regular" or week > config.EARLY_SEASON_LAST_WEEK:
        return this, False
    w = (week - 1) / config.EARLY_SEASON_LAST_WEEK
    last = season_profile(tg, season - 1, None, havoc_last)
    teams = this.index.union(last.index)
    this, last = this.reindex(teams), last.reindex(teams)
    out = pd.DataFrame(index=teams)
    for col in this.columns.union(last.columns):
        if col in COUNT_COLS:
            out[col] = this[col].fillna(0).astype(int) if col in this else 0
            continue
        a = this[col] if col in this else pd.Series(np.nan, index=teams)
        b = last[col] if col in last else pd.Series(np.nan, index=teams)
        blended = w * a + (1 - w) * b
        out[col] = blended.where(a.notna() & b.notna(), a.where(a.notna(), b))
    out.index.name = "team"
    return out, True
