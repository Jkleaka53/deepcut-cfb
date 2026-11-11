import math

import pandas as pd
import pytest

from cfbm.swing_data import adjusted_priors, pregame, pregame_adjusted

COLS = ["off_x", "def_x"]


def _tg(rows):
    return pd.DataFrame([{"game_id": g, "season": 2024, "order": o, "team": t, "opponent": op, "off_x": ox, "def_x": dx}
                         for g, o, t, op, ox, dx in rows])


# Week 1: A beats up WEAK (whose defense allows 0.6), B faces TOUGH (allows 0.0). Week 2: WEAK and TOUGH play others.
ROWS = [
    (1, 1, "A", "WEAK", 0.5, 0.2), (1, 1, "WEAK", "A", 0.2, 0.6),
    (2, 1, "B", "TOUGH", 0.5, 0.2), (2, 1, "TOUGH", "B", 0.2, 0.0),
    (3, 2, "WEAK", "C", 0.1, 0.6), (3, 2, "C", "WEAK", 0.6, 0.1),
    (4, 2, "TOUGH", "D", 0.1, 0.0), (4, 2, "D", "TOUGH", 0.0, 0.1),
]


def test_w0_matches_raw_means():
    tg = _tg(ROWS)
    adj = pregame_adjusted(tg, 2024, 3, COLS, w=0.0)
    raw = pregame(tg, 2024, 3, COLS)
    pd.testing.assert_frame_equal(adj.sort_index()[["games"] + COLS], raw.sort_index()[["games"] + COLS],
                                  check_dtype=False)


def test_weak_schedule_counts_for_less():
    adj = pregame_adjusted(_tg(ROWS), 2024, 3, COLS, w=1.0)
    assert adj.loc["A", "off_x"] < adj.loc["B", "off_x"]
    assert adj.loc["A", "games"] == 1


def test_priors_use_only_earlier_games():
    base = adjusted_priors(_tg(ROWS), COLS, w=1.0).set_index(["game_id", "team"])
    later = [r if r[0] != 3 else (r[0], r[1], r[2], r[3], 9.9, 9.9) for r in ROWS]
    changed = adjusted_priors(_tg(later), COLS, w=1.0).set_index(["game_id", "team"])
    # week-1 rows have no priors; the week-2 prior for TOUGH/D doesn't involve game 3's numbers at all
    assert base.loc[(4, "TOUGH"), "off_x"] == pytest.approx(changed.loc[(4, "TOUGH"), "off_x"])
    assert base.loc[(1, "A"), "prior_games"] == 0 and math.isnan(base.loc[(1, "A"), "off_x"])


def test_training_and_build_agree():
    tg = _tg(ROWS)
    pri = adjusted_priors(tg, COLS, w=0.8).set_index(["game_id", "team"])
    pre = pregame_adjusted(tg, 2024, 2, COLS, w=0.8)
    for t in ("WEAK", "TOUGH", "C", "D"):
        gid = {"WEAK": 3, "C": 3, "TOUGH": 4, "D": 4}[t]
        if t in pre.index:
            assert pri.loc[(gid, t), "off_x"] == pytest.approx(pre.loc[t, "off_x"])
            assert pri.loc[(gid, t), "prior_games"] == pre.loc[t, "games"]
