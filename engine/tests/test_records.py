from cfbm.records import record


def g(i, home, away, hp, ap, conf=False, done=True, conference="SEC"):
    return {"id": i, "homeTeam": home, "awayTeam": away, "homePoints": hp, "awayPoints": ap, "completed": done,
            "conferenceGame": conf, "homeConference": conference, "awayConference": conference}


GAMES = [g(1, "Georgia", "Clemson", 30, 20), g(2, "Alabama", "Georgia", 24, 21, conf=True),
         g(3, "Georgia", "Tennessee", 28, 10, conf=True), g(4, "Georgia", "Auburn", None, None, done=False),
         g(5, "Georgia", "Ole Miss", 35, 3, conf=True)]
ORDERS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}


def test_record_counts_only_games_before_this_one():
    r = record(GAMES, "Georgia", before_order=5, orders=ORDERS)
    assert r == {"wins": 2, "losses": 1, "confWins": 1, "confLosses": 1, "conference": "SEC"}


def test_first_game_is_zero_and_zero():
    assert record(GAMES, "Georgia", before_order=1, orders=ORDERS)["wins"] == 0


def test_independents_have_no_conference_record():
    games = [g(1, "Notre Dame", "Navy", 30, 20, conference="FBS Independents")]
    r = record(games, "Notre Dame", before_order=9, orders={1: 1})
    assert r["conference"] is None and r["confWins"] == 0 and r["wins"] == 1
