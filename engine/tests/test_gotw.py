from cfbm.gotw import pick, score, why


def _sec(off, dfn, off_pct, def_pct, edge):
    rows = [{"key": f"k{i}", "offense": {"pct": o}, "defense": {"pct": d}} for i, (o, d) in enumerate(zip(off_pct, def_pct))]
    return {"offenseTeam": off, "defenseTeam": dfn, "edge": edge, "units": [{"rows": rows}]}


def _m(gid, away, home, a, b, week=11, st="regular"):
    return {"game": {"id": gid, "week": week, "seasonType": st, "away": away, "home": home}, "sections": [a, b]}


STRONG_EVEN = _m(1, "Michigan", "Oregon", _sec("Michigan", "Oregon", [80, 82], [78, 84], "even"),
                 _sec("Oregon", "Michigan", [85, 79], [83, 80], "even"))
STRONG_LOPSIDED = _m(2, "A", "B", _sec("A", "B", [95, 95], [40, 40], "clear-offense"),
                     _sec("B", "A", [90, 90], [40, 40], "clear-offense"))
WEAK_EVEN = _m(3, "C", "D", _sec("C", "D", [30, 30], [30, 30], "even"), _sec("D", "C", [25, 25], [25, 25], "even"))


def test_strength_and_closeness_both_count():
    assert score(STRONG_EVEN) > score(STRONG_LOPSIDED)
    assert score(STRONG_EVEN) > score(WEAK_EVEN)


def test_missing_pct_means_no_score():
    m = _m(4, "E", "F", _sec("E", "F", [None], [None], None), _sec("F", "E", [None], [None], None))
    assert score(m) is None
    assert score({"game": {"id": 5}, "sections": []}) is None


def test_pick_per_week():
    picks = pick([STRONG_LOPSIDED, WEAK_EVEN, STRONG_EVEN, _m(9, "G", "H", *STRONG_EVEN["sections"], st="postseason", week=1)])
    assert set(picks) == {"11", "post"}
    assert picks["11"]["id"] == 1 and picks["post"]["id"] == 9
    assert picks["11"]["why"]


def test_why_is_plain_and_never_a_prediction():
    w = why(STRONG_EVEN)
    assert w == "Both passing games and both pass defenses rank in the top third of FBS. Neither side has a clear edge on paper."
    w2 = why(STRONG_LOPSIDED)
    assert "A's passing game has the edge when A passes" not in w2
    assert "A's passing game has the edge over B's defense" in w2
    for text in (w, w2, why(WEAK_EVEN)):
        low = text.lower()
        assert not any(bad in low for bad in ("win", "lock", "odds", "50/50", "injur", "favorite"))


def test_ranked_games_preferred_when_any_exist():
    ranked = _m(6, "Missouri", "Georgia", *STRONG_LOPSIDED["sections"])
    ranked["game"]["homeRank"] = 1
    assert pick([STRONG_EVEN, ranked])["11"]["id"] == 6
    assert pick([STRONG_EVEN, WEAK_EVEN])["11"]["id"] == 1


def test_swing_factors_show_in_the_why():
    import copy
    a = copy.deepcopy(STRONG_EVEN)
    b = copy.deepcopy(STRONG_EVEN)
    a["swing"] = {"drivers": [{"label": "Big plays"}] * 4}
    b["swing"] = {"drivers": []}
    assert "4 swing factors" in why(a)
    assert "swing factor" not in why(b)


def _with(m, gid, edge_score=None, run=None, away_rank=None, home_rank=None):
    import copy
    out = copy.deepcopy(m)
    out["game"]["id"] = gid
    out["game"]["awayRank"], out["game"]["homeRank"] = away_rank, home_rank
    if edge_score is not None:
        out["swing"] = {"drivers": [], "overallEdge": {"edge": "slight", "team": "x", "score": edge_score}}
    if run is not None:
        for sec in out["sections"]:
            sec["runUnits"] = [{"rows": [{"key": "r", "offense": {"pct": run}, "defense": {"pct": run}}]}]
    return out


def test_running_game_counts():
    """Owner 2026-11-10: Game of the Week looks at the running game too, not just passing."""
    assert score(_with(STRONG_EVEN, 1, edge_score=1.0, run=90)) > score(_with(STRONG_EVEN, 2, edge_score=1.0, run=20))


def test_edge_score_sets_closeness():
    """A near-even edge score beats a near-Big one between equally strong teams."""
    assert score(_with(STRONG_EVEN, 1, edge_score=0.2)) > score(_with(STRONG_EVEN, 2, edge_score=7.9))


def test_both_ranked_beats_one_ranked():
    """Unranked Missouri at #1 Georgia must not win just because Georgia is ranked."""
    one = _with(STRONG_EVEN, 6, edge_score=7.9, home_rank=1)
    both = _with(WEAK_EVEN, 7, edge_score=0.2, away_rank=2, home_rank=22)
    assert pick([one, both])["11"]["id"] == 7


def test_no_edge_score_falls_back_to_passing_gaps():
    assert score(STRONG_EVEN) is not None and score(STRONG_EVEN) > score(STRONG_LOPSIDED)
