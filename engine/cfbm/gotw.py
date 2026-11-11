"""Game of the Week: two strong teams in a close game (owner 2026-11-10).

Score = 0.5 x strength + 0.5 x closeness (both 0-100).
  strength  = mean national percentile of every passing AND running row, both offenses and both defenses
  closeness = 100 - 10 x the overall edge score (0-10); for a game with no edge score (no Elo rating),
              100 - mean absolute offense-minus-defense gap across both passing matchups
Rankings never enter the score; they decide eligibility: games with BOTH teams in the AP Top 25 first,
then games with one, then any game (see pick).
"""

from __future__ import annotations

TOP_THIRD = 200 / 3
W_STRENGTH, W_CLOSE = 0.5, 0.5


def _sides(sec: dict) -> tuple[float | None, float | None, float | None]:
    pairs = [(r["offense"].get("pct"), r["defense"].get("pct")) for u in sec.get("units", []) for r in u["rows"]]
    off = [o for o, _ in pairs if o is not None]
    dfn = [d for _, d in pairs if d is not None]
    both = [o - d for o, d in pairs if o is not None and d is not None]
    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    return mean(off), mean(dfn), mean([abs(x) for x in both])


def _strength(secs: list[dict]) -> float | None:
    xs = [r[side].get("pct") for sec in secs for key in ("units", "runUnits") for u in sec.get(key) or []
          for r in u["rows"] for side in ("offense", "defense")]
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def score(m: dict) -> float | None:
    secs = m.get("sections") or []
    if len(secs) != 2:
        return None
    vals = [_sides(s) for s in secs]
    if any(v is None for trio in vals for v in trio):
        return None
    strength = _strength(secs)
    edge = ((m.get("swing") or {}).get("overallEdge") or {}).get("score")
    closeness = 100 - 10 * edge if edge is not None else 100 - sum(g for _, _, g in vals) / 2
    return W_STRENGTH * strength + W_CLOSE * closeness


def _drivers(m: dict) -> list:
    return ((m.get("swing") or {}).get("drivers")) or []


def why(m: dict) -> str:
    secs = m["sections"]
    strong = []
    for s in secs:
        o, d, _ = _sides(s)
        if o is not None and o >= TOP_THIRD:
            strong.append(f"{s['offenseTeam']}'s passing game")
    for s in secs:
        _, d, _ = _sides(s)
        if d is not None and d >= TOP_THIRD:
            strong.append(f"{s['defenseTeam']}'s pass defense")
    parts = []
    if len(strong) == 4:
        parts.append("Both passing games and both pass defenses rank in the top third of FBS.")
    elif strong:
        names = strong[0] if len(strong) == 1 else ", ".join(strong[:-1]) + " and " + strong[-1]
        parts.append(f"{names[0].upper()}{names[1:]} {'ranks' if len(strong) == 1 else 'rank'} in the top third of FBS.")
    edges = []
    for s in secs:
        e = s.get("edge") or "even"
        if e.endswith("defense"):
            edges.append(f"{s['defenseTeam']}'s defense has the edge when {s['offenseTeam']} passes")
        elif e.endswith("offense"):
            edges.append(f"{s['offenseTeam']}'s passing game has the edge over {s['defenseTeam']}'s defense")
    if edges:
        parts.append("; ".join(edges) + ".")
    else:
        parts.append("Neither side has a clear edge on paper.")
    n = len(_drivers(m))
    if n:
        parts.append(f"{n} swing factor{'s' if n != 1 else ''} in play.")
    return " ".join(parts)


def _week(g: dict) -> str:
    return "post" if g.get("seasonType") == "postseason" else str(g.get("week"))


def _tier(g: dict) -> int:
    return (g.get("homeRank") is not None) + (g.get("awayRank") is not None)


def pick(matchups: list[dict]) -> dict[str, dict]:
    """Best score per week among the week's highest ranking tier that has a scored game: both teams in
    the AP Top 25, else one, else any. A strong-on-paper game against an unranked or weak-schedule
    opponent shouldn't headline the week."""
    best: dict[str, tuple[tuple[int, float], dict]] = {}
    for m in matchups:
        sc = score(m)
        if sc is None:
            continue
        wk = _week(m["game"])
        key = (_tier(m["game"]), sc)
        if wk not in best or key > best[wk][0]:
            best[wk] = (key, m)
    return {wk: {"id": int(m["game"]["id"]), "why": why(m)} for wk, (_, m) in best.items()}
