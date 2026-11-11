"""Assemble everything into the static JSON files the website reads."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from cfbm import colors, config, fetch
from cfbm.availability import qb_flags, report_for
from cfbm.gotw import pick as pick_gotw
from cfbm.qblog import qb_log, rank_lookup
from cfbm.ranks import ap_poll_for
from cfbm.weather import game_weather, http_fetch
from cfbm.plays import game_orders, normalize_plays, order_key
from cfbm.qb import career, current_starter, passer_games
from cfbm.splits import split_table, tier_lookup
from cfbm.team_stats import RUN_COLUMNS, TG_COLUMNS, blended_profile, fbs_only, season_profile, team_game_stats
from cfbm.tiers import assign_tiers
from cfbm.records import record
from cfbm.units import RUN_TABLES, _gaps, biggest_gap, side_edge, unit_tables
from cfbm.qb import COLUMNS as PASSER_COLUMNS
from cfbm.skill import SKILL_COLUMNS, skill_games
from cfbm.watch import watch_list
from cfbm.backup import backup_block
from cfbm.storylines import game_facts, storylines
from cfbm import shootout, upset
from cfbm.shootout import SHOOT_COLS, SHOOT_FEATURES
from cfbm.swing import swing_block
from cfbm.swing_data import pregame, pregame_adjusted, team_games, training_frame
from cfbm.swing_model import train
from cfbm import edge_model


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


def team_entries(info: dict[str, dict], fbs: set[str]) -> list[dict]:
    out = []
    for school in sorted(fbs):
        t = info.get(school, {})
        logos = t.get("logos") or []
        c, alt = t.get("color"), t.get("alternateColor")
        out.append({
            "school": school, "id": t.get("id"), "abbr": t.get("abbreviation") or school[:4].upper(),
            "conference": t.get("conference"), "fill": colors.fill_for_white_text(c, alt),
            "textLight": colors.text_on("#ffffff", c, alt), "textDark": colors.text_on("#13171c", c, alt),
            "barDark": colors.bar_on("#13171c", c),
            "logo": logos[0] if len(logos) > 0 else None, "logoDark": logos[1] if len(logos) > 1 else None,
        })
    return out


def game_summary(g: dict, fbs: set[str], ranks: dict[str, int] | None = None) -> dict:
    ranks = ranks or {}
    return {
        "id": g["id"], "season": g["season"], "week": g["week"], "seasonType": g["seasonType"],
        "start": g.get("startDate"), "home": g["homeTeam"], "away": g["awayTeam"],
        "homeConf": g.get("homeConference"), "awayConf": g.get("awayConference"),
        "neutral": bool(g.get("neutralSite")), "venue": g.get("venue"), "completed": bool(g.get("completed")),
        "homePoints": g.get("homePoints"), "awayPoints": g.get("awayPoints"),
        "hasBreakdown": g["homeTeam"] in fbs and g["awayTeam"] in fbs,
        "homeRank": ranks.get(g["homeTeam"]), "awayRank": ranks.get(g["awayTeam"]),
        "startTimeTBD": bool(g.get("startTimeTBD")),
    }


class _Data:
    """Everything pulled from CFBD, normalized."""

    def __init__(self, client, seasons_all: list[int], live_season: int):
        self.fbs: dict[int, set[str]] = {}
        self.games: dict[int, list[dict]] = {}
        self.havoc: dict[int, dict[str, float]] = {}
        self.orders: dict[int, int] = {}
        self.teams: dict[int, dict[str, dict]] = {}
        self.venues: dict[int, dict] = fetch.venues(client)
        self.positions: dict[int, str] = fetch.roster_positions(client, live_season, True)
        raw_adv = [r for s in seasons_all for r in fetch.game_advanced(client, s, s == live_season)]
        self.adv = team_games(raw_adv)
        self.shoot = team_games(raw_adv, SHOOT_FEATURES)
        self.game_by_id: dict[int, dict] = {}
        tgs, passers, skill = [], [], []
        for s in seasons_all:
            live = s == live_season
            self.fbs[s] = fetch.fbs_teams(client, s)
            self.teams[s] = fetch.team_info(client, s, live)
            self.games[s] = [g for g in fetch.games(client, s, live)
                             if g["homeTeam"] in self.fbs[s] or g["awayTeam"] in self.fbs[s]]
            self.havoc[s] = fetch.front7_havoc(fetch.advanced_season(client, s, live))
            self.orders.update(game_orders(self.games[s]))
            self.game_by_id.update({g["id"]: g for g in self.games[s]})
            weeks = sorted({(g["seasonType"], g["week"]) for g in self.games[s] if g.get("completed")},
                           key=lambda x: order_key(*x))
            for st, wk in weeks:
                raw = fetch.plays(client, s, st, wk, self.games[s])
                tgs.append(team_game_stats(normalize_plays(raw, s, st, wk)))
                passers.append(passer_games(fetch.player_box(client, s, st, wk, self.games[s]), s, st, wk))
                if live:
                    for cat in ("receiving", "rushing"):
                        skill.append(skill_games(fetch.skill_box(client, s, st, wk, self.games[s], cat), s, st, wk, cat))
        tgs = [t for t in tgs if not t.empty]
        passers = [p for p in passers if not p.empty]
        self.tg = fbs_only(pd.concat(tgs, ignore_index=True) if tgs else pd.DataFrame(columns=TG_COLUMNS + RUN_COLUMNS),
                           self.fbs)
        self.passers = pd.concat(passers, ignore_index=True) if passers else pd.DataFrame(columns=PASSER_COLUMNS)
        skill = [k for k in skill if not k.empty]
        self.skill = pd.concat(skill, ignore_index=True) if skill else pd.DataFrame(columns=SKILL_COLUMNS)
        # Chronological order (postseason by date, since CFBD numbers every bowl week 1).
        for frame in (self.tg, self.passers, self.skill, self.adv, self.shoot):
            if not frame.empty:
                frame["order"] = [self.orders.get(gid, o) for gid, o in zip(frame["game_id"], frame["order"])]
        self.full_tiers = {s: assign_tiers(season_profile(self.tg, s, None, self.havoc.get(s)), self.fbs[s])
                           for s in seasons_all}
        self._asof: dict = {}
        self._adv_fbs: dict[int, pd.DataFrame] = {}
        self._pre_adj: dict[tuple[int, int], pd.DataFrame] = {}
        self.polls: dict[int, list[dict]] = {}

    def adv_fbs(self, season: int) -> pd.DataFrame:
        """FBS-vs-FBS advanced-stat rows, cached per season so the opponent-adjustment cache can hit."""
        if season not in self._adv_fbs:
            fbs = self.fbs[season]
            self._adv_fbs[season] = self.adv[self.adv["team"].isin(fbs) & self.adv["opponent"].isin(fbs)]
        return self._adv_fbs[season]

    def ranks_for(self, g: dict) -> dict[str, int]:
        return ap_poll_for(self.polls.get(g["season"], []), g["seasonType"], g["week"])

    def as_of(self, season: int, season_type: str, week: int, order: int):
        """(profile, ranked, early) for a game: stats strictly before it, with the early-season blend."""
        key = (season, season_type, week, order)
        if key not in self._asof:
            prof, early = blended_profile(self.tg, season, week, season_type,
                                          self.havoc.get(season), self.havoc.get(season - 1),
                                          before_order=order)
            self._asof[key] = (prof, assign_tiers(prof, self.fbs[season]), early)
        return self._asof[key]


def _tier(ranked: pd.DataFrame, team: str, skill: str):
    if team not in ranked.index:
        return None
    v = ranked.loc[team, f"{skill}_tier"]
    return None if pd.isna(v) else int(v)


def _before(rows: pd.DataFrame, season: int, order: int) -> pd.DataFrame:
    return rows[(rows["season"] < season) | ((rows["season"] == season) & (rows["order"] < order))]


def _section(d: _Data, g: dict, off: str, dfn: str, qb, ranked: pd.DataFrame, lookup, order: int,
             ranks=None) -> dict:
    s = g["season"]
    tg = _before(d.tg, s, order)
    recent = tg[tg["season"] >= s - 1]
    splits = []
    qb_vs = None
    if qb is not None:
        aid, name = qb
        games = career(d.passers, aid)[["game_id", "team"]].drop_duplicates()
        rows = tg.merge(games, on=["game_id", "team"])
        rank_map, sizes = ranks or ({}, {})
        qb_vs = {"name": name, "opponent": dfn, "oppRank": rank_map.get((s, dfn)), "of": sizes.get(s),
                 "games": qb_log(rows, d.game_by_id, rank_map)}
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
    return {"offenseTeam": off, "defenseTeam": dfn, "units": [], "splits": splits, "qbVs": qb_vs}


def training_data(client, seasons) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Training frame and per-team-game stats for past seasons (cached CFBD calls). None if too few games."""
    adv, games, fbs = [], {}, {}
    for y in seasons:
        adv += fetch.game_advanced(client, y, False)
        fbs[y] = fetch.fbs_teams(client, y)
        for g in fetch.games(client, y, False):
            games[g["id"]] = g
    tg = team_games(adv)
    frame = training_frame(tg, games, fbs) if not tg.empty else None
    if frame is None or len(frame) < config.MIN_TRAIN_GAMES:
        return None
    return frame, tg


def shootout_inputs(client, seasons) -> tuple[pd.DataFrame, dict[int, dict], dict[int, set[str]]]:
    """Shootout team-game stats, games and FBS sets for the given seasons (cached CFBD calls)."""
    adv, games, fbs = [], {}, {}
    for y in seasons:
        adv += fetch.game_advanced(client, y, False)
        fbs[y] = fetch.fbs_teams(client, y)
        for g in fetch.games(client, y, False):
            games[g["id"]] = g
    return team_games(adv, SHOOT_FEATURES), games, fbs


def train_model(client, seasons) -> dict | None:
    """Fit the swing-factor model on past seasons. None if there isn't enough data."""
    data = training_data(client, seasons)
    return train(*data) if data else None


def edge_training_inputs(client, seasons) -> tuple[pd.DataFrame, dict[int, dict], dict[int, set[str]]]:
    """Team-game stats, games and FBS sets for the edge model's training seasons (cached CFBD calls)."""
    adv, games, fbs = [], {}, {}
    for y in seasons:
        adv += fetch.game_advanced(client, y, False)
        fbs[y] = fetch.fbs_teams(client, y)
        for g in fetch.games(client, y, False):
            games[g["id"]] = g
    return team_games(adv), games, fbs


def edge_training_frame(client, seasons, k: float = config.EDGE_SHRINK_K) -> pd.DataFrame | None:
    """The edge model's training frame for past seasons. None if there are too few games."""
    tg, games, fbs = edge_training_inputs(client, seasons)
    frame = edge_model.frame(tg, games, fbs, k) if not tg.empty else None
    return None if frame is None or len(frame) < config.MIN_TRAIN_GAMES else frame


def train_edge_model(client, seasons) -> dict | None:
    """Fit the edge score's model on past seasons. None if there isn't enough data."""
    frame = edge_training_frame(client, seasons)
    return None if frame is None else edge_model.train(frame)


def _pregame(d: _Data, g: dict, order: int) -> pd.DataFrame:
    """Opponent-adjusted pregame stats: what the edge/swing model reads."""
    s = g["season"]
    key = (s, order)
    if key not in d._pre_adj:  # many games share a kickoff order; the cache lives and dies with this build
        d._pre_adj[key] = pregame_adjusted(d.adv_fbs(s), s, order, w=config.OPP_ADJUST)
    return d._pre_adj[key]


def _pregame_raw(d: _Data, g: dict, order: int) -> pd.DataFrame:
    """Real season-to-date stats: what the swing pulldowns show."""
    s = g["season"]
    return pregame(d.adv_fbs(s), s, order)


def _shoot_pregame(d: _Data, g: dict, order: int) -> pd.DataFrame:
    s = g["season"]
    fbs = d.fbs[s]
    rows = d.shoot[d.shoot["team"].isin(fbs) & d.shoot["opponent"].isin(fbs)]
    return pregame(rows, s, order, SHOOT_COLS)


def shootout_picks(d: _Data, built: list[dict], model: dict, gotw: dict) -> tuple[dict, set[int]]:
    """Score every built game for Shootout of the Week; returns (picks by week, Shootout watch ids)."""
    if not model:
        return {}, set()
    scored = []
    for m in built:
        g = d.game_by_id.get(m["game"]["id"])
        if g is None:
            continue
        pre = _shoot_pregame(d, g, d.orders.get(g["id"], order_key(g["seasonType"], g["week"])))
        sc = shootout.game_score(model, pre, g["homeTeam"], g["awayTeam"], bool(g.get("neutralSite")))
        if sc is not None:
            scored.append((g, sc, shootout.why_text(pre, g["homeTeam"], g["awayTeam"])))
    return shootout.pick(scored, gotw)


def upset_picks(d: _Data, built: list[dict], model: dict, lines: dict[int, dict], gotw: dict,
                shoot: dict) -> dict:
    """Upset Watch: DraftKings' underdog that our (internal) chance likes most, per week."""
    if not model or not lines:
        return {}
    cands = []
    for m in built:
        sw = m.get("swing") or {}
        g = d.game_by_id.get(m["game"]["id"])
        if g is None or not sw.get("overallEdge"):
            continue
        bh = upset.book_prob(lines.get(g["id"]) or {})
        if bh is None:
            continue
        order = d.orders.get(g["id"], order_key(g["seasonType"], g["week"]))
        home, away = g["homeTeam"], g["awayTeam"]
        oh = upset.our_prob(model, _pregame(d, g, order), home, away, bool(g.get("neutralSite")))
        gp = None if oh is None else upset.gap(oh, bh)
        if gp is None:
            continue
        dog, fav = (home, away) if gp[0] == "home" else (away, home)
        if not upset.backs_dog(m, dog):
            continue
        cands.append((g, gp[1], {"why": upset.why_text(m, dog, fav), "odds": upset.odds_block(bh)}))
    skip: dict[str, set[int]] = {}
    for picks in (gotw, shoot):
        for wk, p in picks.items():
            skip.setdefault(wk, set()).add(int(p["id"]))
    return upset.pick(cands, skip)


def train_shootout(client, seasons) -> dict | None:
    rows = shootout.training_rows(*shootout_inputs(client, seasons))
    return shootout.fit(rows) if len(rows) else None


def _swing(d: _Data, g: dict, order: int, qbs: dict, model: dict, pre: pd.DataFrame) -> dict:
    s, home, away = g["season"], g["homeTeam"], g["awayTeam"]
    sw = swing_block(model, home, away, pre, bool(g.get("neutralSite")), raw=_pregame_raw(d, g, order))
    facts, prev = {}, {}
    for t in (away, home):
        q = qbs.get(t)
        ids = []
        if q is not None:
            c = career(d.passers, q[0])
            c = c[(c["team"] == t) & ((c["season"] < s) | ((c["season"] == s) & (c["order"] < order)))]
            ids = list(c["game_id"].unique())
        facts[t] = game_facts(ids, t, d.game_by_id, d.venues)
        earlier = [x for x in d.games[s] if t in (x["homeTeam"], x["awayTeam"]) and x.get("startDate")
                   and d.orders.get(x["id"], 0) < order]
        prev[t] = max((x["startDate"] for x in earlier), default=None)
    team_loc = {t: (d.teams.get(s, {}).get(t) or {}).get("location") for t in (away, home)}
    venue = d.venues.get(g.get("venueId")) if g.get("venueId") is not None else None
    sw["storylines"] = storylines(g, qbs, facts, team_loc, venue, prev)
    return sw


def matchup(d: _Data, g: dict, model: dict | None = None) -> dict:
    s, st, wk = g["season"], g["seasonType"], g["week"]
    order = d.orders.get(g["id"], order_key(st, wk))
    prof, ranked, early = d.as_of(s, st, wk, order)
    frames = {y: t for y, t in d.full_tiers.items() if y < s}
    frames[s] = ranked
    lookup = tier_lookup(frames)
    ranks = rank_lookup(frames)
    home, away = g["homeTeam"], g["awayTeam"]
    qbs = {t: current_starter(d.passers, t, s, order) for t in (away, home)}
    pre = _pregame(d, g, order) if model else None
    sections = []
    for off, dfn in ((away, home), (home, away)):
        sec = _section(d, g, off, dfn, qbs[off], ranked, lookup, order, ranks)
        sec["units"] = unit_tables(off, dfn, prof, ranked)
        rows = [r for u in sec["units"] for r in u["rows"]]
        sec["edge"] = side_edge(rows)
        sec["biggestGap"] = biggest_gap(rows)
        sec["runUnits"] = unit_tables(off, dfn, prof, ranked, RUN_TABLES)
        run_rows = [r for u in sec["runUnits"] for r in u["rows"]]
        sec["runEdge"] = side_edge(run_rows)
        sec["runBiggestGap"] = biggest_gap(run_rows)
        sections.append(sec)
    swing = _swing(d, g, order, qbs, model, pre) if model else None
    key_rows = (swing or {}).pop("keyRows", {}) if swing else {}
    for sec in sections:
        for u in sec["units"] + sec["runUnits"]:
            for r in u["rows"]:
                r["isKey"] = r["key"] in key_rows.get(sec["offenseTeam"], [])
    notes = []
    if st == "postseason":
        notes.append(config.BOWL_NOTE)
    if early:
        notes.append(config.EARLY_NOTE)
    return {
        "game": game_summary(g, d.fbs[s], d.ranks_for(g)),
        "earlySeason": early,
        "notes": notes,
        "quarterbacks": {t: (None if q is None else {"athleteId": q[0], "name": q[1]}) for t, q in qbs.items()},
        "sections": sections,
        "records": {t: record(d.games[s], t, order, d.orders) for t in (away, home)},
        "swing": swing,
        "availability": {t: {"flags": qb_flags(d.passers, t, s, order),
                             "report": report_for((d.teams.get(s, {}).get(t) or {}).get("conference")),
                             **_watch(d, s, order, t, dfn, qbs[t], prof, ranked, ranks)}
                         for t, dfn in ((away, home), (home, away))},
    }


def _watch(d: _Data, s: int, order: int, team: str, dfn: str, qb, prof, ranked, ranks) -> dict:
    wl = watch_list(d.passers, d.skill, team, s, order, qb, d.positions)
    backup = None
    if wl["backupId"] is not None:
        bid = wl["backupId"]
        name = next(p["name"] for p in wl["players"] if p["athleteId"] == bid)
        games = career(d.passers, bid)[["game_id", "team"]].drop_duplicates()
        rows = _before(d.tg, s, order).merge(games, on=["game_id", "team"])
        backup = backup_block(rows, name, bid, prof, ranked.index, d.game_by_id, ranks[0])
        backup["qbVs"].update({"opponent": dfn, "oppRank": ranks[0].get((s, dfn)), "of": ranks[1].get(s)})
    return {"players": wl["players"], "backup": backup}


STALE_AFTER = timedelta(days=2)


def _start(g: dict) -> datetime | None:
    try:
        return datetime.fromisoformat((g.get("startDate") or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def _current(games: list[dict], now: datetime) -> tuple[int, str]:
    """Week of the next unfinished game. Games still unfinished days after kickoff (postponed or
    cancelled) are ignored so they can't pin the site to an old week."""
    ordered = sorted(games, key=lambda g: (g.get("startDate") or "", g["id"]))
    pending = [g for g in ordered if not g.get("completed")
               and (_start(g) is None or _start(g) >= now - STALE_AFTER)]
    g = pending[0] if pending else ordered[-1]
    return g["week"], g["seasonType"]


def biggest_gap_row(rows: list[dict]) -> dict | None:
    g = _gaps(rows)
    return max(g, key=lambda x: abs(x[0]))[1] if g else None


# Too few plays per team to headline the home page chip (still shown on the game page).
CHIP_SKIP = {"power_success"}


def summary_gap(m: dict) -> dict | None:
    """The single widest rank gap across both sections, passing and running, and which team it favors."""
    best = None
    for sec in m["sections"]:
        for units, key in ((sec["units"], "biggestGap"), (sec.get("runUnits", []), "runBiggestGap")):
            rows = {r["key"]: r for u in units for r in u["rows"]}
            r = rows.get(sec.get(key))
            if r is None or r["key"] in CHIP_SKIP:
                r = biggest_gap_row([x for x in rows.values() if x["key"] not in CHIP_SKIP])
            if r is None:
                continue
            gap = r["offense"]["pct"] - r["defense"]["pct"]
            if best is None or abs(gap) > abs(best[0]):
                best = (gap, r, sec["offenseTeam"] if gap > 0 else sec["defenseTeam"])
    if best is None:
        return None
    return {"key": best[1]["key"], "label": best[1]["label"], "favors": best[2]}


def venue_block(v: dict | None) -> dict | None:
    if not v:
        return None
    return {"name": v.get("name"), "city": v.get("city"), "state": v.get("state"), "grass": v.get("grass"),
            "dome": v.get("dome")}


def build(client, out_dir: Path, seasons=config.DISPLAY_SEASONS, now: datetime | None = None,
          career_start: int = config.CAREER_START_SEASON, weather_fetch=None, model: dict | None = None,
          train_seasons=config.TRAIN_SEASONS, shootout_model: dict | None = None) -> None:
    out_dir = Path(out_dir)
    live = max(seasons)
    seasons_all = list(range(min(career_start, min(seasons)), live + 1))
    d = _Data(client, seasons_all, live)
    if model is None:
        model = train_model(client, train_seasons)
    if shootout_model is None:
        shootout_model = train_shootout(client, train_seasons)
    now = now or datetime.now(timezone.utc)
    fetch_json = weather_fetch or http_fetch
    calls: dict = {}

    def cached_fetch(url, params):
        key = (url, tuple(sorted(params.items())))
        if key not in calls:
            try:
                calls[key] = fetch_json(url, params)
            except Exception as e:  # noqa: BLE001
                calls[key] = e
        if isinstance(calls[key], Exception):
            raise calls[key]
        return calls[key]

    for s in seasons:
        _write(out_dir / str(s) / "teams.json", team_entries(d.teams[s], d.fbs[s]))
        polls = d.polls[s] = fetch.rankings(client, s, s == live)
        summaries = [game_summary(g, d.fbs[s], ap_poll_for(polls, g["seasonType"], g["week"])) for g in d.games[s]]
        for g, summ in zip(d.games[s], summaries):
            v = d.venues.get(g.get("venueId"))
            summ["gap"] = None
            summ["keyFactor"] = None
            summ["edge"] = None
            summ["weather"] = game_weather(v, g.get("startDate"), bool(g.get("startTimeTBD")),
                                           bool(g.get("completed")), now, cached_fetch)
        built = []
        for g, summ in zip(d.games[s], summaries):
            if summ["hasBreakdown"]:
                m = matchup(d, g, model)
                top = (m["swing"] or {}).get("drivers") or [] if m.get("swing") else []
                summ["keyFactor"] = m["game"]["keyFactor"] = (
                    {"label": top[0]["label"], "favors": top[0]["favors"]} if top else None)
                m["game"]["weather"] = summ["weather"]
                m["venue"] = venue_block(d.venues.get(g.get("venueId")))
                summ["gap"] = m["game"]["gap"] = summary_gap(m)
                o = (m["swing"] or {}).get("overallEdge") if m.get("swing") else None
                summ["edge"] = m["game"]["edge"] = (
                    {"band": o["edge"], "team": o["team"], "score": o["score"]} if o and o["edge"] != "even" else None)
                _write(out_dir / str(s) / "matchups" / f"{g['id']}.json", m)
                built.append(m)
        gotw = pick_gotw(built)
        shoot, watch = shootout_picks(d, built, shootout_model, gotw)
        for summ in summaries:
            summ["shootoutWatch"] = summ["id"] in watch
        _write(out_dir / str(s) / "games.json", summaries)
        _write(out_dir / str(s) / "gotw.json", gotw)
        _write(out_dir / str(s) / "shootout.json", shoot)
        lines = {ln["id"]: ln for ln in fetch.lines(client, s, s == live)}
        _write(out_dir / str(s) / "upset.json", upset_picks(d, built, model, lines, gotw, shoot))

    week, st = _current(d.games[live], now) if d.games[live] else (1, "regular")
    _write(out_dir / "index.json", {
        "seasons": sorted(seasons), "currentSeason": live, "currentWeek": week, "seasonType": st,
        "generatedAt": now.isoformat(),
    })

    p = d.passers[d.passers["is_primary"] & d.passers["season"].isin(list(seasons))]
    players = (p[["athlete_id", "name", "team", "season"]].drop_duplicates()
               .sort_values(["season", "team", "name"]))
    _write(out_dir / "players.json", [
        {"athleteId": r.athlete_id, "name": r.name, "team": r.team, "position": "QB", "season": r.season}
        for r in players.itertuples()])
