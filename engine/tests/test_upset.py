import numpy as np
import pytest

from cfbm.upset import book_prob, fit_spread_scale, spread_of, spread_prob


def _lines(*ls):
    return {"lines": list(ls)}


def test_book_prob_removes_margin():
    g = _lines({"provider": "Bovada", "homeMoneyline": -130, "awayMoneyline": 110},
               {"provider": "DraftKings", "homeMoneyline": -142, "awayMoneyline": 120})
    assert round(book_prob(g), 3) == 0.563  # 0.5868 / (0.5868 + 0.4545)


def test_book_prob_needs_draftkings():
    assert book_prob(_lines({"provider": "Bovada", "homeMoneyline": -130, "awayMoneyline": 110})) is None
    assert book_prob(_lines({"provider": "DraftKings", "homeMoneyline": None, "awayMoneyline": 120})) is None
    assert book_prob({"lines": None}) is None


def test_spread_of_prefers_consensus():
    both = _lines({"provider": "teamrankings", "spread": -3}, {"provider": "consensus", "spread": -4.5})
    assert spread_of(both) == -4.5
    assert spread_of(_lines({"provider": "teamrankings", "spread": None}, {"provider": "Bovada", "spread": -3})) == -3
    assert spread_of(_lines({"provider": "Bovada", "spread": None})) is None


def test_spread_prob_direction():
    assert spread_prob(-7, 15) > 0.5 > spread_prob(7, 15)
    assert spread_prob(0, 15) == 0.5


def test_fit_spread_scale_recovers_k():
    rng = np.random.default_rng(5)
    spreads = rng.uniform(-30, 30, 20000)
    wins = (rng.uniform(size=spreads.size) < 1 / (1 + np.exp(spreads / 14))).astype(int)
    assert abs(fit_spread_scale(spreads, wins) - 14) < 1


from cfbm.upset import gap, our_prob  # noqa: E402


def test_gap_picks_book_underdog():
    side, g = gap(0.48, 0.30)
    assert side == "home" and g == pytest.approx(0.18)
    side, g = gap(0.40, 0.75)
    assert side == "away" and g == pytest.approx(0.35)  # ours 0.60 vs book 0.25


def test_no_pick_without_disagreement():
    assert gap(0.20, 0.30) is None


def test_close_odds_not_an_upset():
    assert gap(0.60, 0.47) is None


def test_neutral_site_no_home_tilt():
    from tests.test_edge_score import model, pre
    m = model({})
    p = pre(Home={}, Away={})
    assert our_prob(m, p, "Home", "Away", neutral=True) == pytest.approx(0.5)
    assert our_prob(m, p, "Home", "Away", neutral=False) > 0.5
    assert our_prob(m, p, "Nobody", "Away", neutral=False) is None
