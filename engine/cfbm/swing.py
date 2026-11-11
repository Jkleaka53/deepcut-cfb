"""What could swing this game: factor = importance x gap x volatility, plus the overall edge score (cfbm.edge_score).
Words only: never a win probability or a margin."""

from __future__ import annotations

import pandas as pd

from cfbm.swing_data import DIRECTION, FEATURES, MIN_PRIOR, side_advantage
from cfbm.edge_score import overall_edge
from cfbm.units import edge

LABEL = {k: label for k, _, _, label in FEATURES}
GAP_FLOOR = 0.25
MAX_DRIVERS = 5
# The unit row each model feature badges as Key (passing and running rows).
KEY_ROW = {"pass_ppa": "epa_per_db", "pd_sr": "pd_epa", "pass_sr": "success_rate",
           "rush_ppa": "rush_epa", "stuff": "stuff_rate", "line_yards": "line_yards"}
# Plain-English meaning of each model stat, shown when a swing reason is opened.
MEANING = {
    "sd_sr": "How often the offense has a successful play on normal downs: every 1st down, 2nd-and-7 or shorter, and "
             "3rd or 4th-and-4 or shorter, on any set of downs in a drive (not just the first two plays). Successful "
             "means gaining half the yards needed on 1st down, 70% on 2nd, and all of it on 3rd or 4th.",
    "pd_sr": "How often the offense has a successful play when it's behind schedule: 2nd-and-8 or longer, and 3rd or "
             "4th-and-5 or longer. Successful means gaining 70% of the yards needed on 2nd down, and all of it on 3rd or 4th.",
    "pass_sr": "How often a pass play is successful: half the yards needed on 1st down, 70% on 2nd, all of it on 3rd "
               "or 4th. Sacks count as pass plays.",
    "rush_sr": "How often a run is successful: half the yards needed on 1st down, 70% on 2nd, all of it on 3rd or 4th.",
    "pass_ppa": "Points added per pass: how much the average pass play moves the offense toward scoring, based on down, "
                "distance and field position. Above zero helps the offense.",
    "rush_ppa": "Points added per run: how much the average run moves the offense toward scoring, based on down, "
                "distance and field position. Above zero helps the offense.",
    "explosive": "How big the good plays are: the average points added on the offense's successful plays. High numbers "
                 "mean chunk gains, not just steady ones.",
    "stuff": "How often a run is stopped at or behind the line of scrimmage. Lower is better for the offense, higher "
             "is better for the defense.",
    "line_yards": "Yards per carry credited to the offensive line: the first 4 yards count fully, yards 5 to 10 count "
                  "half, and losses count extra.",
}
FORMAT = {"sd_sr": "pct", "pd_sr": "pct", "pass_sr": "pct", "rush_sr": "pct", "stuff": "pct",
          "pass_ppa": "epa", "rush_ppa": "epa", "explosive": "num", "line_yards": "num"}
CUES = {
    "sd_sr": "Watch {off} on 1st down: gaining 4 or more yards keeps them out of 3rd-and-long.",
    "pd_sr": "Watch {off} on 3rd-and-5 or longer: converting there keeps drives alive.",
    "pass_sr": "Watch whether {off}'s passes gain enough to stay ahead of the chains, not just whether they're caught.",
    "pass_ppa": "Watch {off}'s first few drives through the air: completions of 15 or more yards.",
    "rush_ppa": "Watch for {off} runs of 10 or more yards against {def}.",
    "rush_sr": "Watch whether {off}'s runs gain 4 or more yards on 1st down.",
    "explosive": "Watch for {off} plays of 20 or more yards; one or two can decide it.",
    "line_yards": "Watch {off}'s runs between the tackles: 4 or more yards a carry means the line is winning.",
    "stuff": "Watch whether {off}'s runs get past the line of scrimmage against {def}.",
}
CUE_SUFFIX = " If {off} does that often, {off}'s offense is winning this matchup; if not, {def}'s defense is."
WHY = ("One of the {n} stats the model found actually decide games. Since {since}, when one team's offense or "
       "defense was ahead in this matchup (this offense against this defense), that team won {pct}% of the time.")
# A stat the model trusts can still be near a coin flip on its own (it earns its weight next to the others).
WHY_WEAK = ("One of the {n} stats the model found actually decide games. On its own it's close to a coin flip "
            "(since {since}, when one team's offense or defense was ahead in this matchup, that team won {pct}% "
            "of the time), but next to the other stats it adds real weight.")
WEAK_RATE = 0.55


def _val(v) -> float | None:
    return None if v is None or pd.isna(v) else round(float(v), 4)


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
    cands = []
    n_proven = sum(1 for f in feats.values() if f["proven"])
    since = min(model.get("seasons") or [2015])
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
            band = (edge(off_pct, def_pct) or "even").split("-")[0]
            # One measure decides both the badge and the team: the rank gap between the two units.
            if not f["proven"] or abs(z) < GAP_FLOOR or band == "even":
                continue
            cands.append({"key": k, "label": LABEL[k], "offense": off, "defense": dfn, "edge": band,
                          "favors": off if gap > 0 else dfn, "offRank": off_rank, "defRank": def_rank, "of": n,
                          "cue": (CUES[k] + CUE_SUFFIX).format(off=off, **{"def": dfn}),
                          "detail": {"meaning": MEANING[k], "format": FORMAT[k],
                                     "offValue": _val(pre.loc[off, f"off_{k}"]), "defAllows": _val(pre.loc[dfn, f"def_{k}"]),
                                     "fbsAvg": _val(pre[f"off_{k}"].mean()),
                                     "why": (WHY if f.get("matchupWinRate", 0.5) >= WEAK_RATE else WHY_WEAK).format(
                                         n=n_proven, since=since, pct=round(100 * f.get("matchupWinRate", 0.5)))},
                          "score": round(f["importance"] * abs(z) * f["volatility"], 4)})
    drivers = sorted(cands, key=lambda c: -c["score"])[:MAX_DRIVERS]
    overall = overall_edge(model, pre, home, away, neutral)
    key_rows = {home: [], away: []}
    for dr in drivers:
        if dr["key"] in KEY_ROW and KEY_ROW[dr["key"]] not in key_rows[dr["offense"]]:
            key_rows[dr["offense"]].append(KEY_ROW[dr["key"]])
    note = None if drivers else "No big swing factors: these teams match up evenly on the stats the model trusts."
    return {"drivers": drivers, "overallEdge": overall, "keyRows": key_rows, "note": note}
