"""Assemble everything into the static JSON files the website reads."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from cfbm import config, fetch
from cfbm.plays import normalize_plays, order_key
from cfbm.qb import career, current_starter, passer_games
from cfbm.splits import split_table, tier_lookup
from cfbm.team_stats import TG_COLUMNS, blended_profile, fbs_only, season_profile, team_game_pass
from cfbm.tiers import assign_tiers
from cfbm.units import unit_tables
from cfbm.qb import COLUMNS as PASSER_COLUMNS


def to_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    return obj


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_json_safe(data), ensure_ascii=False, separators=(",", ":"), allow_nan=False))


def game_summary(g: dict, fbs: set[str]) -> dict:
    return {
        "id": g["id"], "season": g["season"], "week": g["week"], "seasonType": g["seasonType"],
        "start": g.get("startDate"), "home": g["homeTeam"], "away": g["awayTeam"],
        "homeConf": g.get("homeConference"), "awayConf": g.get("awayConference"),
        "neutral": bool(g.get("neutralSite")), "venue": g.get("venue"), "completed": bool(g.get("completed")),
        "homePoints": g.get("homePoints"), "awayPoints": g.get("awayPoints"),
        "hasBreakdown": g["homeTeam"] in fbs and g["awayTeam"] in fbs,
    }


class _Data:
    """Everything pulled from CFBD, normalized."""

    def __init__(self, client, seasons_all: list[int], live_season: int):
        self.fbs: dict[int, set[str]] = {}
        self.games: dict[int, list[dict]] = {}
        self.havoc: dict[int, dict[str, float]] = {}
        tgs, passers = [], []
        for s in seasons_all:
            live = s == live_season
            self.fbs[s] = fetch.fbs_teams(client, s)
            self.games[s] = [g for g in fetch.games(client, s, live)
                             if g["homeTeam"] in self.fbs[s] or g["awayTeam"] in self.fbs[s]]
            self.havoc[s] = fetch.front7_havoc(fetch.advanced_season(client, s, live))
            weeks = sorted({(g["seasonType"], g["week"]) for g in self.games[s] if g.get("completed")},
                           key=lambda x: order_key(*x))
            for st, wk in weeks:
                raw = fetch.plays(client, s, st, wk, self.games[s])
                tgs.append(team_game_pass(normalize_plays(raw, s, st, wk)))
                passers.append(passer_games(fetch.player_box(client, s, st, wk, self.games[s]), s, st, wk))
        tgs = [t for t in tgs if not t.empty]
        passers = [p for p in passers if not p.empty]
        self.tg = fbs_only(pd.concat(tgs, ignore_index=True) if tgs else pd.DataFrame(columns=TG_COLUMNS),
                           self.fbs)
        self.passers = pd.concat(passers, ignore_index=True) if passers else pd.DataFrame(columns=PASSER_COLUMNS)
        self.full_tiers = {s: assign_tiers(season_profile(self.tg, s, None, self.havoc.get(s)), self.fbs[s])
                           for s in seasons_all}
        self._asof: dict = {}

    def as_of(self, season: int, season_type: str, week: int):
        """(profile, ranked, early) for a game: stats strictly before it, with the early-season blend."""
        key = (season, season_type, week)
        if key not in self._asof:
            prof, early = blended_profile(self.tg, season, week, season_type,
                                          self.havoc.get(season), self.havoc.get(season - 1))
            self._asof[key] = (prof, assign_tiers(prof, self.fbs[season]), early)
        return self._asof[key]


def _tier(ranked: pd.DataFrame, team: str, skill: str):
    if team not in ranked.index:
        return None
    v = ranked.loc[team, f"{skill}_tier"]
    return None if pd.isna(v) else int(v)


def _before(rows: pd.DataFrame, season: int, order: int) -> pd.DataFrame:
    return rows[(rows["season"] < season) | ((rows["season"] == season) & (rows["order"] < order))]


def _section(d: _Data, g: dict, off: str, dfn: str, qb, ranked: pd.DataFrame, lookup, order: int) -> dict:
    s = g["season"]
    tg = _before(d.tg, s, order)
    recent = tg[tg["season"] >= s - 1]
    splits = []
    if qb is not None:
        aid, name = qb
        games = career(d.passers, aid)[["game_id", "team"]].drop_duplicates()
        rows = tg.merge(games, on=["game_id", "team"])
        splits.append(split_table(rows, "offense", "pass_defense", lookup, _tier(ranked, dfn, "pass_defense"),
                                  f"{name} vs. pass defenses by strength", name))
    splits.append(split_table(recent[recent["team"] == off], "offense", "pass_rush", lookup,
                              _tier(ranked, dfn, "pass_rush"),
                              f"{off} pass protection vs. pass rushes by strength", off))
    d_rows = recent[recent["opponent"] == dfn]
    splits.append(split_table(d_rows, "defense", "pass_offense", lookup, _tier(ranked, off, "pass_offense"),
                              f"{dfn} pass defense vs. passing offenses by strength", dfn))
    splits.append(split_table(d_rows, "defense", "pass_protection", lookup, _tier(ranked, off, "pass_protection"),
                              f"{dfn} pass rush vs. pass protection by strength", dfn))
    return {"offenseTeam": off, "defenseTeam": dfn, "units": [], "splits": splits}


def matchup(d: _Data, g: dict) -> dict:
    s, st, wk = g["season"], g["seasonType"], g["week"]
    order = order_key(st, wk)
    prof, ranked, early = d.as_of(s, st, wk)
    frames = {y: t for y, t in d.full_tiers.items() if y < s}
    frames[s] = ranked
    lookup = tier_lookup(frames)
    home, away = g["homeTeam"], g["awayTeam"]
    qbs = {t: current_starter(d.passers, t, s, order) for t in (away, home)}
    sections = []
    for off, dfn in ((away, home), (home, away)):
        sec = _section(d, g, off, dfn, qbs[off], ranked, lookup, order)
        sec["units"] = unit_tables(off, dfn, prof, ranked)
        sections.append(sec)
    notes = []
    if st == "postseason":
        notes.append(config.BOWL_NOTE)
    if early:
        notes.append(config.EARLY_NOTE)
    return {
        "game": game_summary(g, d.fbs[s]),
        "earlySeason": early,
        "notes": notes,
        "quarterbacks": {t: (None if q is None else {"athleteId": q[0], "name": q[1]}) for t, q in qbs.items()},
        "sections": sections,
    }


def _current(games: list[dict]) -> tuple[int, str]:
    ordered = sorted(games, key=lambda g: (g.get("startDate") or "", g["id"]))
    pending = [g for g in ordered if not g.get("completed")]
    g = pending[0] if pending else ordered[-1]
    return g["week"], g["seasonType"]


def build(client, out_dir: Path, seasons=config.DISPLAY_SEASONS, now: datetime | None = None,
          career_start: int = config.CAREER_START_SEASON) -> None:
    out_dir = Path(out_dir)
    live = max(seasons)
    seasons_all = list(range(min(career_start, min(seasons)), live + 1))
    d = _Data(client, seasons_all, live)

    for s in seasons:
        summaries = [game_summary(g, d.fbs[s]) for g in d.games[s]]
        _write(out_dir / str(s) / "games.json", summaries)
        for g, summ in zip(d.games[s], summaries):
            if summ["hasBreakdown"]:
                _write(out_dir / str(s) / "matchups" / f"{g['id']}.json", matchup(d, g))

    week, st = _current(d.games[live]) if d.games[live] else (1, "regular")
    _write(out_dir / "index.json", {
        "seasons": sorted(seasons), "currentSeason": live, "currentWeek": week, "seasonType": st,
        "generatedAt": (now or datetime.now(timezone.utc)).isoformat(),
    })

    p = d.passers[d.passers["is_primary"] & d.passers["season"].isin(list(seasons))]
    players = (p[["athlete_id", "name", "team", "season"]].drop_duplicates()
               .sort_values(["season", "team", "name"]))
    _write(out_dir / "players.json", [
        {"athleteId": r.athlete_id, "name": r.name, "team": r.team, "position": "QB", "season": r.season}
        for r in players.itertuples()])
