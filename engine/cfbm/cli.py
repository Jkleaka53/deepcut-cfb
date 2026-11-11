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


def _edge_held(client):
    """(held-out edge scores for the training seasons, the edge training frame)."""
    from cfbm import config, edge_model
    from cfbm.edge_backtest import held_out
    from cfbm.export import edge_training_frame

    fr = edge_training_frame(client, config.TRAIN_SEASONS)
    if fr is None:
        sys.exit("Not enough training games.")
    return held_out(fr, keys=edge_model.EDGE_KEYS, fit=edge_model.train), fr


def _season_scores(client, model: dict, season: int):
    """Edge scores for one season's finished games from a fitted edge model: (frame with lin/score/favored_won, tables)."""
    import numpy as np

    from cfbm import edge_model
    from cfbm.edge_backtest import frame_linear
    from cfbm.edge_score import to_score
    from cfbm.export import edge_training_inputs

    tg, games, fbs = edge_training_inputs(client, (season,))
    tables = edge_model.pregame_tables(tg, games, fbs)
    fr = edge_model.frame(tg, games, fbs, tables=tables)
    lin = frame_linear(model, fr, edge_model.EDGE_KEYS)
    won = fr["home_win"].to_numpy(int)
    fr = fr.assign(lin=lin, score=[to_score(v, model["scale"]["overall"]) for v in lin],
                   favored_won=np.where(lin >= 0, won, 1 - won))
    return fr, tables, games, fbs


def edge_cutoffs(client, check_season: int = 2026) -> None:
    from cfbm import config, edge_model
    from cfbm.edge_backtest import band_table, pick_cutoffs

    df, fr = _edge_held(client)
    slight, big = pick_cutoffs(df)
    print(f"games {len(df)}  EDGE_SCORE_SLIGHT = {slight}  EDGE_SCORE_BIG = {big}")
    pairs = [(slight, big), (config.EDGE_SCORE_SLIGHT, config.EDGE_SCORE_BIG)]
    for sl, bg in pairs:
        print(f"history at {sl} / {bg}:", band_table(df, sl, bg))
    for c in (1, 2, 3, 4, 5, 6, 7, 8, 9):
        lo, hi = df[df["score"] < c], df[df["score"] >= c]
        print(f"score<{c}: n={len(lo)} fav={lo['favored_won'].mean():.3f} | score>={c}: n={len(hi)} fav={hi['favored_won'].mean():.3f}")
    live, *_ = _season_scores(client, edge_model.train(fr), check_season)
    for sl, bg in pairs:
        print(f"{check_season} finished games ({len(live)}) at {sl} / {bg}:", band_table(live, sl, bg))
    for label, part in (("early", live[~live["scored_before"]]), ("weeks 5+", live[live["scored_before"]])):
        print(f"{check_season} {label} at {pairs[1][0]} / {pairs[1][1]}:", band_table(part, *pairs[1]))


def _history(client):
    """Games, lines and FBS sets for the training seasons (cached)."""
    from cfbm import config, fetch

    games, lines, fbs = {}, {}, {}
    for y in config.TRAIN_SEASONS:
        fbs[y] = fetch.fbs_teams(client, y)
        games.update({g["id"]: g for g in fetch.games(client, y, False)})
        lines.update({ln["id"]: ln for ln in fetch.lines(client, y, False)})
    return games, lines, fbs


def edge_audit(client) -> None:
    """Held-out edge model against the closing spread, plus a check that pregame Elo is really pregame."""
    from cfbm import config
    from cfbm.edge_audit import compare, elo_continuity, market_frame
    from cfbm.edge_backtest import held_out
    from cfbm.export import training_data

    data = training_data(client, config.TRAIN_SEASONS)
    if data is None:
        sys.exit("Not enough training games.")
    games, lines, fbs = _history(client)
    market = market_frame(games, lines, fbs)
    held = held_out(*data)
    print(f"market games {len(market)}  spread scale k={market.attrs.get('k')}")
    print("current model, games it scores:", compare(held, market))
    for s in sorted(held["season"].unique()):
        print(" ", s, compare(held, market, held["season"] == s))

    from cfbm import edge_model
    from cfbm.edge_model import EDGE_KEYS
    from cfbm.export import edge_training_inputs

    tg, eg, efbs = edge_training_inputs(client, config.TRAIN_SEASONS)
    tables = edge_model.pregame_tables(tg, eg, efbs)
    best = None
    print("edge model (nine stats + Elo + capped margin), by shrink strength k:")
    for k in (0, 1, 2, 3, 5):
        fr = edge_model.frame(tg, eg, efbs, k, tables=tables)
        h = held_out(fr, keys=EDGE_KEYS, fit=edge_model.train)
        allg, late, early = compare(h, market), compare(h, market, h["scored_before"]), compare(h, market, ~h["scored_before"])
        print(f"  k={k}: all {allg}\n        weeks 5+ {late}\n        early {early}")
        if best is None or allg["modelLogLoss"] < best[1]:
            best = (k, allg["modelLogLoss"], h, fr)
    k, _, h, fr = best
    print(f"best k by all-games log loss: {k} (config.EDGE_SHRINK_K = {config.EDGE_SHRINK_K})")
    print("edge model on exactly the current model's games:", compare(h, market, h["game_id"].isin(held["game_id"])))
    elo = held_out(fr, keys=["elo"], fit=lambda rows: edge_model.train(rows, keys=["elo"]))
    print("Elo and home field only, early games:", compare(elo, market, ~elo["scored_before"]))
    print("Elo and home field only, all games:", compare(elo, market))
    for s in sorted(h["season"].unique()):
        print(" ", s, "all", compare(h, market, h["season"] == s), "| early", compare(h, market, (h["season"] == s) & ~h["scored_before"]))
    for y in config.TRAIN_SEASONS:
        gs = [g for g in games.values() if g["season"] == y]
        print(f"  elo continuity {y}: FBS-vs-FBS {elo_continuity(gs, fbs[y]):.4f}  (all rows {elo_continuity(gs):.4f})")


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


def upset_backtest(client, check_season: int = 2026, check_weeks: tuple[int, ...] = (10, 11)) -> None:
    import numpy as np

    from cfbm import edge_model
    from cfbm.swing_data import MIN_PRIOR
    from cfbm.upset import book_prob, fit_spread_scale, gap, spread_of
    from cfbm.upset_backtest import covered, join, summary, weekly_picks

    held, fr = _edge_held(client)
    games, lines, _ = _history(client)
    sp, hw = [], []
    for gid, ln in lines.items():
        g, s_ = games.get(gid), spread_of(ln)
        if g and s_ is not None and g.get("homePoints") is not None and g.get("awayPoints") is not None \
                and g["homePoints"] != g["awayPoints"]:
            sp.append(s_)
            hw.append(int(g["homePoints"] > g["awayPoints"]))
    k = fit_spread_scale(np.array(sp), np.array(hw))
    # Judged on the games Upset Watch can pick: both teams with MIN_PRIOR games. All games shown for reference.
    df = join(held[held["scored_before"]], lines, games, k)
    picks = weekly_picks(df)
    print(f"spread scale k={k}  games with model+spread {len(df)} (both teams {MIN_PRIOR}+ games)")
    print("ALL", summary(picks))
    for s_, p in picks.groupby("season"):
        print(s_, summary(p))
    print("reference, every week incl. early games:", summary(weekly_picks(join(held, lines, games, k))))
    dogs = []
    for r in df.itertuples():
        bh = r.book_home
        dog = "home" if bh <= 0.45 else "away" if 1 - bh <= 0.45 else None
        if dog:
            dogs.append(covered(dog, r.spread, r.home_margin))
    print(f"control: all <=45% underdogs n={len(dogs)} cover={np.mean(dogs):.3f}")
    for lo, hi in ((0, 3.5), (3.5, 7.5), (7.5, 14.5), (14.5, 99)):
        rows = []
        for r in df[(df["spread"].abs() > lo) & (df["spread"].abs() <= hi)].itertuples():
            gp = gap(r.our_home, r.book_home)
            if gp and gp[1] > 0.10:
                won = r.home_margin > 0 if gp[0] == "home" else r.home_margin < 0
                rows.append((covered(gp[0], r.spread, r.home_margin), won, r.book_home if gp[0] == "home" else 1 - r.book_home))
        if rows:
            a = np.array(rows, float)
            print(f"  spread {lo}-{hi}, gap>0.10: n={len(a)} cover={a[:, 0].mean():.3f} won={a[:, 1].mean():.3f} book={a[:, 2].mean():.3f}")

    live, _, g26, _ = _season_scores(client, edge_model.train(fr), check_season)
    from cfbm import fetch
    l26 = {ln["id"]: ln for ln in fetch.lines(client, check_season, False)}
    live = live[live["scored_before"]].set_index("game_id")
    for wk in check_weeks:
        cands = []
        for gid, r in live.iterrows():
            g = g26[gid]
            if g.get("week") != wk or g["seasonType"] != "regular":
                continue
            bh = book_prob(l26.get(gid, {}))
            gp = None if bh is None else gap(1 / (1 + np.exp(-r["lin"])), bh)
            if gp:
                cands.append((gp[1], gp[0], g, bh))
        print(f"{check_season} wk {wk} (finished games only): {len(cands)} candidates; top 3:")
        for gv, dog, g, bh in sorted(cands, key=lambda c: -c[0])[:3]:
            print(f"   {g['awayTeam']} at {g['homeTeam']}  dog={dog}  DK home {round(100*bh)}%  gap {gv:.2f}  {g['awayPoints']}-{g['homePoints']}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cfbm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Pull CFBD data and write the site's JSON")
    b.add_argument("--out", type=Path, default=ROOT / "web" / "public" / "data")
    sub.add_parser("edge-cutoffs", help="Backtest the edge score and print Even/Slight/Big cutoffs")
    sub.add_parser("edge-audit", help="Held-out edge model against the closing spread")
    sub.add_parser("shootout-backtest", help="Backtest Shootout of the Week (leave one season out)")
    sub.add_parser("upset-backtest", help="Backtest Upset Watch (leave one season out)")
    args = parser.parse_args(argv)

    client = CfbdClient(api_key(), ENGINE / ".cache")
    if args.cmd == "edge-cutoffs":
        edge_cutoffs(client)
        return
    if args.cmd == "edge-audit":
        edge_audit(client)
        return
    if args.cmd == "shootout-backtest":
        shootout_backtest(client)
        return
    if args.cmd == "upset-backtest":
        upset_backtest(client)
        return
    t0 = time.time()
    build(client, args.out)
    print(f"done in {time.time() - t0:.0f}s, CFBD calls made: {client.calls_made}")


if __name__ == "__main__":
    main()
