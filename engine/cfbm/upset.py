"""Upset Watch: the game where the pros are most likely wrong. DraftKings' odds (margin removed) give the
pros' win chance; our internal pregame chance comes from the nine-stat swing model (edge_score.overall_linear,
not the edge model: Upset Watch failed its backtest on that one, owner 2026-11-10) and NEVER leaves the
engine. The why-line quotes the edge score the site shows. Only DraftKings' own whole-number percentages are published."""

from __future__ import annotations

import math

import numpy as np

PROVIDER = "DraftKings"


def _raw(ml: float | None) -> float | None:
    """American odds to a raw chance; anything under 100 in size is not a real moneyline."""
    if ml is None or abs(ml) < 100:
        return None
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def book_prob(game_lines: dict, provider: str = PROVIDER) -> float | None:
    """Home win chance from one provider's moneylines, with the bookmaker's margin removed."""
    for line in game_lines.get("lines") or []:
        if line.get("provider") != provider:
            continue
        rh, ra = _raw(line.get("homeMoneyline")), _raw(line.get("awayMoneyline"))
        if rh is None or ra is None:
            return None
        return rh / (rh + ra)
    return None


def spread_of(game_lines: dict) -> float | None:
    """Home-side spread (negative = home favored): consensus if present, else the first provider with one."""
    ls = [x for x in game_lines.get("lines") or [] if x.get("spread") is not None]
    cons = [x for x in ls if x.get("provider") == "consensus"]
    pick = cons[0] if cons else (ls[0] if ls else None)
    return None if pick is None else float(pick["spread"])


def spread_prob(spread: float, k: float) -> float:
    """Home win chance implied by a spread (backtest only)."""
    return 1 / (1 + math.exp(spread / k))


def fit_spread_scale(spreads: np.ndarray, home_win: np.ndarray) -> float:
    """Logistic scale k mapping spread to home win chance, by grid search on log loss."""
    s = np.asarray(spreads, float)
    y = np.asarray(home_win, float)
    best, best_k = math.inf, None
    for k in np.arange(5.0, 25.0001, 0.1):
        p = np.clip(1 / (1 + np.exp(s / k)), 1e-9, 1 - 1e-9)
        loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        if loss < best:
            best, best_k = loss, float(k)
    return round(best_k, 1)

DOG_MAX = 0.45


def our_prob(model: dict, pre, home: str, away: str, neutral: bool, extra: dict | None = None) -> float | None:
    """Our pregame home win chance from the Upset Watch model (export.train_upset_model). extra = the
    non-stat inputs (team_prior.diffs). Internal only, never exported."""
    from cfbm.edge_score import overall_linear

    lin = overall_linear(model, pre, home, away, neutral, extra)
    return None if lin is None else 1 / (1 + math.exp(-lin))


def own_edge(model: dict, pre, home: str, away: str, neutral: bool, extra: dict | None = None) -> dict | None:
    """The game's edge (band, team, 0-10 score) on the nine-stat model that makes the Upset Watch pick, in the
    shape edge_score.edge returns. The picked game shows this one, so the pick and the score next to it come
    from the same model (owner 2026-11-11). None when the game cannot be scored."""
    from cfbm.edge_score import band, overall_linear, to_score

    lin = overall_linear(model, pre, home, away, neutral, extra)
    if lin is None:
        return None
    score = to_score(lin, model["scale"]["overall"])
    b = band(score)
    return {"edge": b, "team": None if b == "even" else (home if lin > 0 else away), "score": score}


def gap(our_home: float, book_home: float) -> tuple[str, float] | None:
    """The book's underdog ("home"/"away") and how much more we like it, when the book gives it at most
    DOG_MAX and we give it more than the book does."""
    if book_home <= DOG_MAX:
        side, ours, book = "home", our_home, book_home
    elif 1 - book_home <= DOG_MAX:
        side, ours, book = "away", 1 - our_home, 1 - book_home
    else:
        return None
    return (side, ours - book) if ours > book else None


def odds_block(book_home: float) -> dict:
    """The only win % the site publishes: DraftKings' own, whole numbers adding to 100."""
    home = max(1, min(99, round(100 * book_home)))  # never show a sure thing
    return {"source": PROVIDER, "home": home, "away": 100 - home}


def _ord(n: int) -> str:
    from cfbm.shootout import ordinal
    return ordinal(int(n))


def backs_dog(m: dict, dog: str) -> bool:
    """A pick needs a reason that argues for the underdog: a swing factor in its favor, or our edge score
    even or leaning its way. Otherwise "Why that could be wrong" would argue for the favorite."""
    sw = m.get("swing") or {}
    if any(x.get("favors") == dog for x in sw.get("drivers") or []):
        return True
    e = sw.get("overallEdge") or {}
    return e.get("edge") == "even" or not e.get("team") or e.get("team") == dog


def why_text(m: dict, dog: str, fav: str) -> str:
    """'Why that could be wrong', in words: the underdog's strongest swing factor, then our edge score's view
    when it is even or leans the underdog."""
    sw = m.get("swing") or {}
    parts = []
    d = next((x for x in sw.get("drivers") or [] if x.get("favors") == dog), None)
    if d:
        if d["offense"] == dog:
            parts.append(f"{dog} has the edge in {d['label']}: {dog}'s offense ranks {_ord(d['offRank'])} against "
                         f"{fav}'s defense, which ranks {_ord(d['defRank'])} of {d['of']}.")
        else:
            parts.append(f"{dog} has the edge in {d['label']}: {dog}'s defense ranks {_ord(d['defRank'])} against "
                         f"{fav}'s offense, which ranks {_ord(d['offRank'])} of {d['of']}.")
    e = sw.get("overallEdge") or {}
    if e.get("edge") == "even" or not e.get("team"):
        parts.append("Our edge score has it even.")
    elif e["team"] == dog:
        parts.append(f"Our edge score leans {dog}, {e['score']} of 10.")
    # When the edge score favors the favorite, say nothing about it: the underdog can be more likely than the
    # book says and still not be favored, and the line should not argue against its own pick (owner 2026-11-10).
    return " ".join(parts)


def pick(cands: list[tuple[dict, float, dict]], skip: dict[str, set[int]]) -> dict[str, dict]:
    """Per week: the biggest gap, skipping that week's Game of the Week and Shootout pick."""
    from cfbm.gotw import _week

    best: dict[str, tuple[float, dict, dict]] = {}
    for g, gp, info in cands:
        wk = _week(g)
        if int(g["id"]) in skip.get(wk, set()):
            continue
        if wk not in best or gp > best[wk][0]:
            best[wk] = (gp, g, info)
    return {wk: {"id": int(g["id"]), "why": info["why"], "odds": info["odds"]} for wk, (_, g, info) in best.items()}
