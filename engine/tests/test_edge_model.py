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


def test_margin_skips_a_game_still_being_played():
    live = {**_game(1, "A", "B", 14, 0, week=1), "completed": False}
    assert team_margins([live], FBS, {1: 1}).empty
    assert len(team_margins([{**live, "completed": True}], FBS, {1: 1})) == 2


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


# --- training frame and fit ---------------------------------------------------------------------------------
import numpy as np  # noqa: E402

from cfbm import config  # noqa: E402
from cfbm.edge_backtest import held_out  # noqa: E402
from cfbm.edge_model import frame, train  # noqa: E402
from cfbm.swing_data import pregame_adjusted  # noqa: E402

TEAMS = [f"T{i}" for i in range(8)]


def _world(seasons=(2023, 2024), weeks=7, seed=4):
    """Round robin among 8 teams for each season: advanced-stat rows, games with points and Elo."""
    rng = np.random.default_rng(seed)
    tg_rows, games, gid = [], {}, 0
    strength = dict(zip(TEAMS, np.linspace(-1, 1, 8)))
    for s in seasons:
        for wk in range(1, weeks + 1):
            rot = [TEAMS[0]] + TEAMS[1:][wk - 1:] + TEAMS[1:][:wk - 1]
            for i in range(4):
                h, a = rot[i], rot[7 - i]
                gid += 1
                hp = int(24 + 10 * strength[h] + rng.integers(-10, 11))
                ap = int(24 + 10 * strength[a] + rng.integers(-10, 11))
                ap = ap + 1 if ap == hp else ap
                games[gid] = {"id": gid, "season": s, "week": wk, "seasonType": "regular", "homeTeam": h, "awayTeam": a,
                              "homePoints": hp, "awayPoints": ap, "neutralSite": False, "startDate": f"{s}-09-{wk:02d}",
                              "homePregameElo": 1500 + 200 * strength[h] + wk, "awayPregameElo": 1500 + 200 * strength[a]}
                for t, o in ((h, a), (a, h)):
                    row = {"game_id": gid, "season": s, "order": wk, "team": t, "opponent": o}
                    for c in stat_cols():
                        row[c] = strength[t] * (0.1 if c.startswith("off_") else -0.1) + rng.normal(0, 0.05)
                    tg_rows.append(row)
    return pd.DataFrame(tg_rows), games, {s: set(TEAMS) for s in seasons}


def test_frame_keeps_early_games_and_flags_them():
    tg, games, fbs = _world()
    fr = frame(tg, games, fbs, k=2.0).set_index("game_id")
    assert len(fr) == len(games)
    wk1 = fr.loc[1]
    assert not wk1.scored_before and wk1.f_pass_ppa == 0 and wk1.f_margin == 0
    assert wk1.f_elo == pytest.approx(games[1]["homePregameElo"] - games[1]["awayPregameElo"])
    assert fr.loc[max(games)].scored_before
    wk3 = fr.loc[[g for g, x in games.items() if x["week"] == 3 and x["season"] == 2023]]
    assert not wk3.scored_before.any() and (wk3.f_pass_ppa != 0).all()   # two games each: scored, but thin


def test_frame_skips_games_without_elo_ties_and_non_fbs():
    tg, games, fbs = _world()
    games[5]["homePregameElo"] = None
    games[6]["awayPoints"] = games[6]["homePoints"]
    fbs[2023] = fbs[2023] - {"T7"}
    fr = frame(tg, games, fbs, k=2.0)
    assert 5 not in set(fr.game_id) and 6 not in set(fr.game_id)
    t7 = {g for g, x in games.items() if x["season"] == 2023 and "T7" in (x["homeTeam"], x["awayTeam"])}
    assert not t7 & set(fr.game_id)


def test_frame_matches_live_features_for_the_same_game():
    tg, games, fbs = _world()
    gid = max(g for g, x in games.items() if x["season"] == 2024 and x["week"] == 5)
    g = games[gid]
    row = frame(tg, games, fbs, k=2.0).set_index("game_id").loc[gid]
    tm = team_margins(list(games.values()), fbs, {i: x["week"] for i, x in games.items()})
    sp = shrunk_pregame(pregame_adjusted(tg, 2024, 5, w=config.OPP_ADJUST), margin_before(tm, 2024, 5), 2.0)
    live = features(sp, g["homeTeam"], g["awayTeam"], g["homePregameElo"], g["awayPregameElo"])
    assert all(row[f"f_{k}"] == pytest.approx(live[k]) for k in EDGE_KEYS)


def test_frame_never_uses_the_game_itself():
    tg, games, fbs = _world()
    before = frame(tg, games, fbs, k=2.0).set_index("game_id").loc[20]
    games[20]["homePoints"], games[20]["awayPoints"] = 99, 0
    tg.loc[tg.game_id == 20, stat_cols()] = 9.0
    after = frame(tg, games, fbs, k=2.0).set_index("game_id").loc[20]
    assert all(before[f"f_{k}"] == pytest.approx(after[f"f_{k}"]) for k in EDGE_KEYS)


def test_train_scale_is_monotone_and_has_101_points():
    tg, games, fbs = _world(seasons=(2021, 2022, 2023, 2024))
    m = train(frame(tg, games, fbs, k=2.0))
    q = m["scale"]["overall"]
    assert len(q) == 101 and q == sorted(q) and set(m["features"]) == set(EDGE_KEYS)
    assert m["features"]["elo"]["coef"] > 0 and m["games"] == len(games) and m["seasons"] == [2021, 2022, 2023, 2024]
    assert set(m["features"]["elo"]) == {"coef", "mean", "sd"} and "coef" in m["home"]


def test_held_out_accepts_a_fit_function():
    tg, games, fbs = _world(seasons=(2021, 2022, 2023, 2024))
    fr = frame(tg, games, fbs, k=2.0)
    df = held_out(fr, keys=EDGE_KEYS, fit=train)
    assert {"season", "game_id", "lin", "score", "favored_won", "scored_before"} <= set(df.columns)
    assert len(df) == len(fr) and df["score"].between(0, 10).all()
    assert df["favored_won"].mean() > 0.6   # Elo tracks strength in this world, so held-out picks beat a coin


def test_games_against_non_fbs_teams_do_not_feed_the_stats():
    tg, games, fbs = _world()
    fbs[2023] = fbs[2023] - {"T7"}
    with_rows = frame(tg, games, fbs, k=0.0).set_index("game_id")
    without = frame(tg[(tg.season != 2023) | ((tg.team != "T7") & (tg.opponent != "T7"))], games, fbs, k=0.0).set_index("game_id")
    late = [g for g, x in games.items() if x["season"] == 2023 and x["week"] == 7 and "T7" not in (x["homeTeam"], x["awayTeam"])]
    assert late
    for gid in late:
        assert all(with_rows.loc[gid, f"f_{k}"] == pytest.approx(without.loc[gid, f"f_{k}"]) for k in EDGE_KEYS)


def test_features_carry_talent_and_returning_production():
    """Owner 2026-11-11: the edge model reads roster talent and returning production (team_prior)."""
    p = {"talent": {"H": 900.0, "A": 700.0}, "ret": {"H": 0.5, "A": 0.75}}
    f = features(pd.DataFrame(columns=stat_cols() + ["margin"]), "H", "A", 1600, 1500, prior=p)
    assert f["talent"] == pytest.approx(200.0) and f["ret"] == pytest.approx(-0.25)
    none = features(pd.DataFrame(columns=stat_cols() + ["margin"]), "H", "A", 1600, 1500)
    assert none["talent"] == 0.0 and none["ret"] == 0.0


def test_frame_reads_priors_for_each_season():
    tg, games, fbs = _world()
    priors = {s: {"talent": {t: 10.0 * i for i, t in enumerate(sorted(f))}, "ret": {}} for s, f in fbs.items()}
    fr = frame(tg, games, fbs, k=2.0, priors=priors).set_index("game_id")
    gid = next(iter(fr.index))
    g = games[gid]
    want = priors[g["season"]]["talent"][g["homeTeam"]] - priors[g["season"]]["talent"][g["awayTeam"]]
    assert fr.loc[gid, "f_talent"] == pytest.approx(want) and (fr["f_ret"] == 0).all()
