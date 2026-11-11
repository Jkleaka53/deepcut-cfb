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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cfbm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Pull CFBD data and write the site's JSON")
    b.add_argument("--out", type=Path, default=ROOT / "web" / "public" / "data")
    sub.add_parser("edge-cutoffs", help="Backtest the edge score and print Even/Slight/Big cutoffs")
    args = parser.parse_args(argv)

    client = CfbdClient(api_key(), ENGINE / ".cache")
    if args.cmd == "edge-cutoffs":
        edge_cutoffs(client)
        return
    t0 = time.time()
    build(client, args.out)
    print(f"done in {time.time() - t0:.0f}s, CFBD calls made: {client.calls_made}")


if __name__ == "__main__":
    main()
