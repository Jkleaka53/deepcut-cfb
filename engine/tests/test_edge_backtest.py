import numpy as np
import pandas as pd

from cfbm.edge_backtest import band_table, held_out, pick_cutoffs
from tests.test_swing_model import _synthetic

def _multi():
    fr, tg = _synthetic(n=2000)
    fr["season"] = 2016 + (fr["game_id"] % 4)
    return fr, tg


def test_held_out_one_row_per_game():
    fr, tg = _multi()
    out = held_out(fr, tg, keys=["a", "b"])
    assert len(out) == len(fr)
    assert out["score"].between(0, 10).all()
    assert set(out["favored_won"].unique()) <= {0, 1}


def test_pick_cutoffs_monotone():
    rng = np.random.default_rng(5)
    score = rng.uniform(0, 10, 20000)
    df = pd.DataFrame({"season": 2019, "score": score,
                       "favored_won": (rng.random(20000) < 0.5 + score / 20).astype(int)})
    slight, big = pick_cutoffs(df)
    assert slight < big
    assert (slight * 2).is_integer() and (big * 2).is_integer()


def test_band_table_counts_sum():
    rng = np.random.default_rng(6)
    df = pd.DataFrame({"season": 2019, "score": rng.uniform(0, 10, 500), "favored_won": rng.integers(0, 2, 500)})
    rows = band_table(df, 2.0, 7.0)
    assert [r["band"] for r in rows] == ["even", "slight", "clear"]
    assert sum(r["games"] for r in rows) == 500


def test_even_cutoff_uses_local_rate_not_cumulative():
    rng = np.random.default_rng(8)
    score = rng.uniform(0, 10, 40000)
    p = np.where(score < 2, 0.5, 0.75)
    df = pd.DataFrame({"season": 2019, "score": score, "favored_won": (rng.random(40000) < p).astype(int)})
    slight, _ = pick_cutoffs(df)
    assert slight == 2.0
