import math

import pandas as pd
import pytest

from cfbm.edge_model import EDGE_KEYS, features, margin_before, shrunk_pregame, team_margins
from cfbm.swing_data import KEYS, stat_cols

FBS = {2024: {"A", "B", "C", "H"}}


def _game(gid, home, away, hp, ap, week, season=2024, st="regular"):
    return {"id": gid, "season": season, "week": week, "seasonType": st, "homeTeam": home, "awayTeam": away,
            "homePoints": hp, "awayPoints": ap}


def test_margin_is_capped_and_only_counts_earlier_games():
    games = [_game(1, "A", "B", 45, 3, week=1), _game(2, "A", "C", 10, 20, week=2)]
    tm = team_margins(games, FBS, {1: 1, 2: 2})
    assert margin_before(tm, 2024, 2).loc["A", "margin"] == 28      # 42 capped
    assert margin_before(tm, 2024, 3).loc["A", "margin"] == 9       # (28 - 10) / 2
    assert margin_before(tm, 2024, 3).loc["B", "margin"] == -28
    assert "A" not in margin_before(tm, 2024, 1).index              # nothing before week 1


def test_margin_skips_non_fbs_opponents_and_unplayed_games():
    games = [_game(1, "A", "FCS U", 60, 0, week=1), _game(2, "A", "B", None, None, week=2)]
    assert team_margins(games, FBS, {1: 1, 2: 2}).empty


def test_bowl_game_does_not_see_its_own_margin():
    games = [_game(i, "A", "B", 20, 10, week=i) for i in range(1, 13)]
    games += [_game(101, "A", "C", 50, 0, week=1, st="postseason"), _game(102, "A", "B", 0, 50, week=1, st="postseason")]
    orders = {**{i: i for i in range(1, 13)}, 101: 101, 102: 102}
    tm = team_margins(games, FBS, orders)
    first = margin_before(tm, 2024, 101)
    assert first.loc["A", "games"] == 12 and first.loc["A", "margin"] == 10
    assert margin_before(tm, 2024, 102).loc["A", "games"] == 13


def _pre(rows):
    """rows: team -> (games, value); every stat column gets the same value."""
    df = pd.DataFrame({t: {"games": n, **{c: v for c in stat_cols()}} for t, (n, v) in rows.items()}).T
    df.index.name = "team"
    return df


def _margin(rows):
    return pd.DataFrame({t: {"games": n, "margin": v} for t, (n, v) in rows.items()}).T


def test_shrink_pulls_thin_samples_toward_zero():
    # A (1 game) and B (8 games) sit the same distance above the league mean; C and D balance them below it.
    pre = _pre({"A": (1, 0.4), "B": (8, 0.4), "C": (8, 0.0), "D": (8, 0.0)})
    sp = shrunk_pregame(pre, _margin({"A": (1, 10), "B": (8, 10), "C": (8, -10), "D": (8, -10)}), k=2.0)
    assert sp.loc["B", "off_pass_ppa"] == pytest.approx(0.2 * 8 / 10)
    assert sp.loc["A", "off_pass_ppa"] == pytest.approx(0.2 * 1 / 3)
    assert sp.loc["A", "margin"] == pytest.approx(10 * 1 / 3) and sp.loc["C", "margin"] == pytest.approx(-10 * 8 / 10)
    assert not sp.isna().any().any()


def test_shrink_k_zero_only_centers():
    sp = shrunk_pregame(_pre({"A": (1, 0.4), "B": (8, 0.0)}), _margin({"A": (1, 4), "B": (8, 0)}), k=0.0)
    assert sp.loc["A", "def_stuff"] == pytest.approx(0.2) and sp.loc["A", "margin"] == pytest.approx(2)


def test_shrink_turns_missing_values_into_league_average():
    pre = _pre({"A": (2, 0.4), "B": (8, 0.0)})
    pre.loc["A", "off_stuff"] = float("nan")
    sp = shrunk_pregame(pre, _margin({"B": (8, 3)}), k=2.0)
    assert sp.loc["A", "off_stuff"] == 0.0 and sp.loc["A", "margin"] == 0.0


def test_features_with_no_games_is_elo_only():
    f = features(pd.DataFrame(columns=stat_cols() + ["margin"]), "H", "A", 1600, 1500)
    assert f["elo"] == 100 and all(f[k] == 0 for k in KEYS) and f["margin"] == 0
    assert list(f) == EDGE_KEYS


def test_one_team_with_no_games_sits_at_league_average():
    # H has played (above average on offense, average on defense); A has not played at all.
    pre = _pre({"H": (2, 0.4), "B": (8, 0.0)})
    for c in stat_cols():
        if c.startswith("def_"):
            pre[c] = 0.1
    f = features(shrunk_pregame(pre, _margin({"H": (2, 14), "B": (8, 0)}), 2.0), "H", "A", 1500, 1500)
    assert f["pass_ppa"] == pytest.approx(0.2 * 2 / 4) and f["stuff"] == pytest.approx(-0.2 * 2 / 4)
    assert f["margin"] == pytest.approx(7 * 2 / 4) and f["elo"] == 0
    assert not any(math.isnan(v) for v in f.values())


def test_features_none_without_elo():
    sp = shrunk_pregame(_pre({"H": (3, 0.1), "A": (3, 0.0)}), _margin({"H": (3, 1), "A": (3, 0)}), 2.0)
    assert features(sp, "H", "A", None, 1500) is None and features(sp, "H", "A", 1500, None) is None


def test_features_are_home_minus_away():
    pre = _pre({"H": (8, 0.0), "A": (8, 0.0)})
    pre.loc["H", "off_rush_sr"], pre.loc["A", "off_rush_sr"] = 0.5, 0.3   # H runs better
    pre.loc["H", "def_rush_sr"], pre.loc["A", "def_rush_sr"] = 0.3, 0.5   # H allows less
    f = features(shrunk_pregame(pre, _margin({"H": (8, 7), "A": (8, -7)}), 0.0), "H", "A", 1500, 1550)
    assert f["rush_sr"] == pytest.approx(0.4) and f["margin"] == 14 and f["elo"] == -50
