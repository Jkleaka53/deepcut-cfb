import pytest

from cfbm.swing_data import FEATURES, pregame, team_games, training_frame


def adv(gid, season, week, team, opp, ppa=0.2, sr=0.45, st="regular"):
    side = {"ppa": ppa, "successRate": sr, "explosiveness": 1.0, "stuffRate": 0.2, "lineYards": 3.0,
            "standardDowns": {"successRate": sr}, "passingDowns": {"successRate": sr - 0.1},
            "rushingPlays": {"ppa": ppa, "successRate": sr}, "passingPlays": {"ppa": ppa, "successRate": sr}}
    return {"gameId": gid, "season": season, "seasonType": st, "week": week, "team": team, "opponent": opp,
            "offense": side, "defense": {**side, "passingPlays": {"ppa": ppa / 2, "successRate": sr}}}


def test_nested_paths_parse():
    tg = team_games([adv(1, 2020, 1, "A", "B", ppa=0.3)])
    assert tg.iloc[0]["off_pass_ppa"] == 0.3 and tg.iloc[0]["def_pass_ppa"] == 0.15
    assert tg.iloc[0]["off_pd_sr"] == pytest.approx(0.35)
    assert {f"off_{k}" for k, *_ in FEATURES} <= set(tg.columns)


def test_pregame_uses_only_earlier_games():
    tg = team_games([adv(1, 2020, 1, "A", "B", ppa=0.1), adv(2, 2020, 2, "A", "C", ppa=0.3),
                     adv(3, 2020, 3, "A", "D", ppa=0.9)])
    p = pregame(tg, 2020, before_order=3)
    assert p.loc["A", "games"] == 2 and p.loc["A", "off_pass_ppa"] == pytest.approx(0.2)


def _season(teams=("A", "B", "C", "D")):
    # round robin, 4 weeks; week 4 A hosts B
    rows, games, gid = [], {}, 0
    sched = [("A", "C"), ("B", "D"), ("A", "D"), ("B", "C"), ("C", "D"), ("A", "B"), ("D", "A"), ("C", "B"), ("A", "B")]
    weeks = [1, 1, 2, 2, 3, 3, 4, 4, 5]
    for (h, a), wk in zip(sched, weeks):
        gid += 1
        rows += [adv(gid, 2019, wk, h, a, ppa=0.3 if h == "A" else 0.1), adv(gid, 2019, wk, a, h, ppa=0.3 if a == "A" else 0.1)]
        games[gid] = {"id": gid, "season": 2019, "seasonType": "regular", "week": wk, "homeTeam": h, "awayTeam": a,
                      "homePoints": 30 if h == "A" else 20, "awayPoints": 10 if h == "A" else 21, "neutralSite": gid == 9,
                      "completed": True}
    return team_games(rows), games


def test_training_needs_three_prior_games_each():
    tg, games = _season()
    fr = training_frame(tg, games, {2019: {"A", "B", "C", "D"}})
    assert set(fr["game_id"]) <= {7, 8, 9}
    assert len(fr) >= 1


def test_neutral_site_has_home_zero_and_target():
    tg, games = _season()
    fr = training_frame(tg, games, {2019: {"A", "B", "C", "D"}}).set_index("game_id")
    assert fr.loc[9, "home"] == 0 and fr.loc[9, "home_win"] == 1
    assert fr.loc[9, "f_pass_ppa"] > 0  # A's offense is better


def test_ties_and_fcs_dropped():
    tg, games = _season()
    games[9]["awayPoints"] = 30
    fr = training_frame(tg, games, {2019: {"A", "B", "C", "D"}})
    assert 9 not in set(fr["game_id"])
    fr2 = training_frame(tg, games, {2019: {"A", "C", "D"}})
    assert not ({7, 8} & set(fr2["game_id"])) or all(
        games[g]["homeTeam"] != "B" and games[g]["awayTeam"] != "B" for g in fr2["game_id"])
