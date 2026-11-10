import math

import pandas as pd
import pytest

from cfbm.plays import normalize_plays
from cfbm.team_stats import blended_profile, season_profile, team_game_pass


def _raw(i, ptype, ppa=0.1, off="A", deff="B", down=1, distance=10, period=1, game=1, off_score=0):
    return {"id": str(i), "gameId": game, "offense": off, "defense": deff, "home": "A", "away": "B",
            "offenseScore": off_score, "defenseScore": 0, "period": period, "down": down,
            "distance": distance, "playType": ptype, "playText": "", "ppa": ppa}


def _tg(rows):
    """rows: (season, season_type, week, game_id, team, opponent, dropbacks, sacks, epa_sum)"""
    out = []
    for s, st, wk, gid, team, opp, db, sk, epa in rows:
        out.append(dict(game_id=gid, season=s, season_type=st, week=wk,
                        order=wk if st == "regular" else 100 + wk, team=team, opponent=opp,
                        dropbacks=db, epa_sum=epa, epa_n=db, success=0, sacks=sk, ints=0, pressure_est=0,
                        pd_dropbacks=0, pd_epa_sum=0.0, pd_epa_n=0, pd_sacks=0))
    return pd.DataFrame(out)


def test_team_game_pass_counts_and_drops_garbage():
    raw = [_raw(1, "Pass Reception", 0.5), _raw(2, "Sack", -1.0), _raw(3, "Rush", 0.2),
           _raw(4, "Pass Incompletion", -0.2, down=3, distance=7),
           _raw(5, "Pass Reception", 0.3, off="B", deff="A")]
    tg = team_game_pass(normalize_plays(raw, 2025, "regular", 2)).set_index("team")
    a = tg.loc["A"]
    assert a["opponent"] == "B" and a["dropbacks"] == 3 and a["sacks"] == 1
    assert a["epa_sum"] == pytest.approx(-0.7) and a["success"] == 1
    assert a["pd_dropbacks"] == 1 and a["order"] == 2
    assert tg.loc["B", "dropbacks"] == 1

    garbage = [_raw(1, "Rush", off_score=30, period=4), _raw(2, "Pass Reception", 0.4, period=4)]
    assert team_game_pass(normalize_plays(garbage, 2025, "regular", 2)).empty


def test_rates_are_pooled():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 10, 1, 0.0), (2025, "regular", 2, 2, "A", "C", 30, 0, 0.0)])
    p = season_profile(tg, 2025, None)
    assert p.loc["A", "off_sack_rate"] == pytest.approx(0.025)
    assert p.loc["A", "games"] == 2


def test_defense_side_uses_opponent_rows():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 20, 4, 2.0)])
    p = season_profile(tg, 2025, None)
    assert p.loc["B", "def_sack_rate"] == pytest.approx(0.2)
    assert p.loc["B", "def_epa_per_db"] == pytest.approx(0.1)


def test_before_order_excludes_same_and_later_games():
    tg = _tg([(2025, "regular", w, w, "A", "B", 10, s, 0.0) for w, s in ((1, 0), (2, 5), (3, 5))])
    p = season_profile(tg, 2025, before_order=2)
    assert p.loc["A", "off_sack_rate"] == 0 and p.loc["A", "games"] == 1


def test_postseason_sees_full_regular_season():
    tg = _tg([(2025, "regular", 14, 1, "A", "B", 10, 2, 0.0), (2025, "postseason", 1, 2, "A", "C", 10, 0, 0.0)])
    p = season_profile(tg, 2025, before_order=101)
    assert p.loc["A", "games"] == 1 and p.loc["A", "off_sack_rate"] == pytest.approx(0.2)


def test_havoc_attached_to_defense():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 10, 1, 0.0)])
    p = season_profile(tg, 2025, None, havoc={"B": 0.07})
    assert p.loc["B", "def_front7_havoc"] == 0.07 and math.isnan(p.loc["A", "def_front7_havoc"])


def test_zero_dropbacks_gives_nan_not_error():
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 0, 0, 0.0)])
    p = season_profile(tg, 2025, None)
    assert math.isnan(p.loc["A", "off_sack_rate"]) and math.isnan(p.loc["A", "off_epa_per_db"])


def _two_seasons():
    return _tg([(2024, "regular", 5, 1, "A", "B", 10, 4, 0.0),   # last season: A sack rate 0.4
                (2025, "regular", 1, 2, "A", "B", 10, 0, 0.0),   # this season week 1: 0.0
                (2025, "regular", 2, 3, "A", "B", 10, 0, 0.0),
                (2025, "regular", 1, 4, "N", "B", 10, 2, 0.0)])  # N is new to FBS in 2025


def test_week1_uses_last_season_only():
    p, early = blended_profile(_two_seasons(), 2025, 1, "regular", None, None)
    assert early and p.loc["A", "off_sack_rate"] == pytest.approx(0.4)


def test_week3_blend_weights():
    p, early = blended_profile(_two_seasons(), 2025, 3, "regular", None, None)
    assert early and p.loc["A", "off_sack_rate"] == pytest.approx(0.2)  # w = 0.5


def test_new_fbs_team_uses_this_season_only():
    p, _ = blended_profile(_two_seasons(), 2025, 3, "regular", None, None)
    assert p.loc["N", "off_sack_rate"] == pytest.approx(0.2)


def test_week5_is_not_early():
    p, early = blended_profile(_two_seasons(), 2025, 5, "regular", None, None)
    assert not early and p.loc["A", "off_sack_rate"] == 0


def test_postseason_is_not_early():
    _, early = blended_profile(_two_seasons(), 2025, 1, "postseason", None, None)
    assert not early


def test_fbs_only_drops_games_involving_non_fbs_teams():
    from cfbm.team_stats import fbs_only
    tg = _tg([(2025, "regular", 1, 1, "A", "B", 10, 0, 0.0),
              (2025, "regular", 2, 2, "A", "FCS U", 10, 9, 0.0),      # A's offense vs FCS defense
              (2025, "regular", 2, 2, "FCS U", "A", 10, 9, 0.0),      # FCS offense vs A's defense
              (2024, "regular", 1, 3, "B", "N", 10, 0, 0.0)])         # N was FCS in 2024
    out = fbs_only(tg, {2025: {"A", "B", "N"}, 2024: {"A", "B"}})
    assert out["game_id"].tolist() == [1]
    p = season_profile(out, 2025, None)
    assert p.loc["A", "off_sack_rate"] == 0 and p.loc["A", "games"] == 1


# ---- Slice 4: run phase ----
from cfbm.team_stats import team_game_run, team_game_stats
from cfbm.tiers import assign_tiers


def _rush(i, y, ppa=0.1, off="A", deff="B", down=1, distance=10, ytg=50, ptype="Rush", **kw):
    r = _raw(i, ptype, ppa, off=off, deff=deff, down=down, distance=distance, **kw)
    r.update(yardsGained=y, yardsToGoal=ytg)
    return r


def _run(raw):
    return team_game_run(normalize_plays(raw, 2025, "regular", 2)).set_index("team")


def test_line_second_level_and_open_field_yards():
    a = _run([_rush(1, -2), _rush(2, 3), _rush(3, 7), _rush(4, 15)]).loc["A"]
    assert a["runs"] == 4
    assert a["line_yards_sum"] == pytest.approx(-2.4 + 3 + 5.5 + 7)
    assert a["second_level_sum"] == pytest.approx(0 + 0 + 2 + 5)
    assert a["open_field_sum"] == pytest.approx(5)
    assert a["stuffs"] == 1


def test_power_chances_and_conversions():
    a = _run([_rush(1, 2, down=3, distance=1), _rush(2, 0, down=1, distance=2, ytg=2),
              _rush(3, 1, down=2, distance=1), _rush(4, 1, down=4, distance=2)]).loc["A"]
    assert a["power_n"] == 3 and a["power_conv"] == 1


def test_sacks_passes_and_garbage_are_not_runs():
    raw = [_rush(1, 4), _rush(2, -7, ptype="Sack"), _rush(3, 9, ptype="Pass Reception", off_score=40, period=4),
           _rush(4, 30, off_score=40, period=4), _rush(5, 2, ptype="Rushing Touchdown", ytg=2)]
    a = _run(raw).loc["A"]
    assert a["runs"] == 2


def test_team_game_stats_keeps_run_only_teams():
    raw = [_rush(1, 4), _rush(2, 5, off="B", deff="A"),
           {**_raw(3, "Pass Reception", 0.3), "yardsGained": 8, "yardsToGoal": 40}]
    tg = team_game_stats(normalize_plays(raw, 2025, "regular", 2)).set_index("team")
    assert tg.loc["B", "runs"] == 1 and tg.loc["B", "dropbacks"] == 0
    assert tg.loc["A", "runs"] == 1 and tg.loc["A", "dropbacks"] == 1


def _rtg(team, opp, gid, wk, runs=10, line=40.0, stuffs=2, pn=0, pc=0, s=2025):
    row = _tg([(s, "regular", wk, gid, team, opp, 10, 0, 0.0)]).iloc[0].to_dict()
    row.update(runs=runs, rush_epa_sum=0.5, rush_epa_n=runs, line_yards_sum=line, second_level_sum=5.0,
               open_field_sum=3.0, stuffs=stuffs, power_n=pn, power_conv=pc)
    return row


def test_profile_rates_and_no_power_chances_is_nan():
    tg = pd.DataFrame([_rtg("A", "B", 1, 1), _rtg("A", "C", 2, 2, line=20.0, stuffs=0, pn=4, pc=3),
                       _rtg("B", "A", 1, 1, stuffs=5)])
    p = season_profile(tg, 2025, None)
    assert p.loc["A", "off_line_yards"] == pytest.approx(3.0)
    assert p.loc["A", "off_stuff_rate"] == pytest.approx(0.1)
    assert p.loc["A", "off_power_success"] == pytest.approx(0.75)
    assert math.isnan(p.loc["B", "off_power_success"])
    assert p.loc["A", "def_stuff_rate"] == pytest.approx(0.5)
    assert p.loc["A", "off_runs"] == 20


def test_fewer_stuffs_ranks_higher_for_offense_and_more_for_defense():
    tg = pd.DataFrame([_rtg("A", "B", 1, 1, stuffs=1), _rtg("B", "A", 1, 1, stuffs=6)])
    r = assign_tiers(season_profile(tg, 2025, None), {"A", "B"})
    assert r.loc["A", "off_stuff_rate_rank"] == 1 and r.loc["A", "def_stuff_rate_rank"] == 1  # A stuffed 6 of B's 10 runs


def test_early_season_blends_run_columns():
    tg = pd.DataFrame([_rtg("A", "B", 1, 1, line=20.0, s=2024), _rtg("A", "B", 11, 1, line=40.0, s=2025)])
    tg.loc[1, "order"] = 1
    p, early = blended_profile(tg, 2025, 3, "regular", None, None)
    assert early and 2.0 < p.loc["A", "off_line_yards"] < 4.0
