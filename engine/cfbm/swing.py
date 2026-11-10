"""What could swing this game: factor = importance x gap x volatility, plus the overall weighted edge.
Words only: never a win probability or a margin."""

from __future__ import annotations

import pandas as pd

from cfbm.swing_data import DIRECTION, FEATURES, MIN_PRIOR, side_advantage
from cfbm.units import edge

LABEL = {k: label for k, _, _, label in FEATURES}
GAP_FLOOR = 0.25
MAX_DRIVERS = 5
PASS_ROW = {"pass_ppa": "epa_per_db", "pd_sr": "pd_epa", "pass_sr": "success_rate"}
CUES = {
    "sd_sr": "Watch {off} on first and second down. If it stays on schedule, this edge is playing out.",
    "pass_ppa": "Watch {off}'s first few drives through the air. Chunk completions mean this edge is real.",
    "pd_sr": "Watch {off} on 3rd-and-long. Conversions there flip drives.",
    "explosive": "One or two big plays by {off} could decide it.",
    "pass_sr": "Watch how often {off}'s passes keep it on schedule.",
    "rush_ppa": "Watch whether {off} can run for chunks against {def}.",
    "rush_sr": "Watch whether {off}'s runs keep it ahead of the chains.",
    "line_yards": "Watch {off}'s line against {def}'s front on early runs.",
    "stuff": "Watch how often {def} stuffs {off}'s runs at the line.",
}


def _pct_rank(series: pd.Series, team: str, direction: int) -> tuple[int, float] | None:
    vals = series.dropna() * direction
    if team not in vals.index:
        return None
    n = len(vals)
    rank = int(1 + (vals > vals[team]).sum())
    return rank, (n - rank) / (n - 1) * 100 if n > 1 else 50.0


def swing_block(model: dict, home: str, away: str, pre: pd.DataFrame, neutral: bool) -> dict:
    feats = model["features"]
    short = [t for t in (away, home) if t not in pre.index or pre.loc[t, "games"] < MIN_PRIOR]
    if short:
        return {"drivers": [], "overallEdge": None, "keyRows": {home: [], away: []},
                "note": f"Too early in the season: {' and '.join(short)} {'has' if len(short) == 1 else 'have'} "
                        f"fewer than {MIN_PRIOR} games against FBS teams."}
    n = len(pre)
    cands, weighted, weight = [], 0.0, 0.0
    for off, dfn in ((away, home), (home, away)):
        for k, f in feats.items():
            if f["importance"] <= 0:
                continue
            d = DIRECTION[k]
            adv = side_advantage(pre.loc[off, f"off_{k}"], pre.loc[dfn, f"def_{k}"], k)
            z = (adv - f["sideMean"]) / f["sideSd"]
            o, df = _pct_rank(pre[f"off_{k}"], off, d), _pct_rank(pre[f"def_{k}"], dfn, -d)
            if o is None or df is None or pd.isna(adv):
                continue
            (off_rank, off_pct), (def_rank, def_pct) = o, df
            gap = off_pct - def_pct
            weighted += f["importance"] * (gap if off == home else -gap)
            weight += f["importance"]
            band = (edge(off_pct, def_pct) or "even").split("-")[0]
            # One measure decides both the badge and the team: the rank gap between the two units.
            if not f["proven"] or abs(z) < GAP_FLOOR or band == "even":
                continue
            cands.append({"key": k, "label": LABEL[k], "offense": off, "defense": dfn, "edge": band,
                          "favors": off if gap > 0 else dfn, "offRank": off_rank, "defRank": def_rank, "of": n,
                          "cue": CUES[k].format(off=off, **{"def": dfn}),
                          "score": round(f["importance"] * abs(z) * f["volatility"], 4)})
    drivers = sorted(cands, key=lambda c: -c["score"])[:MAX_DRIVERS]
    overall = None
    if weight:
        g = weighted / weight
        band = edge(50 + g / 2, 50 - g / 2)
        overall = {"edge": band.split("-")[0] if band else "even", "team": None if band in (None, "even") else (home if g > 0 else away)}
    key_rows = {home: [], away: []}
    for dr in drivers:
        if dr["key"] in PASS_ROW and PASS_ROW[dr["key"]] not in key_rows[dr["offense"]]:
            key_rows[dr["offense"]].append(PASS_ROW[dr["key"]])
    note = None if drivers else "No big swing factors: these teams match up evenly on the stats the model trusts."
    return {"drivers": drivers, "overallEdge": overall, "keyRows": key_rows, "note": note}
