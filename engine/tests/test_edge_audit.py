import numpy as np
import pandas as pd

from cfbm.edge_audit import compare, elo_continuity, log_loss, market_frame


def test_log_loss_matches_hand_value():
    assert round(log_loss(np.array([0.8, 0.3]), np.array([1.0, 0.0])), 4) == 0.2899


def test_compare_counts_picks_from_sign_of_lin():
    held = pd.DataFrame({"game_id": [1, 2], "lin": [2.0, 1.0]})
    market = pd.DataFrame({"game_id": [1, 2], "season": [2024, 2024], "home_win": [1, 0],
                           "spread": [-7.0, 3.0], "book_home": [0.69, 0.41]})
    out = compare(held, market)
    assert out["games"] == 2 and out["modelPicks"] == 0.5 and out["marketPicks"] == 1.0


def test_compare_subset_limits_the_games():
    held = pd.DataFrame({"game_id": [1, 2], "lin": [2.0, 1.0]})
    market = pd.DataFrame({"game_id": [1, 2], "season": [2024, 2024], "home_win": [1, 0],
                           "spread": [-7.0, 3.0], "book_home": [0.69, 0.41]})
    out = compare(held, market, subset=pd.Series([True, False]))
    assert out["games"] == 1 and out["modelPicks"] == 1.0


def _g(gid, home, away, date, hpre, hpost, apre, apost, hp=21, ap=14, season=2024):
    return {"id": gid, "season": season, "homeTeam": home, "awayTeam": away, "startDate": date + "T18:00:00.000Z",
            "homePoints": hp, "awayPoints": ap, "homePregameElo": hpre, "homePostgameElo": hpost,
            "awayPregameElo": apre, "awayPostgameElo": apost}


def test_elo_continuity_is_one_when_pregame_equals_last_postgame():
    games = [_g(1, "A", "B", "2024-09-01", hpre=1500, hpost=1520, apre=1500, apost=1480),
             _g(2, "A", "C", "2024-09-08", hpre=1520, hpost=1530, apre=1400, apost=1390)]
    assert elo_continuity(games) == 1.0


def test_elo_continuity_drops_when_pregame_already_holds_the_result():
    games = [_g(1, "A", "B", "2024-09-01", hpre=1500, hpost=1520, apre=1500, apost=1480),
             _g(2, "A", "C", "2024-09-08", hpre=1530, hpost=1530, apre=1400, apost=1390)]
    assert elo_continuity(games) == 0.0


def test_market_frame_keeps_decided_fbs_games_with_a_spread():
    games = {1: _g(1, "A", "B", "2024-09-01", 1, 1, 1, 1, hp=30, ap=10),
             2: _g(2, "A", "FCS U", "2024-09-08", 1, 1, 1, 1),
             3: _g(3, "B", "A", "2024-09-15", 1, 1, 1, 1, hp=10, ap=20),
             4: _g(4, "B", "A", "2024-09-22", 1, 1, 1, 1)}
    lines = {1: {"lines": [{"provider": "consensus", "spread": -7.0}]}, 2: {"lines": [{"provider": "x", "spread": -30.0}]},
             3: {"lines": [{"provider": "x", "spread": 3.0}]}, 4: {"lines": []}}
    mf = market_frame(games, lines, {2024: {"A", "B"}})
    assert list(mf["game_id"]) == [1, 3] and list(mf["home_win"]) == [1, 0]
    assert mf["book_home"].iloc[0] > 0.5 > mf["book_home"].iloc[1]


def test_elo_continuity_ignores_games_against_non_fbs_teams():
    # CFBD puts an unrelated placeholder Elo on FBS-vs-FCS rows (2022 on); the FBS chain skips over them.
    games = [_g(1, "A", "B", "2024-09-01", hpre=1500, hpost=1520, apre=1500, apost=1480),
             _g(2, "A", "FCS U", "2024-09-08", hpre=1900, hpost=1900, apre=1000, apost=1000),
             _g(3, "A", "B", "2024-09-15", hpre=1520, hpost=1530, apre=1480, apost=1470)]
    assert elo_continuity(games) < 1.0
    assert elo_continuity(games, fbs={"A", "B"}) == 1.0
