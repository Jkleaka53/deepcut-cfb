"""Game of the Week: strong passing units on both sides, with a close edge picture.

Score = 0.5 x strength + 0.35 x closeness + 0.15 x swing (all 0-100; swing = drivers / 5).
  strength  = mean national percentile of the four sides (each passing offense, each pass defense)
  closeness = 100 - mean absolute offense-minus-defense gap across both passing matchups
Rankings never enter the score; they only decide which games are eligible (see pick).
"""

from __future__ import annotations

TOP_THIRD = 200 / 3
W_STRENGTH, W_CLOSE, W_SWING = 0.5, 0.35, 0.15
MAX_DRIVERS = 5


def _sides(sec: dict) -> tuple[float | None, float | None, float | None]:
    pairs = [(r["offense"].get("pct"), r["defense"].get("pct")) for u in sec.get("units", []) for r in u["rows"]]
    off = [o for o, _ in pairs if o is not None]
    dfn = [d for _, d in pairs if d is not None]
    both = [o - d for o, d in pairs if o is not None and d is not None]
    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    return mean(off), mean(dfn), mean([abs(x) for x in both])


def score(m: dict) -> float | None:
    secs = m.get("sections") or []
    if len(secs) != 2:
        return None
    vals = [_sides(s) for s in secs]
    if any(v is None for trio in vals for v in trio):
        return None
    strength = sum(o + d for o, d, _ in vals) / 4
    closeness = 100 - sum(g for _, _, g in vals) / 2
    swing = 100 * min(len(_drivers(m)), MAX_DRIVERS) / MAX_DRIVERS
    return W_STRENGTH * strength + W_CLOSE * closeness + W_SWING * swing


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


def _ranked(g: dict) -> bool:
    return g.get("homeRank") is not None or g.get("awayRank") is not None


def pick(matchups: list[dict]) -> dict[str, dict]:
    """Best score per week. Games with an AP Top 25 team are the only candidates when the week has any:
    a strong-on-paper Group of 5 game built on a weak schedule shouldn't headline the week."""
    weeks_with_ranked = {_week(m["game"]) for m in matchups if _ranked(m["game"]) and score(m) is not None}
    best: dict[str, tuple[float, dict]] = {}
    for m in matchups:
        if _week(m["game"]) in weeks_with_ranked and not _ranked(m["game"]):
            continue
        sc = score(m)
        if sc is None:
            continue
        wk = _week(m["game"])
        if wk not in best or sc > best[wk][0]:
            best[wk] = (sc, m)
    return {wk: {"id": int(m["game"]["id"]), "why": why(m)} for wk, (_, m) in best.items()}
