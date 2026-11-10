"""Win-loss record going into a game: overall and in conference (all opponents, FCS included)."""

from __future__ import annotations

INDEPENDENT = "FBS Independents"


def record(games: list[dict], team: str, before_order: int, orders: dict[int, int]) -> dict:
    wins = losses = conf_w = conf_l = 0
    conference = None
    for g in games:
        side = "home" if g["homeTeam"] == team else "away" if g["awayTeam"] == team else None
        if side is None:
            continue
        conference = conference or g.get(f"{side}Conference")
        if not g.get("completed") or orders.get(g["id"], 10**6) >= before_order:
            continue
        mine, theirs = g.get(f"{side}Points"), g.get(f"{'away' if side == 'home' else 'home'}Points")
        if mine is None or theirs is None or mine == theirs:
            continue
        won = mine > theirs
        wins, losses = wins + won, losses + (not won)
        if g.get("conferenceGame"):
            conf_w, conf_l = conf_w + won, conf_l + (not won)
    if conference == INDEPENDENT:
        conference = None
    return {"wins": wins, "losses": losses, "confWins": conf_w, "confLosses": conf_l, "conference": conference}
