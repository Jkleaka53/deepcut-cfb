import json
import math
from datetime import datetime, timezone

import numpy as np
import pytest

from cfbm import config
from cfbm.export import build, game_summary, to_json_safe

FBS = ["A", "B", "C", "D", "E", "F"]


def _plays(gid, home, away, week, n=12):
    out, i = [], gid * 1000
    for off, dfn in ((home, away), (away, home)):
        for k in range(n):
            i += 1
            ptype = "Sack" if k % 6 == 0 else ("Pass Reception" if k % 2 else "Pass Incompletion")
            out.append({"id": str(i), "gameId": gid, "offense": off, "defense": dfn, "home": home, "away": away,
                        "offenseScore": 0, "defenseScore": 0, "period": 1, "down": 3 if k % 3 == 0 else 1,
                        "distance": 7, "playType": ptype, "playText": "", "ppa": 0.3 if off == home else -0.1})
        for k in range(4):  # runs: home gains 6, away is stuffed
            i += 1
            out.append({"id": str(i), "gameId": gid, "offense": off, "defense": dfn, "home": home, "away": away,
                        "offenseScore": 0, "defenseScore": 0, "period": 1, "down": 1, "distance": 10,
                        "playType": "Rush", "playText": "", "ppa": 0.2 if off == home else -0.3,
                        "yardsGained": 6 if off == home else -1, "yardsToGoal": 60})
    return out


def _box(gid, home, away, category="passing"):
    def team(t):
        base = abs(hash(t)) % 10000
        if category == "receiving":
            return {"team": t, "categories": [{"name": "receiving", "types": [
                {"name": "REC", "athletes": [{"id": str(base + 2 + k), "name": f"{t} WR{k}", "stat": str(5 - k)} for k in range(4)]},
                {"name": "YDS", "athletes": [{"id": str(base + 2 + k), "name": f"{t} WR{k}", "stat": str(80 - 15 * k)} for k in range(4)]}]}]}
        if category == "rushing":
            return {"team": t, "categories": [{"name": "rushing", "types": [
                {"name": "CAR", "athletes": [{"id": str(base + 9), "name": f"{t} RB", "stat": "15"}]},
                {"name": "YDS", "athletes": [{"id": str(base + 9), "name": f"{t} RB", "stat": "70"}]}]}]}
        qbs = [{"id": str(base + 1), "name": f"{t} QB", "stat": "10/20"}]
        if t == "A" and gid == 4:
            qbs.append({"id": str(base + 8), "name": "A Backup", "stat": "1/2"})
        return {"team": t, "categories": [{"name": "passing", "types": [{"name": "C/ATT", "athletes": qbs}]}]}
    return {"id": gid, "teams": [team(home), team(away)]}


def _world():
    sched = [  # (id, seasonType, week, home, away, neutral, completed)
        (1, "regular", 1, "A", "B", False, True), (2, "regular", 1, "C", "D", False, True),
        (3, "regular", 1, "E", "F", False, True), (4, "regular", 2, "A", "C", False, True),
        (5, "regular", 2, "B", "E", False, True), (6, "regular", 2, "D", "FCS U", False, True),
        (7, "regular", 3, "F", "A", False, False), (8, "postseason", 1, "B", "C", True, True),
        (9, "postseason", 1, "B", "A", True, False),
    ]
    games = [{"id": i, "season": 2025, "week": wk, "seasonType": st, "startDate": f"2025-09-{wk + (20 + i if st == 'postseason' else 0):02d}T19:00:00.000Z",
              "homeTeam": h, "awayTeam": a, "homeConference": "Conf" if h in FBS else None,
              "awayConference": "Conf" if a in FBS else None, "neutralSite": neu, "venue": "Stadium", "venueId": 1, "startTimeTBD": False,
              "completed": done, "homePoints": 21 if done else None, "awayPoints": 14 if done else None}
             for i, st, wk, h, a, neu, done in sched]
    return games


class WorldClient:
    def __init__(self):
        self.games = _world()
        self.calls_made = 0

    def get(self, path, params, *, cacheable=True):
        self.calls_made += 1
        if path == "/teams/fbs":
            return [{"school": t} for t in FBS]
        if path == "/teams":
            return [{"id": 100 + i, "school": t, "abbreviation": t * 2, "conference": "Conf", "color": "#eaaa00",
                     "alternateColor": "#002855", "logos": [f"https://x/{t}.png", f"https://x/d/{t}.png"]}
                    for i, t in enumerate(FBS)] + [{"id": 999, "school": "FCS U", "abbreviation": "FU",
                                                    "conference": "X", "color": None, "alternateColor": None, "logos": None}]
        if path == "/rankings":
            return [{"season": 2025, "seasonType": "regular", "week": 3,
                     "polls": [{"poll": "AP Top 25", "ranks": [{"rank": 7, "school": "A"}]}]}]
        if path == "/venues":
            return [{"id": 1, "name": "Stadium", "city": "Town", "state": "ST", "latitude": 40.0, "longitude": -80.0,
                     "dome": False, "grass": True, "timezone": "America/New_York"}]
        if path == "/games":
            return [g for g in self.games if g["seasonType"] == params["seasonType"] and params["year"] == 2025]
        if path == "/stats/game/advanced":
            return []
        if path == "/roster":
            return []
        if path == "/stats/season/advanced":
            return [{"team": t, "defense": {"havoc": {"frontSeven": 0.05 + i / 100}}} for i, t in enumerate(FBS)]
        wk = [g for g in self.games if g["seasonType"] == params.get("seasonType") and g["week"] == params.get("week")
              and g["completed"] and params["year"] == 2025]
        if path == "/plays":
            return [p for g in wk for p in _plays(g["id"], g["homeTeam"], g["awayTeam"], g["week"])]
        if path == "/games/players":
            return [_box(g["id"], g["homeTeam"], g["awayTeam"], params.get("category", "passing")) for g in wk]
        return []


def _fake_weather(url, params):
    hours = [f"2025-09-{d:02d}T{h:02d}:00" for d in range(1, 30) for h in range(24)]
    n = len(hours)
    return {"hourly": {"time": hours, "temperature_2m": [70.0] * n, "precipitation_probability": [5] * n,
                       "wind_speed_10m": [4.0] * n, "wind_gusts_10m": [9.0] * n, "weather_code": [0] * n}}


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    build(WorldClient(), d, seasons=(2025,), career_start=2025,
          now=datetime(2025, 9, 2, tzinfo=timezone.utc), weather_fetch=_fake_weather)
    return d


def _load(path):
    def bad(c):
        raise ValueError(f"non-JSON constant {c}")
    return json.loads(path.read_text(), parse_constant=bad)


def test_files_written(out):
    assert (out / "index.json").exists() and (out / "players.json").exists()
    games = _load(out / "2025" / "games.json")
    assert len(games) == 9
    files = sorted(p.stem for p in (out / "2025" / "matchups").glob("*.json"))
    assert files == ["1", "2", "3", "4", "5", "7", "8", "9"]  # game 6 has an FCS team
    g6 = next(g for g in games if g["id"] == 6)
    assert g6["hasBreakdown"] is False


def test_no_nan_in_output(out):
    for p in out.rglob("*.json"):
        _load(p)


def test_index_points_at_first_unfinished_week(out):
    ix = _load(out / "index.json")
    assert ix["seasons"] == [2025] and ix["currentSeason"] == 2025
    assert ix["currentWeek"] == 3 and ix["seasonType"] == "regular"


def test_sections_order_away_offense_first(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    assert [s["offenseTeam"] for s in m["sections"]] == ["A", "F"]
    assert [s["defenseTeam"] for s in m["sections"]] == ["F", "A"]
    assert len(m["sections"][0]["units"]) == 2


def test_split_tables_present_with_three_rows(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    sec = m["sections"][0]
    assert len(sec["splits"]) == 4  # QB, protection, defense, pass rush
    assert all([r["tier"] for r in t["rows"]] == [1, 2, 3] for t in sec["splits"])
    assert sec["splits"][0]["tierSkill"] == "pass_defense"
    assert m["quarterbacks"]["A"]["name"] == "A QB"


def test_postseason_note_and_neutral(out):
    m = _load(out / "2025" / "matchups" / "8.json")
    assert config.BOWL_NOTE in m["notes"] and m["game"]["neutral"] is True and m["game"]["seasonType"] == "postseason"


def test_early_note_week2(out):
    m = _load(out / "2025" / "matchups" / "4.json")
    assert m["earlySeason"] is True and config.EARLY_NOTE in m["notes"]


def test_completed_game_has_points(out):
    m = _load(out / "2025" / "matchups" / "4.json")
    assert m["game"]["completed"] and m["game"]["homePoints"] == 21


def test_missing_starter_omits_qb_table(out):
    m = _load(out / "2025" / "matchups" / "1.json")  # week 1: no prior games
    assert m["quarterbacks"] == {"A": None, "B": None}
    assert len(m["sections"][0]["splits"]) == 3


def test_players_index(out):
    players = _load(out / "players.json")
    assert {"athleteId", "name", "team", "position", "season"} <= set(players[0])
    assert {p["team"] for p in players} >= {"A", "B"}


def test_game_summary_shape():
    g = _world()[0]
    s = game_summary(g, set(FBS))
    assert s == {"id": 1, "season": 2025, "week": 1, "seasonType": "regular", "start": g["startDate"], "home": "A",
                 "away": "B", "homeConf": "Conf", "awayConf": "Conf", "neutral": False, "venue": "Stadium",
                 "completed": True, "homePoints": 21, "awayPoints": 14, "hasBreakdown": True,
                 "homeRank": None, "awayRank": None, "startTimeTBD": False}


def test_to_json_safe():
    v = to_json_safe({"a": float("nan"), "b": [np.float64(0.123456), np.int64(3), float("inf")], "c": None})
    assert v == {"a": None, "b": [0.1235, 3, None], "c": None}
    assert type(v["b"][1]) is int and not any(isinstance(x, float) and math.isnan(x) for x in v["b"] if x is not None)


def test_title_game_sees_earlier_playoff_game(out):
    # Game 9 (later postseason date) must count game 8 (B vs C) in B's protection split; CFBD numbers all bowls week 1.
    m = _load(out / "2025" / "matchups" / "9.json")
    b_off = next(s for s in m["sections"] if s["offenseTeam"] == "B")
    prot = next(t for t in b_off["splits"] if t["tierSkill"] == "pass_rush")
    assert sum(r["games"] for r in prot["rows"]) == 3  # wk1 vs A, wk2 vs E, bowl vs C


def test_current_week_skips_stale_postponed_games():
    from cfbm.export import _current
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    games = [{"id": 1, "week": 4, "seasonType": "regular", "startDate": "2026-09-20T19:00:00.000Z", "completed": False},  # postponed
             {"id": 2, "week": 10, "seasonType": "regular", "startDate": "2026-11-07T19:00:00.000Z", "completed": True},
             {"id": 3, "week": 11, "seasonType": "regular", "startDate": "2026-11-14T19:00:00.000Z", "completed": False}]
    assert _current(games, now) == (11, "regular")


def test_current_week_keeps_game_awaiting_final_data():
    from cfbm.export import _current
    now = datetime(2026, 11, 9, 2, tzinfo=timezone.utc)  # Saturday night game not marked complete yet
    games = [{"id": 2, "week": 10, "seasonType": "regular", "startDate": "2026-11-08T02:30:00.000Z", "completed": False},
             {"id": 3, "week": 11, "seasonType": "regular", "startDate": "2026-11-14T19:00:00.000Z", "completed": False}]
    assert _current(games, now) == (10, "regular")


def test_teams_json(out):
    teams = _load(out / "2025" / "teams.json")
    assert sorted(t["school"] for t in teams) == FBS
    t = teams[0]
    assert set(t) == {"school", "id", "abbr", "conference", "fill", "textLight", "textDark", "barDark", "logo", "logoDark"}
    assert t["fill"] == "#002855" and t["logo"].endswith(".png")


def test_game_ranks(out):
    g7 = next(g for g in _load(out / "2025" / "games.json") if g["id"] == 7)
    assert g7["awayRank"] == 7 and g7["homeRank"] is None


def test_weather_and_venue(out):
    games = {g["id"]: g for g in _load(out / "2025" / "games.json")}
    assert games[7]["weather"]["status"] == "forecast" and games[7]["weather"]["label"] == "Clear"
    assert games[4]["weather"] is None
    m = _load(out / "2025" / "matchups" / "7.json")
    assert m["venue"]["city"] == "Town" and m["venue"]["grass"] is True


def test_section_edge_and_gap(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    sec = m["sections"][0]
    assert "edge" in sec and sec["biggestGap"] is not None
    g7 = next(g for g in _load(out / "2025" / "games.json") if g["id"] == 7)
    assert set(g7["gap"]) == {"key", "label", "favors"} and g7["gap"]["favors"] in ("A", "F")


def test_availability_block(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    assert set(m["availability"]) == {"A", "F"}
    a = m["availability"]["A"]
    assert isinstance(a["flags"], list) and a["report"] == {"conference": "Conf", "url": None, "when": None, "publishes": False}


def test_availability_watch_block(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    a = m["availability"]["A"]
    roles = [p["role"] for p in a["players"]]
    assert roles[:2] == ["QB", "QB2"] and roles.count("WR") == 3 and roles[-1] == "RB"
    assert a["players"][1]["name"] == "A Backup"
    b = a["backup"]
    assert b["name"] == "A Backup" and b["games"] == 0 and b["smallSample"] is True
    assert set(b["cells"]) >= {"epa_per_db", "sack_rate"}
    assert b["qbVs"]["opponent"] == "F" and b["qbVs"]["of"] is not None
    assert m["availability"]["F"]["backup"] is None


def test_swing_block_with_injected_model(tmp_path):
    from cfbm.swing_data import KEYS
    feat = {"coef": 0.5, "lo": 0.1, "hi": 0.9, "proven": True, "importance": 0.5, "volatility": 1.3,
            "mean": 0.0, "sd": 1.0, "sideMean": 0.0, "sideSd": 0.01}
    model = {"seasons": [2024], "games": 1000, "home": {"coef": 0.3, "lo": 0.1, "hi": 0.5},
             "features": {k: dict(feat) for k in KEYS}, "intercept": 0.0,
             "scale": {g: [i / 50 for i in range(101)] for g in ("overall",)}}
    build(WorldClient(), tmp_path, seasons=(2025,), career_start=2025, now=datetime(2025, 9, 20, tzinfo=timezone.utc),
          weather_fetch=_fake_weather, model=model)
    m = _load(tmp_path / "2025" / "matchups" / "7.json")
    sw = m["swing"]
    assert set(sw) == {"drivers", "storylines", "overallEdge", "note"}
    assert len(sw["drivers"]) <= 5 and all(d["cue"] for d in sw["drivers"])
    rows = [r for s in m["sections"] for u in s["units"] for r in u["rows"]]
    assert all(isinstance(r["isKey"], bool) for r in rows)
    games = _load(tmp_path / "2025" / "games.json")
    g7 = next(g for g in games if g["id"] == 7)
    assert g7["keyFactor"] is None or set(g7["keyFactor"]) == {"label", "favors"}
    # The model (coefficients, intercept, score quantiles) would let anyone turn an edge score back into
    # our own win %, so it never reaches the published data.
    assert not (tmp_path / "model.json").exists()


def test_no_model_means_no_swing(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    assert m["swing"] is None


def test_game_summary_exports_tbd_flag():
    from cfbm.export import game_summary
    g = {"id": 1, "season": 2026, "week": 1, "seasonType": "regular", "startDate": "2026-11-14T05:00:00.000Z",
         "homeTeam": "A", "awayTeam": "B", "startTimeTBD": True}
    assert game_summary(g, {"A", "B"})["startTimeTBD"] is True
    assert game_summary({**g, "startTimeTBD": None}, {"A", "B"})["startTimeTBD"] is False


def test_gotw_json(out):
    g = _load(out / "2025" / "gotw.json")
    assert isinstance(g, dict)
    for v in g.values():
        assert set(v) == {"id", "why"} and isinstance(v["id"], int)


def test_qb_vs_block(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    for sec in m["sections"]:
        qv = sec["qbVs"]
        if m["quarterbacks"][sec["offenseTeam"]] is None:
            assert qv is None
            continue
        assert set(qv) == {"name", "opponent", "oppRank", "of", "games"}
        assert qv["opponent"] == sec["defenseTeam"]
        assert all({"opponent", "oppRank", "result", "epaPerDb"} <= set(r) for r in qv["games"])


def test_run_units_in_both_sections(out):
    m = _load(out / "2025" / "matchups" / "7.json")
    for sec in m["sections"]:
        assert [u["title"] for u in sec["runUnits"]] == ["Run blocking vs. run defense front", "Running game vs. run defense"]
        assert "runEdge" in sec and "runBiggestGap" in sec
        assert all(u["title"] != "Run blocking vs. run defense front" for u in sec["units"])
    rows = [r for sec in m["sections"] for u in sec["runUnits"] for r in u["rows"]]
    assert any(r["offense"]["value"] is not None for r in rows)


def test_summary_gap_can_pick_a_run_row():
    from cfbm.export import summary_gap
    row = lambda key, o, d: {"key": key, "label": key, "offense": {"pct": o}, "defense": {"pct": d}}
    m = {"sections": [{"offenseTeam": "A", "defenseTeam": "B", "biggestGap": "epa_per_db", "runBiggestGap": "line_yards",
                       "units": [{"rows": [row("epa_per_db", 60, 50)]}],
                       "runUnits": [{"rows": [row("line_yards", 95, 10)]}]}]}
    assert summary_gap(m) == {"key": "line_yards", "label": "line_yards", "favors": "A"}


def test_home_chip_skips_short_yardage():
    from cfbm.export import summary_gap
    row = lambda key, o, d: {"key": key, "label": key, "offense": {"pct": o}, "defense": {"pct": d}}
    m = {"sections": [{"offenseTeam": "A", "defenseTeam": "B", "biggestGap": "epa_per_db", "runBiggestGap": "power_success",
                       "units": [{"rows": [row("epa_per_db", 60, 30)]}],
                       "runUnits": [{"rows": [row("power_success", 99, 1), row("line_yards", 50, 45)]}]}]}
    assert summary_gap(m)["key"] == "epa_per_db"


def test_matchup_carries_team_records(out):
    m = _load(out / "2025" / "matchups" / "7.json")  # F vs A, week 3
    assert set(m["records"]) == {"F", "A"}
    assert m["records"]["A"]["wins"] + m["records"]["A"]["losses"] == 2


BANNED = {"winprob", "probability", "prob", "logit", "linear", "predictedtotal", "spread", "margin"}


def _walk(x):
    """Yield (key, value, parent dict) for every key in a JSON tree."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield k, v, x
            yield from _walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from _walk(v)


class AdvClient(WorldClient):
    """WorldClient plus per-game advanced stats, so the edge score has pregame numbers to use."""

    def get(self, path, params, *, cacheable=True):
        if path == "/stats/game/advanced":
            out = []
            for g in self.games:
                if not g["completed"] or g["homeTeam"] not in FBS or g["awayTeam"] not in FBS:
                    continue
                for t, o in ((g["homeTeam"], g["awayTeam"]), (g["awayTeam"], g["homeTeam"])):
                    lvl = (ord(t[0]) - 65) / 10
                    side = lambda v: {"passingPlays": {"ppa": v, "successRate": v}, "passingDowns": {"successRate": v},
                                      "rushingPlays": {"ppa": v, "successRate": v}, "standardDowns": {"successRate": v},
                                      "explosiveness": v, "stuffRate": v, "lineYards": v,
                                      "ppa": v, "successRate": v, "drives": 10 + 4 * v}
                    out.append({"gameId": g["id"], "season": 2025, "week": g["week"], "seasonType": g["seasonType"],
                                "team": t, "opponent": o, "offense": side(lvl), "defense": side(0.5 - lvl)})
            return out
        return super().get(path, params, cacheable=cacheable)


SHOOT_HAND = {"means": {k: 0.0 for k in ("x_ppa", "x_sr", "x_expl", "x_pace", "home")},
              "sds": {k: 1.0 for k in ("x_ppa", "x_sr", "x_expl", "x_pace", "home")},
              "coef": {"x_ppa": 10.0, "x_sr": 0.0, "x_expl": 0.0, "x_pace": 1.0, "home": 1.0}, "intercept": 20.0}


def _model_build(tmp_path, client=None):
    from cfbm.swing_data import KEYS
    feat = {"coef": 0.5, "lo": 0.1, "hi": 0.9, "proven": True, "importance": 0.5, "volatility": 1.3,
            "mean": 0.0, "sd": 1.0, "sideMean": 0.0, "sideSd": 0.01}
    model = {"seasons": [2024], "games": 1000, "home": {"coef": 0.3, "lo": 0.1, "hi": 0.5},
             "features": {k: dict(feat) for k in KEYS}, "intercept": 0.0,
             "scale": {g: [i / 50 for i in range(101)] for g in ("overall",)}}
    build(client or WorldClient(), tmp_path, seasons=(2025,), career_start=2025,
          now=datetime(2025, 9, 20, tzinfo=timezone.utc), weather_fetch=_fake_weather, model=model,
          shootout_model=SHOOT_HAND)
    return tmp_path


def test_no_gambling_fields_exported(tmp_path, monkeypatch):
    import cfbm.export
    import cfbm.swing
    monkeypatch.setattr(cfbm.swing, "MIN_PRIOR", 1)
    out = _model_build(tmp_path, AdvClient())
    docs = [_load(f) for f in (out / "2025" / "matchups").glob("*.json")] + [_load(out / "2025" / "games.json")]
    scores = 0
    for doc in docs:
        for k, v, parent in _walk(doc):
            assert k.lower() not in BANNED, k
            edge_score = k == "score" and ("band" in parent or ("team" in parent and "edge" in parent))
            if edge_score and isinstance(v, (int, float)):
                assert 0 <= v <= 10
                scores += 1
    assert scores > 0


def test_section_edges_stay_table_based_with_model(tmp_path, monkeypatch):
    """Owner 2026-11-10: the passing/running lines keep matching their tables; the edge score
    drives only the overall meter and the home chip."""
    import cfbm.export
    import cfbm.swing
    from cfbm.units import side_edge
    monkeypatch.setattr(cfbm.swing, "MIN_PRIOR", 1)
    out = _model_build(tmp_path, AdvClient())
    scored = 0
    for f in (out / "2025" / "matchups").glob("*.json"):
        m = _load(f)
        scored += bool(m["swing"] and m["swing"]["overallEdge"])
        for sec in m["sections"]:
            assert sec["edge"] == side_edge([r for u in sec["units"] for r in u["rows"]])
            assert sec["runEdge"] == side_edge([r for u in sec["runUnits"] for r in u["rows"]])
            assert not {"edgeScore", "runEdgeScore", "rowEdge"} & set(sec)
    assert scored


def test_summary_edge_mirrors_overall(tmp_path):
    out = _model_build(tmp_path)
    games = {g["id"]: g for g in _load(out / "2025" / "games.json")}
    for f in (out / "2025" / "matchups").glob("*.json"):
        m = _load(f)
        o = m["swing"]["overallEdge"] if m["swing"] else None
        want = None if not o or o["edge"] == "even" else {"band": o["edge"], "team": o["team"], "score": o["score"]}
        assert games[m["game"]["id"]]["edge"] == want == m["game"]["edge"]


def test_shootout_exports_no_numbers(tmp_path, monkeypatch):
    """Shootout of the Week publishes a pick and a reason in words, never predicted points."""
    import re

    import cfbm.shootout
    import cfbm.swing
    monkeypatch.setattr(cfbm.swing, "MIN_PRIOR", 1)
    monkeypatch.setattr(cfbm.shootout, "MIN_PRIOR", 1)
    out = _model_build(tmp_path, AdvClient())
    picks = _load(out / "2025" / "shootout.json")
    assert picks
    gotw = _load(out / "2025" / "gotw.json")
    for wk, p in picks.items():
        assert set(p) == {"id", "why"}
        assert not re.search(r"\d+(\.\d+)?\s*points?\b", p["why"])
        assert p["id"] != (gotw.get(wk) or {}).get("id")
    games = _load(out / "2025" / "games.json")
    assert all(isinstance(g["shootoutWatch"], bool) for g in games)
    for g in games:
        assert not {k for k in g if k.lower() in {"total", "points", "predictedtotal", "predicted"}}
        assert not any(k.startswith("predicted") for k in g)


def test_shootout_file_empty_without_model(tmp_path):
    from cfbm.export import build
    build(WorldClient(), tmp_path, seasons=(2025,), career_start=2025,
          now=datetime(2025, 9, 20, tzinfo=timezone.utc), weather_fetch=_fake_weather, model={},
          shootout_model={})
    assert _load(tmp_path / "2025" / "shootout.json") == {}
    assert all(g["shootoutWatch"] is False for g in _load(tmp_path / "2025" / "games.json"))


def test_pulldowns_show_real_stats_while_model_reads_adjusted(tmp_path, monkeypatch):
    import cfbm.swing
    from cfbm import config
    monkeypatch.setattr(cfbm.swing, "MIN_PRIOR", 1)

    def run(w, sub):
        monkeypatch.setattr(config, "OPP_ADJUST", w)
        out = _model_build(tmp_path / sub, AdvClient())
        ms = {}
        for f in (out / "2025" / "matchups").glob("*.json"):
            m = _load(f)
            ms[m["game"]["id"]] = m["swing"]
        return ms

    raw, adj = run(0.0, "raw"), run(0.8, "adj")
    shown_raw = {(gid, d["key"], d["offense"]): d["detail"]["offValue"]
                 for gid, sw in raw.items() if sw for d in sw["drivers"]}
    shown_adj = {(gid, d["key"], d["offense"]): d["detail"]["offValue"]
                 for gid, sw in adj.items() if sw for d in sw["drivers"]}
    common = set(shown_raw) & set(shown_adj)
    assert common and all(shown_raw[k] == shown_adj[k] for k in common)
    scores = lambda ms: {g: (sw.get("overallEdge") or {}).get("score") for g, sw in ms.items() if sw}  # noqa: E731
    assert scores(raw) != scores(adj)


class LinesClient(AdvClient):
    """AdvClient plus betting lines: DraftKings on every FBS game except the first, which has Bovada only."""

    def get(self, path, params, *, cacheable=True):
        if path == "/lines":
            out, first = [], True
            for g in self.games:
                if g["homeTeam"] not in FBS or g["awayTeam"] not in FBS:
                    continue
                if first:
                    first = False
                    self.bovada_only = g["id"]
                    ls = [{"provider": "Bovada", "spread": 20, "homeMoneyline": 900, "awayMoneyline": -2000}]
                else:
                    h, a = (250, -300) if g["id"] % 2 == 0 else (-300, 250)
                    ls = [{"provider": "DraftKings", "spread": 7 if h > 0 else -7, "homeMoneyline": h, "awayMoneyline": a}]
                out.append({"id": g["id"], "homeTeam": g["homeTeam"], "awayTeam": g["awayTeam"], "lines": ls})
            return out
        return super().get(path, params, cacheable=cacheable)


def test_upset_exports_only_draftkings_odds(tmp_path, monkeypatch):
    import cfbm.swing
    monkeypatch.setattr(cfbm.swing, "MIN_PRIOR", 1)
    client = LinesClient()
    out = _model_build(tmp_path, client)
    picks = _load(out / "2025" / "upset.json")
    assert picks
    gotw, shoot = _load(out / "2025" / "gotw.json"), _load(out / "2025" / "shootout.json")
    for wk, p in picks.items():
        assert set(p) == {"id", "why", "odds"}
        assert set(p["odds"]) == {"source", "home", "away"} and p["odds"]["source"] == "DraftKings"
        assert p["odds"]["home"] + p["odds"]["away"] == 100
        assert "%" not in p["why"]
        assert p["id"] not in {(gotw.get(wk) or {}).get("id"), (shoot.get(wk) or {}).get("id")}
        assert p["id"] != client.bovada_only
    docs = [_load(f) for f in (out / "2025" / "matchups").glob("*.json")] + [_load(out / "2025" / "games.json")]
    for doc in docs:
        for k, _, _ in _walk(doc):
            assert not any(bad in k.lower() for bad in ("prob", "moneyline", "spread", "odds")), k


def test_upset_file_empty_without_lines(tmp_path):
    out = _model_build(tmp_path)
    assert _load(out / "2025" / "upset.json") == {}
