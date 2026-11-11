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


def test_side_advantage_adds_what_the_defense_allows():
    from cfbm.swing_data import side_advantage
    # good offense (0.3) vs a defense that allows a lot (0.25) beats the same offense vs a stingy one (0.0)
    assert side_advantage(0.3, 0.25, "pass_ppa") > side_advantage(0.3, 0.0, "pass_ppa")
    # stuff rate: lower is better for the offense, and a defense that stuffs a lot hurts it
    assert side_advantage(0.1, 0.3, "stuff") < side_advantage(0.1, 0.1, "stuff")


def test_empty_input_gives_empty_frame():
    assert training_frame(team_games([]), {}, {}).empty


def _post_world(include_later=True):
    rows, games, gid = [], {}, 0
    rr = [("A", "B", 1), ("C", "D", 1), ("A", "C", 2), ("B", "D", 2), ("A", "D", 3), ("B", "C", 3)]
    for h, a, wk in rr:
        gid += 1
        rows += [adv(gid, 2019, wk, h, a, ppa=0.1), adv(gid, 2019, wk, a, h, ppa=0.1)]
        games[gid] = {"id": gid, "season": 2019, "seasonType": "regular", "week": wk, "homeTeam": h, "awayTeam": a,
                      "homePoints": 20, "awayPoints": 10, "neutralSite": False, "completed": True,
                      "startDate": f"2019-09-0{wk}T19:00:00.000Z"}
    post = [(200, "A", "B", "2019-12-20T19:00:00.000Z", 0.1)]
    if include_later:
        post.append((100, "A", "C", "2020-01-05T19:00:00.000Z", 5.0))  # later game, smaller id
    for pid, h, a, start, ppa in post:
        rows += [adv(pid, 2019, 1, h, a, ppa=ppa, st="postseason"), adv(pid, 2019, 1, a, h, ppa=0.1, st="postseason")]
        games[pid] = {"id": pid, "season": 2019, "seasonType": "postseason", "week": 1, "homeTeam": h, "awayTeam": a,
                      "homePoints": 30, "awayPoints": 10, "neutralSite": True, "completed": True, "startDate": start}
    return team_games(rows), games


def test_postseason_priors_follow_dates_not_ids():
    fbs = {2019: {"A", "B", "C", "D"}}
    tg, games = _post_world()
    with_later = training_frame(tg, games, fbs).set_index("game_id").loc[200, "f_pass_ppa"]
    tg2, games2 = _post_world(include_later=False)
    without = training_frame(tg2, games2, fbs).set_index("game_id").loc[200, "f_pass_ppa"]
    assert with_later == pytest.approx(without)


def test_apply_orders_remaps_by_game():
    from cfbm.swing_data import apply_orders
    tg, games = _post_world()
    out = apply_orders(tg, {200: 101, 100: 102})
    assert set(out.loc[out["game_id"] == 100, "order"]) == {102} and set(out.loc[out["game_id"] == 1, "order"]) == set(tg.loc[tg["game_id"] == 1, "order"])


def test_training_frame_reads_opponent_adjusted_stats(monkeypatch):
    """Owner 2026-11-10: the model trains on opponent-adjusted stats (config.OPP_ADJUST)."""
    from cfbm import config
    from cfbm.swing_data import side_advantage
    tg, games = _season()
    fbs = {2019: {"A", "B", "C", "D"}}
    monkeypatch.setattr(config, "OPP_ADJUST", 0.0)
    raw = training_frame(tg, games, fbs).set_index("game_id")
    monkeypatch.setattr(config, "OPP_ADJUST", 1.0)
    adj = training_frame(tg, games, fbs).set_index("game_id")
    assert set(raw.index) == set(adj.index)
    assert any(abs(raw.loc[g, "ha_pass_ppa"] - adj.loc[g, "ha_pass_ppa"]) > 1e-9 for g in raw.index)
    from cfbm.swing_data import adjusted_priors, apply_orders
    from cfbm.plays import game_orders
    pri = adjusted_priors(apply_orders(tg, game_orders(list(games.values()))), w=1.0).set_index(["game_id", "team"])
    g = games[9]
    H, A = pri.loc[(9, g["homeTeam"])], pri.loc[(9, g["awayTeam"])]
    assert adj.loc[9, "ha_pass_ppa"] == pytest.approx(side_advantage(H["off_pass_ppa"], A["def_pass_ppa"], "pass_ppa"))
