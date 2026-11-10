from cfbm.skill import SKILL_COLUMNS, skill_games
from cfbm.plays import order_key


def _box(cat, count_type, rows):
    return [{"id": 9, "teams": [{"team": "Michigan", "categories": [{"name": cat, "types": [
        {"name": count_type, "athletes": [{"id": str(i), "name": n, "stat": c} for i, n, c, _ in rows]},
        {"name": "YDS", "athletes": [{"id": str(i), "name": n, "stat": y} for i, n, _, y in rows]},
        {"name": "TD", "athletes": [{"id": str(i), "name": n, "stat": "1"} for i, n, _, _ in rows]}]}]}]}]


def test_skill_games_parses_receiving():
    df = skill_games(_box("receiving", "REC", [(11, "A Wr", "7", "64")]), 2026, "regular", 10, "receiving")
    assert list(df.columns) == SKILL_COLUMNS
    r = df.iloc[0]
    assert (r.game_id, r.team, r.athlete_id, r["name"], r["count"], r.yards, r.category) == (9, "Michigan", 11, "A Wr", 7, 64, "receiving")
    assert r.order == order_key("regular", 10)


def test_skill_games_parses_rushing():
    df = skill_games(_box("rushing", "CAR", [(12, "A Rb", "18", "-3")]), 2026, "regular", 10, "rushing")
    assert (int(df.iloc[0]["count"]), int(df.iloc[0].yards), df.iloc[0].category) == (18, -3, "rushing")


def test_bad_stat_is_zero():
    df = skill_games(_box("receiving", "REC", [(13, "B", "--", "x")]), 2026, "regular", 10, "receiving")
    assert (int(df.iloc[0]["count"]), int(df.iloc[0].yards)) == (0, 0)


def test_team_totals_row_and_bad_ids_skipped():
    df = skill_games(_box("receiving", "REC", [(-1, "Team", "3", "20"), (14, "C", "1", "5")]), 2026, "regular", 10, "receiving")
    assert list(df.athlete_id) == [14]
