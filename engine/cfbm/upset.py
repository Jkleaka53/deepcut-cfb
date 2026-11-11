"""Upset Watch: the game where the pros are most likely wrong. DraftKings' odds (margin removed) give the
pros' win chance; our internal pregame chance comes from the edge score's linear model and NEVER leaves the
engine. Only DraftKings' own whole-number percentages are published."""

from __future__ import annotations

import math

import numpy as np

PROVIDER = "DraftKings"


def _raw(ml: float) -> float:
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def book_prob(game_lines: dict, provider: str = PROVIDER) -> float | None:
    """Home win chance from one provider's moneylines, with the bookmaker's margin removed."""
    for line in game_lines.get("lines") or []:
        if line.get("provider") != provider:
            continue
        h, a = line.get("homeMoneyline"), line.get("awayMoneyline")
        if h is None or a is None:
            return None
        rh, ra = _raw(h), _raw(a)
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


def our_prob(model: dict, pre, home: str, away: str, neutral: bool) -> float | None:
    """Our pregame home win chance from the edge score's linear model. Internal only, never exported."""
    from cfbm.edge_score import overall_linear

    lin = overall_linear(model, pre, home, away, neutral)
    return None if lin is None else 1 / (1 + math.exp(-lin))


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
