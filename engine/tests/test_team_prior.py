import pandas as pd
import pytest

from cfbm import team_prior
from cfbm.team_prior import PRIOR_KEYS, add_to_frame, diffs, load


class _Client:
    def __init__(self):
        self.calls = []

    def get(self, path, params, *, cacheable=True):
        self.calls.append((path, params["year"], cacheable))
        if path == "/talent":
            return [{"year": params["year"], "team": "A", "talent": 900.0}, {"year": params["year"], "team": "B", "talent": 600.5}]
        if path == "/player/returning":
            return [{"season": params["year"], "team": "A", "percentPPA": 0.4},
                    {"season": params["year"], "team": "B", "percentPPA": 0.7},
                    {"season": params["year"], "team": "C", "percentPPA": None}]
        return []


def test_load_reads_talent_and_returning_production_per_season():
    c = _Client()
    p = load(c, [2024, 2025], live_season=2025)
    assert p[2024] == {"talent": {"A": 900.0, "B": 600.5}, "ret": {"A": 0.4, "B": 0.7}}
    assert ("/talent", 2024, True) in c.calls and ("/talent", 2025, False) in c.calls  # the live season is never cached
    assert ("/player/returning", 2025, False) in c.calls


def test_diffs_are_home_minus_away_and_zero_when_a_team_is_missing():
    p = {"talent": {"A": 900.0, "B": 600.5}, "ret": {"A": 0.4, "B": 0.7}}
    assert diffs(p, "A", "B") == {"talent": pytest.approx(299.5), "ret": pytest.approx(-0.3)}
    assert diffs(p, "A", "Nobody") == {"talent": 0.0, "ret": 0.0}
    assert diffs(None, "A", "B") == {k: 0.0 for k in PRIOR_KEYS}


def test_add_to_frame_adds_one_column_per_prior():
    games = {1: {"homeTeam": "A", "awayTeam": "B"}, 2: {"homeTeam": "B", "awayTeam": "Nobody"}}
    fr = pd.DataFrame({"game_id": [1, 2], "season": [2024, 2024]})
    out = add_to_frame(fr, games, {2024: {"talent": {"A": 900.0, "B": 600.5}, "ret": {"A": 0.4, "B": 0.7}}})
    assert list(out["f_talent"]) == pytest.approx([299.5, 0.0])
    assert list(out["f_ret"]) == pytest.approx([-0.3, 0.0])
    assert "f_talent" not in fr  # the input frame is left alone


def test_team_prior_never_reaches_published_files():
    assert team_prior.__doc__ and "internal" in team_prior.__doc__.lower()
