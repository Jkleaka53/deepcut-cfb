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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cfbm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Pull CFBD data and write the site's JSON")
    b.add_argument("--out", type=Path, default=ROOT / "web" / "public" / "data")
    args = parser.parse_args(argv)

    client = CfbdClient(api_key(), ENGINE / ".cache")
    t0 = time.time()
    build(client, args.out)
    print(f"done in {time.time() - t0:.0f}s, CFBD calls made: {client.calls_made}")


if __name__ == "__main__":
    main()
