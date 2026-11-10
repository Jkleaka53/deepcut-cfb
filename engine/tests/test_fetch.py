from cfbm import fetch


class FakeClient:
    def __init__(self, responses):
        self.responses = responses  # path -> callable(params) or value
        self.calls = []

    def get(self, path, params, *, cacheable=True):
        self.calls.append((path, dict(params), cacheable))
        r = self.responses.get(path, [])
        return r(params) if callable(r) else r


def _g(i, week, completed=True, st="regular"):
    return {"id": i, "week": week, "seasonType": st, "completed": completed}


def test_games_merges_regular_and_postseason():
    c = FakeClient({"/games": lambda p: [_g(1, 1)] if p["seasonType"] == "regular" else [_g(2, 1, st="postseason")]})
    out = fetch.games(c, 2025, live=False)
    assert [g["id"] for g in out] == [1, 2]
    assert all(call[2] is True for call in c.calls)


def test_live_games_never_cached():
    c = FakeClient({"/games": []})
    fetch.games(c, 2026, live=True)
    assert all(call[2] is False for call in c.calls)


def test_completed_week_uses_cache_flag():
    c = FakeClient({"/plays": [{"id": "1"}]})
    gl = [_g(1, 5), _g(2, 5)]
    fetch.plays(c, 2025, "regular", 5, gl)
    assert c.calls[-1] == ("/plays", {"year": 2025, "week": 5, "seasonType": "regular"}, True)


def test_incomplete_week_refetches():
    c = FakeClient({"/plays": []})
    gl = [_g(1, 5), _g(2, 5, completed=False)]
    fetch.plays(c, 2026, "regular", 5, gl)
    assert c.calls[-1][2] is False


def test_postseason_week_completeness_is_separate_from_regular():
    c = FakeClient({"/games/players": []})
    gl = [_g(1, 1, completed=False), _g(2, 1, st="postseason")]
    fetch.player_box(c, 2025, "postseason", 1, gl)
    assert c.calls[-1][1]["category"] == "passing" and c.calls[-1][2] is True


def test_fbs_teams_returns_school_names():
    c = FakeClient({"/teams/fbs": [{"school": "West Virginia"}, {"school": "Texas Tech"}]})
    assert fetch.fbs_teams(c, 2025) == {"West Virginia", "Texas Tech"}


def test_front7_havoc_map():
    raw = [{"team": "Texas Tech", "defense": {"havoc": {"frontSeven": 0.09}}},
           {"team": "Nowhere", "defense": {"havoc": None}}]
    assert fetch.front7_havoc(raw) == {"Texas Tech": 0.09}
