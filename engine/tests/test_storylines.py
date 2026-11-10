from cfbm.storylines import game_facts, miles, storylines

EAST = {"latitude": 42.27, "longitude": -83.75, "timezone": "America/Detroit", "capacity": 107601}
WEST = {"latitude": 44.06, "longitude": -123.07, "timezone": "America/Los_Angeles", "capacity": 54000}
GAMES = {
    1: {"id": 1, "homeTeam": "Michigan", "awayTeam": "X", "homePoints": 30, "awayPoints": 10, "neutralSite": False,
        "startDate": "2025-09-06T23:30:00.000Z", "startTimeTBD": False, "venueId": 10},
    2: {"id": 2, "homeTeam": "Y", "awayTeam": "Michigan", "homePoints": 31, "awayPoints": 20, "neutralSite": False,
        "startDate": "2025-09-13T16:00:00.000Z", "startTimeTBD": False, "venueId": 30},
    3: {"id": 3, "homeTeam": "Z", "awayTeam": "Michigan", "homePoints": 7, "awayPoints": 27, "neutralSite": False,
        "startDate": "2025-09-27T23:00:00.000Z", "startTimeTBD": False, "venueId": 10},
    4: {"id": 4, "homeTeam": "W", "awayTeam": "Michigan", "homePoints": 24, "awayPoints": 21, "neutralSite": True,
        "startDate": "2025-10-04T19:00:00.000Z", "startTimeTBD": False, "venueId": 20},
}
VENUES = {10: EAST, 20: WEST, 30: {**WEST, "capacity": 102000}}


def test_game_facts_site_result_night_capacity():
    f = {x["gameId"]: x for x in game_facts([1, 2, 3, 4], "Michigan", GAMES, VENUES)}
    assert f[1]["site"] == "home" and f[1]["result"] == "W" and f[1]["night"] is True  # 7:30 PM Detroit
    assert f[2]["site"] == "road" and f[2]["result"] == "L" and f[2]["night"] is False
    assert f[4]["site"] == "neutral" and f[3]["capacity"] == 107601


def test_miles():
    assert 1900 < miles(EAST, WEST) < 2000
    assert miles(EAST, {"latitude": None, "longitude": None}) is None


def _game(neutral=False, start="2026-11-14T00:30:00.000Z", tbd=False):
    return {"id": 99, "homeTeam": "Oregon", "awayTeam": "Michigan", "neutralSite": neutral, "startDate": start,
            "startTimeTBD": tbd, "venueId": 20}


def _story(**kw):
    facts = {"Michigan": game_facts([1, 2, 3, 4], "Michigan", GAMES, VENUES), "Oregon": []}
    args = dict(qbs={"Michigan": (1, "Tommy Carr"), "Oregon": None}, facts=facts,
                team_loc={"Michigan": EAST, "Oregon": WEST}, venue=WEST,
                prev_start={"Michigan": "2026-10-31T19:00:00.000Z", "Oregon": "2026-11-08T19:00:00.000Z"})
    args.update(kw)
    return storylines(_game(**{k: v for k, v in kw.items() if k in ("neutral", "start", "tbd")}),
                      **{k: v for k, v in args.items() if k not in ("neutral", "start", "tbd")})


def test_road_record_travel_bye_short_week():
    texts = [s["text"] for s in _story()]
    assert "Tommy Carr is 1-1 on the road as a starter." in texts
    assert any(t.startswith("Michigan travels about 1,9") and t.endswith("miles for this one.") for t in texts)
    assert "Michigan is coming off a bye (13 days of rest)." in texts
    assert "Oregon is on a short week (5 days of rest)." in texts
    assert all(s["kind"] == "storyline" and s["sample"] for s in _story())


def test_neutral_skips_home_road_and_travel_uses_neutral_site():
    texts = [s["text"] for s in _story(neutral=True)]
    assert not any("on the road" in t for t in texts)


def test_night_only_when_this_game_is_at_night():
    night = [s["text"] for s in _story()]  # 4:30 PM Pacific, not night
    assert not any("night" in t for t in night)
    texts = [s["text"] for s in _story(start="2026-11-15T03:30:00.000Z")]  # 7:30 PM Pacific
    assert "Tommy Carr is 2-0 in night games as a starter." in texts


def test_missing_coords_skip_travel_only():
    texts = [s["text"] for s in _story(venue={"latitude": None, "longitude": None, "timezone": None, "capacity": None})]
    assert not any("travels" in t for t in texts)
    assert "Tommy Carr is 1-1 on the road as a starter." in texts


def test_big_stadium_record_needs_two_games():
    big = {**WEST, "capacity": 100000}
    texts = [s["text"] for s in _story(venue=big)]
    # road and neutral games only: game 2 (L, 102k) and game 3 (W, 107k); his own home games don't count
    assert "Tommy Carr is 1-1 in road stadiums of 80,000 or more." in texts
