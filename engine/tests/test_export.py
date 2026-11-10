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
        wk = [g for g in self.games if g["seasonType"] == params["seasonType"] and g["week"] == params["week"]
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
             "features": {k: dict(feat) for k in KEYS}}
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
    assert _load(tmp_path / "model.json")["games"] == 1000


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
