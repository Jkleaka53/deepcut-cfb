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


from cfbm.upset import odds_block, pick, why_text  # noqa: E402


def test_odds_block_sums_to_100():
    assert odds_block(0.567) == {"source": "DraftKings", "home": 57, "away": 43}
    assert odds_block(0.995) == {"source": "DraftKings", "home": 99, "away": 1}


def _g(gid, week=11):
    return {"id": gid, "week": week, "seasonType": "regular"}


def test_pick_skips_gotw_and_shootout():
    cands = [(_g(1), 0.30, {"why": "a", "odds": {}}), (_g(2), 0.25, {"why": "b", "odds": {}}),
             (_g(3), 0.20, {"why": "c", "odds": {}})]
    out = pick(cands, {"11": {1, 2}})
    assert out == {"11": {"id": 3, "why": "c", "odds": {}}}
    assert pick([], {}) == {}


def _m(drivers, edge):
    return {"swing": {"drivers": drivers, "overallEdge": edge}}


EXPL = {"key": "explosive", "label": "Big plays", "offense": "Iowa State", "defense": "Kansas State",
        "favors": "Iowa State", "offRank": 9, "defRank": 101, "of": 134}


def test_why_text_with_driver():
    m = _m([{**EXPL, "favors": "Kansas State", "key": "sd_sr", "label": "Early-down success",
             "offense": "Kansas State", "defense": "Iowa State"}, EXPL],
           {"edge": "slight", "team": "Kansas State", "score": 3.1})
    assert why_text(m, "Iowa State", "Kansas State") == (
        "Iowa State has the edge in Big plays: Iowa State's offense ranks 9th against Kansas State's defense, "
        "which ranks 101st of 134.")


def test_why_text_never_quotes_an_edge_score_that_favors_the_favorite():
    """Owner 2026-11-10: the upset model makes the upset call; the edge score (a different model) is only
    quoted when it is even or leans the underdog, whatever its size."""
    for edge in ({"edge": "slight", "team": "Kansas State", "score": 3.1}, {"edge": "clear", "team": "Kansas State", "score": 9.0}):
        text = why_text(_m([EXPL], edge), "Iowa State", "Kansas State")
        assert "edge score" not in text and text.startswith("Iowa State has the edge in Big plays")


def test_why_text_defense_driver_and_dog_lean():
    d = {**EXPL, "offense": "Kansas State", "defense": "Iowa State", "offRank": 120, "defRank": 12}
    m = _m([d], {"edge": "slight", "team": "Iowa State", "score": 2.4})
    assert why_text(m, "Iowa State", "Kansas State") == (
        "Iowa State has the edge in Big plays: Iowa State's defense ranks 12th against Kansas State's offense, "
        "which ranks 120th of 134. Our edge score leans Iowa State, 2.4 of 10.")


def test_why_text_without_driver():
    m = _m([{**EXPL, "favors": "Kansas State"}], {"edge": "even", "team": None, "score": 1.2})
    assert why_text(m, "Iowa State", "Kansas State") == "Our edge score has it even."


def test_why_text_no_bad_articles():
    """Review: 'against a Iowa offense' was published. Name the team's unit without an article."""
    d = {**EXPL, "offense": "Iowa State", "defense": "Iowa"}
    m = _m([d], {"edge": "even", "team": None, "score": 1.0})
    assert why_text(m, "Iowa State", "Iowa") == (
        "Iowa State has the edge in Big plays: Iowa State's offense ranks 9th against Iowa's defense, "
        "which ranks 101st of 134. Our edge score has it even.")


def test_zero_moneyline_is_missing():
    g = {"lines": [{"provider": "DraftKings", "homeMoneyline": 0, "awayMoneyline": 0}]}
    assert book_prob(g) is None
    g = {"lines": [{"provider": "DraftKings", "homeMoneyline": 0, "awayMoneyline": -150}]}
    assert book_prob(g) is None


def test_reason_must_back_the_underdog():
    """No driver for the dog and our edge score on the favorite: the note would argue for the favorite."""
    from cfbm.upset import backs_dog
    fav_only = _m([{**EXPL, "favors": "Kansas State"}], {"edge": "slight", "team": "Kansas State", "score": 2.5})
    assert not backs_dog(fav_only, "Iowa State")
    assert backs_dog(_m([], {"edge": "even", "team": None, "score": 1.0}), "Iowa State")
    assert backs_dog(_m([EXPL], {"edge": "slight", "team": "Kansas State", "score": 2.5}), "Iowa State")
