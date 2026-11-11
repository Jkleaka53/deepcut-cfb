import numpy as np
import pandas as pd
import pytest

from cfbm.shootout import SHOOT_FEATURES, X_KEYS, side_features, training_rows
from cfbm.swing_data import team_games


def _adv(gid, season, week, team, opp, off, dfn):
    side = lambda v: {"ppa": v[0], "successRate": v[1], "explosiveness": v[2], "plays": v[3],
                      "passingPlays": {"ppa": v[0], "successRate": v[1]}}
    return {"gameId": gid, "season": season, "week": week, "seasonType": "regular", "team": team, "opponent": opp,
            "offense": side(off), "defense": side(dfn)}


def test_team_games_default_unchanged():
    cols = list(team_games([]).columns)
    assert cols[:5] == ["game_id", "season", "order", "team", "opponent"]
    assert "off_pass_ppa" in cols and "off_plays" not in cols


def test_team_games_with_shoot_features():
    tg = team_games([_adv(1, 2024, 1, "A", "B", (0.1, 0.4, 1.2, 72), (0.0, 0.4, 1.1, 65))], SHOOT_FEATURES)
    assert tg.loc[0, "off_plays"] == 72 and tg.loc[0, "def_plays"] == 65
    assert tg.loc[0, "off_ppa"] == pytest.approx(0.1)


def test_side_features_sum_offense_and_defense():
    pre = pd.DataFrame({"games": [4, 4], "off_ppa": [0.3, 0.0], "def_ppa": [0.0, 0.1], "off_sr": [0.4, 0.4],
                        "def_sr": [0.4, 0.5], "off_expl": [1.2, 1.0], "def_expl": [1.0, 1.3],
                        "off_plays": [70, 60], "def_plays": [65, 75]}, index=["A", "B"])
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
