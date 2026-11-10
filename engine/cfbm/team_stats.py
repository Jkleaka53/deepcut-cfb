"""Per-team-game pass stats and season profiles (with the early-season blend)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cfbm import config
from cfbm.plays import order_key

TG_COLUMNS = ["game_id", "season", "season_type", "week", "order", "team", "opponent", "dropbacks",
              "epa_sum", "epa_n", "success", "sacks", "ints", "pressure_est", "pd_dropbacks",
              "pd_epa_sum", "pd_epa_n", "pd_sacks"]

RUN_COLUMNS = ["runs", "rush_epa_sum", "rush_epa_n", "line_yards_sum", "second_level_sum", "open_field_sum",
               "stuffs", "power_n", "power_conv"]
KEYS = ["game_id", "season", "season_type", "week", "order", "team", "opponent"]

COUNT_COLS = ["games", "off_dropbacks", "def_dropbacks", "off_runs", "def_runs"]


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


def team_game_run(plays: pd.DataFrame) -> pd.DataFrame:
    """Per team-game rushing totals. Line yards use the Football Outsiders rule: losses count 120%,
    the first 4 yards 100%, yards 5 to 10 50%, nothing past 10. Power = 3rd/4th and 2 or less,
    or 2 yards or less from the goal line; converted when the run gains the distance."""
    r = plays[plays["is_rush"] & ~plays["is_garbage"]].copy()
    if r.empty:
        return pd.DataFrame(columns=KEYS + RUN_COLUMNS)
    y = r["yards"].fillna(0.0)
    r["has_ppa"] = r["ppa"].notna()
    r["ppa0"] = r["ppa"].fillna(0.0)
    r["line"] = np.where(y < 0, 1.2 * y, np.minimum(y, 4) + 0.5 * np.clip(y - 4, 0, 6))
    r["second"] = np.clip(y - 5, 0, 5)
    r["open"] = np.clip(y - 10, 0, None)
    r["stuff"] = y <= 0
    dist = pd.to_numeric(r["distance"], errors="coerce")
    r["power"] = (r["down"].isin([3, 4]) & (dist <= 2)) | (r["yards_to_goal"] <= 2)
    r["conv"] = r["power"] & ((y >= dist) | (r["play_type"] == "Rushing Touchdown"))
    g = r.groupby(["game_id", "season", "season_type", "week", "offense", "defense"], as_index=False).agg(
        runs=("play_id", "size"), rush_epa_sum=("ppa0", "sum"), rush_epa_n=("has_ppa", "sum"),
        line_yards_sum=("line", "sum"), second_level_sum=("second", "sum"), open_field_sum=("open", "sum"),
        stuffs=("stuff", "sum"), power_n=("power", "sum"), power_conv=("conv", "sum"))
    g = g.rename(columns={"offense": "team", "defense": "opponent"})
    g["order"] = [order_key(st, wk) for st, wk in zip(g["season_type"], g["week"])]
    return g[KEYS + RUN_COLUMNS]


def team_game_stats(plays: pd.DataFrame) -> pd.DataFrame:
    """Pass and run totals per team-game in one frame; a side with no plays of a kind gets zeros."""
    p, r = team_game_pass(plays), team_game_run(plays)
    if p.empty and r.empty:
        return pd.DataFrame(columns=TG_COLUMNS + RUN_COLUMNS)
    out = p.merge(r, on=KEYS, how="outer") if not p.empty and not r.empty else (p if r.empty else r).copy()
    for c in TG_COLUMNS + RUN_COLUMNS:
        if c not in out:
            out[c] = 0
        elif c not in KEYS:
            out[c] = out[c].fillna(0)
    return out[TG_COLUMNS + RUN_COLUMNS]


def fbs_only(tg: pd.DataFrame, fbs_by_season: dict[int, set[str]]) -> pd.DataFrame:
    """Keep only games where both teams were FBS that season, so FCS games never shape FBS numbers."""
    if tg.empty:
        return tg
    keep = [t in fbs_by_season.get(int(s), set()) and o in fbs_by_season.get(int(s), set())
            for s, t, o in zip(tg["season"], tg["team"], tg["opponent"])]
    return tg[keep].reset_index(drop=True)


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
    if "runs" in rows:
        r = rows.groupby(key)[RUN_COLUMNS].sum()
        out[f"{prefix}_runs"] = r["runs"]
        out[f"{prefix}_rush_epa"] = _div(r["rush_epa_sum"], r["rush_epa_n"])
        out[f"{prefix}_line_yards"] = _div(r["line_yards_sum"], r["runs"])
        out[f"{prefix}_second_level"] = _div(r["second_level_sum"], r["runs"])
        out[f"{prefix}_open_field"] = _div(r["open_field_sum"], r["runs"])
        out[f"{prefix}_stuff_rate"] = _div(r["stuffs"], r["runs"])
        out[f"{prefix}_power_success"] = _div(r["power_conv"], r["power_n"])
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
    for c in ("off_runs", "def_runs"):
        if c in prof:
            prof[c] = prof[c].fillna(0).astype(int)
    prof["def_front7_havoc"] = [(havoc or {}).get(t, np.nan) for t in prof.index]
    return prof


def blended_profile(tg: pd.DataFrame, season: int, week: int, season_type: str,
                    havoc_this: dict[str, float] | None,
                    havoc_last: dict[str, float] | None,
                    before_order: int | None = None) -> tuple[pd.DataFrame, bool]:
    cutoff = before_order if before_order is not None else order_key(season_type, week)
    this = season_profile(tg, season, cutoff, havoc_this)
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
