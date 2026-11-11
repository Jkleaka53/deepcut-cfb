"""Command line: `uv run python -m cfbm.cli build --out ../web/public/data`."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from cfbm.cfbd_client import CfbdClient
from cfbm.export import build

ENGINE = Path(__file__).resolve().parents[1]
ROOT = ENGINE.parent


def api_key() -> str:
    key = os.environ.get("CFBD_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("CFBD_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("CFBD_API_KEY is not set (env var or .env at the repo root).")
    return key


def edge_cutoffs(client) -> None:
    from cfbm import config
    from cfbm.edge_backtest import band_table, held_out, pick_cutoffs
    from cfbm.export import training_data

    data = training_data(client, config.TRAIN_SEASONS)
    if data is None:
        sys.exit("Not enough training games.")
    df = held_out(*data)
    slight, big = pick_cutoffs(df)
    print(f"games {len(df)}  EDGE_SCORE_SLIGHT = {slight}  EDGE_SCORE_BIG = {big}")
    for r in band_table(df, slight, big):
        print(r)
    for c in (1, 2, 3, 4, 5, 6, 7, 8, 9):
        lo, hi = df[df["score"] < c], df[df["score"] >= c]
        print(f"score<{c}: n={len(lo)} fav={lo['favored_won'].mean():.3f} | score>={c}: n={len(hi)} fav={hi['favored_won'].mean():.3f}")


def shootout_backtest(client, check_season: int = 2026, check_week: int = 10,
                      check_id: int = 401856856) -> None:
    from cfbm import config
    from cfbm.export import shootout_inputs
    from cfbm.plays import game_orders
    from cfbm.shootout import SHOOT_COLS, fit, game_score, predicted_total, training_rows
    from cfbm.shootout_backtest import held_out, weekly_hits
    from cfbm.swing_data import apply_orders, pregame

    tg, games, fbs = shootout_inputs(client, config.TRAIN_SEASONS)
    rows = training_rows(tg, games, fbs)
    df = held_out(rows)
    print(f"held-out games {len(df)}")
    for col in ("score_min", "score_sum"):
        print(col, weekly_hits(df, col))
    model = fit(rows)
    tg2, games2, fbs2 = shootout_inputs(client, (check_season,))
    orders = game_orders(list(games2.values()))
    tg2 = apply_orders(tg2, orders)
    f = fbs2[check_season]
    tg2 = tg2[tg2["team"].isin(f) & tg2["opponent"].isin(f)]
    week = [g for g in games2.values() if g.get("week") == check_week and g.get("seasonType") == "regular"
            and g["homeTeam"] in f and g["awayTeam"] in f]
    scored = []
    for g in week:
        pre = pregame(tg2, check_season, orders.get(g["id"], 0), SHOOT_COLS)
        args = (model, pre, g["homeTeam"], g["awayTeam"], bool(g.get("neutralSite")))
        mn, sm = game_score(*args), predicted_total(*args)
        if mn is not None:
            total = (g.get("homePoints") or 0) + (g.get("awayPoints") or 0)
            scored.append((g["id"], g["awayTeam"], g["homeTeam"], total, mn, sm))
    for i, col in ((4, "min"), (5, "sum")):
        ranked = sorted(scored, key=lambda r: -r[i])
        pos = next((n + 1 for n, r in enumerate(ranked) if r[0] == check_id), None)
        print(f"{check_season} wk {check_week} by {col}: game {check_id} ranks {pos} of {len(ranked)}; top 5:")
        for r in ranked[:5]:
            print(f"   {r[1]} at {r[2]}  actual total {r[3]}")
    by_total = sorted(scored, key=lambda r: -r[3])[:5]
    print("actual top 5 totals:", [(r[1], r[2], r[3]) for r in by_total])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cfbm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Pull CFBD data and write the site's JSON")
    b.add_argument("--out", type=Path, default=ROOT / "web" / "public" / "data")
    sub.add_parser("edge-cutoffs", help="Backtest the edge score and print Even/Slight/Big cutoffs")
    sub.add_parser("shootout-backtest", help="Backtest Shootout of the Week (leave one season out)")
    args = parser.parse_args(argv)

    client = CfbdClient(api_key(), ENGINE / ".cache")
    if args.cmd == "edge-cutoffs":
        edge_cutoffs(client)
        return
    if args.cmd == "shootout-backtest":
        shootout_backtest(client)
        return
    t0 = time.time()
    build(client, args.out)
    print(f"done in {time.time() - t0:.0f}s, CFBD calls made: {client.calls_made}")


if __name__ == "__main__":
    main()
