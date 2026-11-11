import pandas as pd
import pytest

from cfbm.upset_backtest import covered, summary, weekly_picks


def test_cover_definition():
    # home underdog getting 7 (spread +7)
    assert covered("home", 7, -3) and not covered("home", 7, -10) and covered("home", 7, 3)
    # away underdog, home favored by 7 (spread -7); margins are home minus away
    assert covered("away", -7, 3) and not covered("away", -7, 10) and covered("away", -7, -3)
    assert not covered("home", 7, -7)  # a push is not a cover


def _row(season, wk, gid, our, book, spread, margin):
    return {"season": season, "week_key": wk, "game_id": gid, "our_home": our, "book_home": book,
            "spread": spread, "home_margin": margin}


def test_weekly_picks_biggest_gap():
    df = pd.DataFrame([
        _row(2019, "3", 1, 0.40, 0.52, -1, 7),    # no underdog at or under 0.45
        _row(2019, "3", 2, 0.45, 0.30, 7, 3),     # home dog: ours 0.45 vs book 0.30 -> gap 0.15, won outright
        _row(2019, "3", 3, 0.25, 0.30, 7, -10),   # we like the favorite more -> no
        _row(2019, "4", 4, 0.50, 0.53, -2, 1),    # no underdog at or under 0.45
    ])
    picks = weekly_picks(df)
    assert list(picks["game_id"]) == [2]
    r = picks.iloc[0]
    assert r["dog_won"] == 1 and r["dog_covered"] == 1 and r["book_dog"] == pytest.approx(0.30)


def test_summary_rates():
    picks = pd.DataFrame({"dog_covered": [1, 1, 0, 1], "dog_won": [1, 0, 0, 0], "book_dog": [0.3] * 4})
    assert summary(picks) == {"weeks": 4, "coverRate": 0.75, "upsetRate": 0.25, "bookUpsetRate": 0.3}


def test_held_out_keeps_old_columns():
    from tests.test_edge_backtest import _multi
    from cfbm.edge_backtest import held_out
    fr, tg = _multi()
    out = held_out(fr, tg, keys=["a", "b"])
    assert {"season", "score", "favored_won", "game_id", "lin"} <= set(out.columns)
    assert list(out["game_id"]) == list(fr.sort_values("season", kind="stable")["game_id"])
