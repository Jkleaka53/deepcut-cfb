import pandas as pd

from cfbm.qb import COLUMNS
from cfbm.skill import SKILL_COLUMNS
from cfbm.watch import watch_list


def P(gid, order, aid, name, att, team="M", season=2026):
    return {"game_id": gid, "season": season, "season_type": "regular", "week": order, "order": order, "team": team,
            "athlete_id": aid, "name": name, "attempts": att, "team_attempts": 30, "share": att / 30, "is_primary": att >= 21}


def K(gid, order, aid, name, cat, count, yards, team="M", season=2026):
    return {"game_id": gid, "season": season, "order": order, "team": team, "athlete_id": aid, "name": name,
            "category": cat, "count": count, "yards": yards}


def frames(prows, krows):
    return pd.DataFrame(prows, columns=COLUMNS), pd.DataFrame(krows, columns=SKILL_COLUMNS)


BASE_P = [P(1, 1, 10, "Starter", 28), P(1, 1, 11, "Backup", 2), P(2, 2, 10, "Starter", 30),
          P(2, 2, 12, "Third", 1), P(3, 3, 10, "Starter", 25), P(3, 3, 11, "Backup", 3)]
BASE_K = [K(g, g, 20, "Wr One", "receiving", 6, 100) for g in (1, 2, 3)] + \
         [K(g, g, 21, "Wr Two", "receiving", 4, 50) for g in (1, 2)] + \
         [K(g, g, 22, "Wr Three", "receiving", 3, 30) for g in (1, 2, 3)] + \
         [K(g, g, 23, "Wr Four", "receiving", 1, 10) for g in (1, 2, 3)] + \
         [K(g, g, 30, "Rb One", "rushing", 15, 80) for g in (1, 2, 3)] + \
         [K(g, g, 10, "Starter", "rushing", 20, 40) for g in (1, 2, 3)] + \
         [K(3, 3, 22, "Wr Three", "rushing", 25, 60)]


POS = {10: "QB", 11: "QB", 12: "QB", 20: "WR", 21: "WR", 22: "TE", 23: "WR", 30: "RB"}


def wl(prows=BASE_P, krows=BASE_K, starter=(10, "Starter"), before=4, positions=POS):
    p, k = frames(prows, krows)
    return watch_list(p, k, "M", 2026, before, starter, positions)


def test_order_and_roles():
    out = wl()
    assert [(x["name"], x["role"]) for x in out["players"]] == [
        ("Starter", "QB"), ("Backup", "QB2"), ("Wr One", "WR"), ("Wr Two", "WR"), ("Wr Three", "WR"), ("Rb One", "RB")]


def test_backup_most_attempts_not_starter():
    assert wl()["backupId"] == 11


def test_no_backup():
    out = wl(prows=[P(1, 1, 10, "Starter", 28)])
    assert out["backupId"] is None
    assert [x["role"] for x in out["players"]][:2] == ["QB", "WR"]


def test_share_of_receiving_and_rushing():
    by = {x["name"]: x for x in wl()["players"]}
    # receiving total = 300 + 100 + 90 + 30 = 520
    assert by["Wr One"]["share"] == round(300 / 520, 3) and by["Wr One"]["shareOf"] == "receiving yards"
    # rushing total = 240 + 120 + 60 = 420
    assert by["Rb One"]["share"] == round(240 / 420, 3) and by["Rb One"]["shareOf"] == "rushing yards"
    assert by["Starter"]["share"] is None and by["Starter"]["shareOf"] is None


def test_no_stats_last_game_flag():
    by = {x["name"]: x for x in wl()["players"]}
    assert by["Wr Two"]["noStatsLastGame"] is True
    assert by["Wr One"]["noStatsLastGame"] is False
    assert by["Starter"]["noStatsLastGame"] is False


def test_last_game_is_latest_with_any_rows():
    # game 4 is after kickoff cutoff (before=4): ignored; last game stays 3
    k = BASE_K + [K(4, 4, 21, "Wr Two", "receiving", 2, 20)]
    by = {x["name"]: x for x in wl(krows=k)["players"]}
    assert by["Wr Two"]["noStatsLastGame"] is True
    # a later game with only skill rows (no passer rows) still counts as the last game
    by = {x["name"]: x for x in wl(krows=k, before=5)["players"]}
    assert by["Wr Two"]["noStatsLastGame"] is False and by["Starter"]["noStatsLastGame"] is True


def test_rb_not_double_listed():
    # Wr Three has the most carries of non-QBs only if counted; RB must not repeat a listed WR
    k = BASE_K + [K(g, g, 22, "Wr Three", "rushing", 40, 100) for g in (1, 2)]
    names = [x["name"] for x in wl(krows=k)["players"]]
    assert names.count("Wr Three") == 1 and names[-1] == "Rb One"


def test_other_team_and_season_ignored():
    k = BASE_K + [K(1, 1, 99, "Other", "receiving", 9, 999, team="X"), K(9, 1, 98, "Old", "receiving", 9, 999, season=2025)]
    names = [x["name"] for x in wl(krows=k)["players"]]
    assert "Other" not in names and "Old" not in names


def test_no_starter_lists_skill_players_only():
    out = wl(starter=None)
    assert out["backupId"] is None and out["players"][0]["role"] == "WR"


def test_trick_pass_receiver_stays_a_receiver_and_is_not_backup():
    prows = [P(1, 1, 10, "Starter", 28), P(2, 2, 10, "Starter", 30), P(2, 2, 20, "Wr One", 1)]
    out = wl(prows=prows)
    assert out["backupId"] is None
    assert [x["name"] for x in out["players"] if x["role"] == "WR"][0] == "Wr One"


def test_unknown_position_falls_back_to_passing_volume():
    prows = BASE_P + [P(2, 2, 20, "Wr One", 1)]
    out = wl(prows=prows, positions={})
    assert out["backupId"] == 11  # 5 attempts beats the 1-attempt receiver
    assert "Wr One" in [x["name"] for x in out["players"] if x["role"] == "WR"]


def test_rb_must_be_a_back_when_position_known():
    k = BASE_K + [K(g, g, 22, "Wr Three", "rushing", 40, 100) for g in (1, 2)] + [K(1, 1, 40, "Ol Guy", "rushing", 99, 1)]
    out = wl(krows=k, positions={**POS, 40: "OL"})
    assert out["players"][-1]["name"] == "Rb One"
