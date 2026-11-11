import numpy as np
import pandas as pd

from cfbm.shootout import X_KEYS
from cfbm.shootout_backtest import held_out, weekly_hits


def _week(season, wk, totals, scores):
    return [{"season": season, "week_key": wk, "game_id": f"{season}-{wk}-{i}", "total": t, "score_min": s,
             "score_sum": s} for i, (t, s) in enumerate(zip(totals, scores))]


def test_weekly_hits_counts_top3():
    rows = _week(2019, "1", [70, 80, 40, 30, 20], [9, 1, 2, 3, 4])  # top score has 2nd-highest total: hit
    rows += _week(2019, "2", [70, 60, 50, 40, 20], [1, 2, 3, 4, 9])  # top score has the lowest total: miss
    out = weekly_hits(pd.DataFrame(rows), "score_min")
    assert out["weeks"] == 2 and out["hits"] == 1
    assert out["hitRate"] == 0.5 and abs(out["chance"] - 0.6) < 1e-9


def test_weeks_under_four_games_skipped():
    rows = _week(2019, "1", [70, 80, 40, 30, 20], [9, 1, 2, 3, 4]) + _week(2019, "2", [70, 60, 50], [1, 2, 3])
    assert weekly_hits(pd.DataFrame(rows), "score_min")["weeks"] == 1


def test_held_out_one_row_per_game():
    rng = np.random.default_rng(4)
    rows = []
    for season in (2017, 2018, 2019):
        for g in range(60):
            gid = season * 1000 + g
            pts = []
            for side in ("home", "away"):
                x = {k: float(rng.normal()) for k in X_KEYS}
                x["home"] = float(side == "home")
                p = 28 + 6 * x["x_ppa"] + float(rng.normal(0, 3))
                pts.append(p)
                rows.append({"game_id": gid, "season": season, "order": g // 10, "week_key": str(g // 10), "side": side,
                             "points": p, **x})
            for r in rows[-2:]:
                r["total"] = sum(pts)
    out = held_out(pd.DataFrame(rows))
    assert len(out) == 180
    assert out["score_min"].notna().all() and out["score_sum"].notna().all()
