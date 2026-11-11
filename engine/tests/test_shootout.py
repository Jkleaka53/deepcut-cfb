import numpy as np
import pandas as pd
import pytest

from cfbm.shootout import SHOOT_FEATURES, X_KEYS, side_features, training_rows
from cfbm.swing_data import team_games


def _adv(gid, season, week, team, opp, off, dfn):
    side = lambda v: {"ppa": v[0], "successRate": v[1], "explosiveness": v[2], "drives": v[3],
                      "passingPlays": {"ppa": v[0], "successRate": v[1]}}
    return {"gameId": gid, "season": season, "week": week, "seasonType": "regular", "team": team, "opponent": opp,
            "offense": side(off), "defense": side(dfn)}


def test_team_games_default_unchanged():
    cols = list(team_games([]).columns)
    assert cols[:5] == ["game_id", "season", "order", "team", "opponent"]
    assert "off_pass_ppa" in cols and "off_drives" not in cols


def test_team_games_with_shoot_features():
    tg = team_games([_adv(1, 2024, 1, "A", "B", (0.1, 0.4, 1.2, 72), (0.0, 0.4, 1.1, 65))], SHOOT_FEATURES)
    assert tg.loc[0, "off_drives"] == 72 and tg.loc[0, "def_drives"] == 65
    assert tg.loc[0, "off_ppa"] == pytest.approx(0.1)


def test_side_features_sum_offense_and_defense():
    pre = pd.DataFrame({"games": [4, 4], "off_ppa": [0.3, 0.0], "def_ppa": [0.0, 0.1], "off_sr": [0.4, 0.4],
                        "def_sr": [0.4, 0.5], "off_expl": [1.2, 1.0], "def_expl": [1.0, 1.3],
                        "off_drives": [70, 60], "def_drives": [65, 75]}, index=["A", "B"])
    x = side_features(pre, "A", "B", 1)
    assert set(x) == set(X_KEYS)
    assert x["x_ppa"] == pytest.approx(0.4) and x["x_pace"] == pytest.approx(145) and x["home"] == 1


def _toy():
    # A plays 4 games (wk 1-4); its opponents B, C, D, E each play enough to qualify by week 4 except as noted.
    sched = [(1, 1, "A", "B"), (2, 2, "A", "C"), (3, 3, "A", "D"), (4, 4, "A", "E"),
             (5, 1, "E", "C"), (6, 2, "E", "D"), (7, 3, "E", "B")]
    adv, games = [], {}
    for gid, wk, h, a in sched:
        for t, o in ((h, a), (a, h)):
            v = 0.1 * wk if t == "A" else 0.0
            adv.append(_adv(gid, 2024, wk, t, o, (v, 0.4, 1.0, 60 + wk), (0.0, 0.4, 1.0, 60)))
        games[gid] = {"id": gid, "season": 2024, "week": wk, "seasonType": "regular", "homeTeam": h, "awayTeam": a,
                      "homePoints": 30 + gid, "awayPoints": 20, "neutralSite": False, "startDate": f"2024-09-{wk:02d}T19:00:00Z"}
    return team_games(adv, SHOOT_FEATURES), games, {2024: {"A", "B", "C", "D", "E"}}


def test_training_rows_two_sides_and_priors_only():
    tg, games, fbs = _toy()
    rows = training_rows(tg, games, fbs)
    g4 = rows[rows["game_id"] == 4]
    assert set(g4["side"]) == {"home", "away"}
    home = g4[g4["side"] == "home"].iloc[0]
    assert home["points"] == 34 and home["total"] == 54 and home["home"] == 1
    # A's prior off_ppa = mean(0.1, 0.2, 0.3) = 0.2; E's prior def_ppa = 0 -> x_ppa 0.2 (week 4 not included)
    assert home["x_ppa"] == pytest.approx(0.2)
    assert not (rows["game_id"] == 1).any()


from cfbm.shootout import fit, game_score, predict_side, predicted_total  # noqa: E402


def test_fit_recovers_signal():
    rng = np.random.default_rng(2)
    n = 6000
    df = pd.DataFrame({k: rng.normal(0, 1, n) for k in X_KEYS})
    df["home"] = rng.integers(0, 2, n).astype(float)
    df["points"] = 28 + 6 * df["x_ppa"] + rng.normal(0, 3, n)
    m = fit(df)
    assert m["coef"]["x_ppa"] == pytest.approx(6, abs=0.5)
    assert abs(m["coef"]["x_sr"]) < 0.5
    assert m["intercept"] == pytest.approx(28, abs=0.5)


HAND = {"means": {k: 0.0 for k in X_KEYS}, "sds": {k: 1.0 for k in X_KEYS},
        "coef": {**{k: 0.0 for k in X_KEYS}, "x_ppa": 10.0}, "intercept": 20.0}


def _pre(home_ppa, away_ppa, games=4, drives=60.0):
    return pd.DataFrame({"games": [games, 4], "off_ppa": [home_ppa, away_ppa], "def_ppa": [0.0, 0.0],
                         "off_sr": [0.4, 0.4], "def_sr": [0.4, 0.4], "off_expl": [1.0, 1.0], "def_expl": [1.0, 1.0],
                         "off_drives": [drives, 60.0], "def_drives": [60.0, 60.0]}, index=["H", "A"])


def test_game_score_is_combined_total():
    """Owner 2026-11-10: rank by combined expected scoring (backtest: WVU-TTU 2nd of its week)."""
    p = _pre(1.0, -0.5)
    assert game_score(HAND, p, "H", "A", neutral=False) == pytest.approx(45.0)
    assert predicted_total(HAND, p, "H", "A", neutral=False) == pytest.approx(45.0)


def test_nan_feature_disqualifies():
    assert game_score(HAND, _pre(1.0, 0.5, drives=float("nan")), "H", "A", neutral=False) is None
    assert predict_side(HAND, {**{k: 0.0 for k in X_KEYS}, "x_pace": float("nan")}) is None


def test_early_team_disqualifies():
    assert game_score(HAND, _pre(1.0, 0.5, games=2), "H", "A", neutral=False) is None


from cfbm.shootout import pick, why_text  # noqa: E402


def _s(gid, week="7"):
    return {"id": gid, "week": int(week), "seasonType": "regular"}


def test_pick_skips_gotw():
    scored = [(_s(1), 70.0, "w1"), (_s(2), 65.0, "w2"), (_s(3), 60.0, "w3")]
    picks, watch = pick(scored, {"7": {"id": 1, "why": "x"}})
    assert picks["7"] == {"id": 2, "why": "w2"}
    assert 1 not in watch and 2 not in watch and watch == {3}


def test_watch_is_next_three():
    scored = [(_s(i), 100.0 - i, f"w{i}") for i in range(1, 7)]
    picks, watch = pick(scored, {})
    assert picks["7"]["id"] == 1 and watch == {2, 3, 4}


def test_no_pick_when_nothing_qualifies():
    picks, watch = pick([(_s(1, "8"), 50.0, "w")], {})
    assert "7" not in picks and picks["8"]["id"] == 1 and watch == set()


def _rank_pre():
    n = 30
    teams = [f"T{i}" for i in range(n)]
    pre = pd.DataFrame({"games": 5, "off_ppa": np.linspace(0.5, -0.4, n), "def_ppa": np.linspace(-0.4, 0.5, n),
                        "off_sr": 0.4, "def_sr": 0.4, "off_expl": 1.0, "def_expl": 1.0,
                        "off_drives": np.linspace(16, 9, n), "def_drives": 12.0}, index=teams)
    return pre


def test_why_text_both_ways():
    pre = _rank_pre()
    # T0 and T1: best offenses, best defenses -> not "both defenses give it up"
    assert why_text(pre, "T1", "T0") == ("Lots of expected scoring: offenses rank 1st and 2nd in points added per play, "
                                         "defenses 1st and 2nd of 30. Pace: 1st and 2nd in drives per game.")
    # Make T28/T29 strong offenses with weak defenses
    pre.loc[["T28", "T29"], "off_ppa"] = [0.6, 0.7]
    assert why_text(pre, "T28", "T29").startswith("Both offenses score efficiently and both defenses give it up: "
                                                  "offenses rank 1st and 2nd")


def test_ordinal():
    from cfbm.shootout import ordinal
    assert [ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 101, 112)] == \
        ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "101st", "112th"]


def test_why_text_drops_pace_when_both_slow():
    pre = _rank_pre()
    # T28 and T29 have the fewest drives per game (ranks 29th and 30th of 30): no pace line
    text = why_text(pre, "T28", "T29")
    assert "Pace" not in text and text.endswith("of 30.")
