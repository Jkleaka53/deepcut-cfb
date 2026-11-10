import pandas as pd

from cfbm.qb import career, current_starter, passer_games


def _box(game_id, team, passers, opp="Opp"):
    """passers: list of (athlete_id, name, completions, attempts)"""
    def team_entry(t, ps):
        return {"team": t, "categories": [{"name": "passing", "types": [
            {"name": "C/ATT", "athletes": [{"id": str(a), "name": n, "stat": f"{c}/{att}"} for a, n, c, att in ps]},
            {"name": "YDS", "athletes": [{"id": str(a), "name": n, "stat": "100"} for a, n, _, _ in ps]}]}]}
    return {"id": game_id, "teams": [team_entry(team, passers), team_entry(opp, [(999, "Opp QB", 10, 20)])]}


def _frame(*week_boxes, season=2025, season_type="regular"):
    return pd.concat([passer_games(b, season, season_type, wk) for wk, b in week_boxes], ignore_index=True)


def test_share_threshold():
    df = passer_games([_box(1, "A", [(1, "Starter", 20, 30), (2, "Backup", 5, 10)])], 2025, "regular", 1)
    s = df[df["team"] == "A"].set_index("athlete_id")
    assert s.loc[1, "share"] == 0.75 and bool(s.loc[1, "is_primary"])
    df2 = passer_games([_box(2, "A", [(1, "Starter", 20, 29), (2, "Backup", 5, 11)])], 2025, "regular", 1)
    assert not df2[df2["athlete_id"] == 1]["is_primary"].iloc[0]


def test_split_game_has_no_primary():
    df = passer_games([_box(1, "A", [(1, "X", 10, 20), (2, "Y", 10, 20)])], 2025, "regular", 1)
    assert not df[df["team"] == "A"]["is_primary"].any()


def test_columns_and_order():
    df = passer_games([_box(1, "A", [(1, "X", 10, 20)])], 2025, "postseason", 1)
    assert set(["game_id", "season", "order", "team", "athlete_id", "name", "attempts", "team_attempts",
                "share", "is_primary"]) <= set(df.columns)
    assert df["order"].iloc[0] == 101


def test_non_numeric_athlete_ids_skipped():
    box = _box(1, "A", [(1, "X", 10, 20)])
    box["teams"][0]["categories"][0]["types"][0]["athletes"].append({"id": "TEAM", "name": "Team", "stat": "0/1"})
    df = passer_games([box], 2025, "regular", 1)
    assert df[df["team"] == "A"]["athlete_id"].tolist() == [1]


def test_career_spans_transfer():
    a = passer_games([_box(10, "Washington State", [(7, "John Mateer", 20, 30)])], 2024, "regular", 3)
    b = passer_games([_box(20, "Oklahoma", [(7, "John Mateer", 22, 30)])], 2025, "regular", 3)
    c = career(pd.concat([a, b], ignore_index=True), 7)
    assert sorted(c["team"].tolist()) == ["Oklahoma", "Washington State"]


def test_career_excludes_non_primary_games():
    df = passer_games([_box(1, "A", [(7, "Q", 10, 20), (8, "R", 10, 20)])], 2025, "regular", 1)
    assert career(df, 7).empty


def test_starter_after_injury():
    weeks = [(w, [_box(w, "A", [(1, "QB A", 20, 30)])]) for w in range(1, 6)]
    weeks += [(w, [_box(w, "A", [(2, "QB B", 20, 30)])]) for w in (6, 7)]
    assert current_starter(_frame(*weeks), "A", 2025, before_order=8) == (2, "QB B")
    assert current_starter(_frame(*weeks), "A", 2025, before_order=6) == (1, "QB A")


def test_starter_falls_back_to_most_attempts_when_last_game_split():
    weeks = [(1, [_box(1, "A", [(1, "QB A", 20, 30)])]), (2, [_box(2, "A", [(1, "QB A", 20, 30)])]),
             (3, [_box(3, "A", [(1, "QB A", 10, 15), (2, "QB B", 10, 15)])])]
    assert current_starter(_frame(*weeks), "A", 2025, before_order=4) == (1, "QB A")


def test_starter_none_in_week1():
    weeks = [(1, [_box(1, "A", [(1, "QB A", 20, 30)])])]
    assert current_starter(_frame(*weeks), "A", 2025, before_order=1) is None


def test_starter_is_latest_primary_not_season_attempts_leader():
    # A starts 8 games, B takes over for 2, then B throws 70% in a split game -> B is still the starter.
    weeks = [(w, [_box(w, "A", [(1, "QB A", 20, 30)])]) for w in range(1, 9)]
    weeks += [(w, [_box(w, "A", [(2, "QB B", 20, 30)])]) for w in (9, 10)]
    weeks += [(11, [_box(11, "A", [(2, "QB B", 14, 21), (1, "QB A", 6, 9)])])]
    assert current_starter(_frame(*weeks), "A", 2025, before_order=12) == (2, "QB B")
