import pandas as pd

from cfbm.availability import qb_flags
from cfbm.qb import COLUMNS


def _p(gid, order, aid, name, primary=True, team="T", season=2026):
    return {"game_id": gid, "season": season, "season_type": "regular", "week": order, "order": order, "team": team,
            "athlete_id": aid, "name": name, "attempts": 30 if primary else 2, "team_attempts": 32,
            "share": 0.9 if primary else 0.06, "is_primary": primary}


def _f(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def test_no_games_no_claims():
    assert qb_flags(_f([]), "T", 2026, 5) == []


def test_same_starter_ok():
    df = _f([_p(1, 1, 10, "Carr"), _p(2, 2, 10, "Carr")])
    assert qb_flags(df, "T", 2026, 3) == [{"kind": "ok", "text": "Carr started last game."}]


def test_qb_change_warns():
    df = _f([_p(1, 1, 10, "Carr"), _p(2, 2, 10, "Carr"), _p(3, 3, 11, "Smith")])
    flags = qb_flags(df, "T", 2026, 4)
    assert {"kind": "warn", "text": "QB change: Smith started last game after Carr the game before."} in flags
    assert {"kind": "warn", "text": "Carr did not play last game."} in flags


def test_leader_who_played_but_did_not_start_is_not_flagged_absent():
    df = _f([_p(1, 1, 10, "Carr"), _p(2, 2, 10, "Carr"), _p(3, 3, 11, "Smith"), _p(3, 3, 10, "Carr", primary=False)])
    flags = qb_flags(df, "T", 2026, 4)
    assert not any("did not play" in f["text"] for f in flags)


def test_only_games_before_order_and_season_count():
    df = _f([_p(1, 1, 10, "Carr"), _p(2, 2, 11, "Smith"), _p(9, 1, 12, "Old", season=2025)])
    assert qb_flags(df, "T", 2026, 2) == [{"kind": "ok", "text": "Carr started last game."}]


def test_never_says_injury():
    df = _f([_p(1, 1, 10, "Carr"), _p(2, 2, 11, "Smith")])
    assert all("injur" not in f["text"].lower() for f in qb_flags(df, "T", 2026, 3))


def test_report_for_known_conference_without_link():
    from cfbm.availability import report_for
    b = report_for("Big Ten")
    assert b["url"] is None and b["publishes"] is True and b["when"]
    assert report_for("SEC")["publishes"] is True and report_for("SEC")["url"]
    assert report_for("Mountain West") == {"conference": "Mountain West", "url": None, "when": None, "publishes": False}
