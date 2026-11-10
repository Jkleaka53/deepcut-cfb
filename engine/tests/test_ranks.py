from cfbm.ranks import ap_poll_for


def _entry(st, week, ap, coaches=None):
    polls = [{"poll": "AP Top 25", "ranks": [{"rank": r, "school": s} for s, r in ap.items()]}]
    if coaches:
        polls.append({"poll": "Coaches Poll", "ranks": [{"rank": r, "school": s} for s, r in coaches.items()]})
    return {"season": 2026, "seasonType": st, "week": week, "polls": polls}


R = [
    _entry("regular", 1, {"Georgia": 3}, {"Michigan": 9}),
    _entry("regular", 11, {"Oregon": 18, "Georgia": 1}, {"Michigan": 25}),
    _entry("postseason", 1, {"Oregon": 2}),
]


def test_week_uses_its_own_poll():
    assert ap_poll_for(R, "regular", 11)["Oregon"] == 18


def test_later_week_uses_latest_earlier_poll():
    assert ap_poll_for(R, "regular", 12) == {"Oregon": 18, "Georgia": 1}


def test_week_one_uses_preseason_poll():
    assert ap_poll_for(R, "regular", 1) == {"Georgia": 3}


def test_postseason_uses_last_regular_poll_not_final():
    assert ap_poll_for(R, "postseason", 1)["Oregon"] == 18


def test_coaches_poll_never_leaks():
    assert "Michigan" not in ap_poll_for(R, "regular", 11)


def test_empty_rankings():
    assert ap_poll_for([], "regular", 5) == {}
