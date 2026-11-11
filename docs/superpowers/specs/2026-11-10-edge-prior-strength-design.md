# Edge score: prior team strength and scoring margin (design, 2026-11-10)

## Why

An audit on 2026-11-10 measured the edge model against the closing spread on every FBS-vs-FBS game from 2015 to 2025 (no 2020), each season scored by a model that never saw it.

| | Picks the winner | Log loss |
|---|---|---|
| Current model | 70.8% | 0.5626 |
| Market (spread, k = 8.7) | 72.6% | 0.5315 |

The model is well calibrated but knows nothing about a team beyond this season's nine play-by-play stats. Two inputs it lacks explain most of the gap:

- Prior team strength. Adding the pregame Elo difference alone: log loss 0.5463, winners 72.3%, 52% of the gap closed.
- Scoring margin to date (per game, capped at 28). Alone: 0.5570, 18% of the gap. With Elo: 0.5459, 54%.

It also scores only 72% of games, because it needs three prior FBS games per team: 98% of weeks 1 to 4 have no edge score. On those games an Elo-only model picks 74.3% of winners (log loss 0.5203) against the market's 76.3% (0.4774).

Things that did not help and are out: last-three-games form, rest days, extra play-by-play stats (overall points added, power success, second-level and open-field yards, pace), stronger regularization.

## Goals

1. The edge model reads two new inputs: pregame Elo difference and capped scoring margin to date.
2. Every FBS-vs-FBS game gets an edge score, including weeks 1 to 4 (owner decision).
3. Held-out accuracy improves over the current model, measured the same way as the audit.

## Non-goals

- No visual change to the site. Same 0-10 meter, same Even / Slight / Big labels, same swing-factor pulldowns (owner decision).
- Nothing on the site says or implies it competes with oddsmakers (owner decision). The market is a private yardstick inside backtests only.
- No new CFBD endpoints. Elo comes on the `/games` rows already fetched (`homePregameElo`, `awayPregameElo`); verified 2026-11-10 that all 562 completed and all 199 upcoming 2026 FBS games carry both, week 1 included.
- No change to the Shootout model.

## Anti-goals

- Publishing our win %, predicted margin, the model, or the Elo and margin inputs in any JSON. The existing tests that enforce this stay green; add the two new inputs to what they forbid.
- Any stat from a game leaking into that game's own features. Elo must be the pregame value; margin uses only games before kickoff.
- Showing Elo or scoring margin as a swing factor. Swing drivers stay the nine matchup stats, with ranks and shown numbers on real (unadjusted) stats as today.

## Design

### Inputs

- `elo`: home pregame Elo minus away pregame Elo, from the game row. A game missing either value gets no edge score (expected: none among FBS games).
- `margin`: for each team, mean of (points for minus points against, clipped to plus or minus 28) over its FBS-vs-FBS games this season before kickoff; feature is home minus away.
- The nine existing opponent-adjusted stat differences, unchanged in definition (`OPP_ADJUST` 0.8).

### One model for every week

Train one logistic regression on all decided FBS-vs-FBS games in `TRAIN_SEASONS`, early weeks included, on: intercept, home field, the nine stat differences, `elo`, `margin`.

Thin samples are handled by shrinking, not by dropping the game:

- Each team's season-to-date values (the nine stats and margin) are pulled toward the league average by `n / (n + k)`, where `n` is the team's prior FBS games. With zero games the team sits at league average, so the game is scored by Elo and home field alone.
- `k` is chosen once by held-out log loss over all games (builder's call on the grid; audit hint: on weeks 5+ only, k of 1 to 2 was marginally best and k up to 3 did no harm). Record the chosen value in `config.py` with the numbers, like `OPP_ADJUST`.
- Where the opponent adjustment cannot be computed for an early game (an opponent with no earlier games), fall back to the unadjusted value for that game. Builder may choose a better fallback if it tests better.

`MIN_PRIOR` stops gating the edge score. It keeps gating the swing-factor card: with fewer than three games a team's stat ranks are not meaningful, so that card keeps its current "fewer than 3 games" message while the edge meter and home chip now show a score.

### Two fits: the swing card keeps its own (my call, follows from "no visual change")

The swing-factor card (drivers, `proven`, `importance`, `sideMean` / `sideSd`, `matchupWinRate`, home-page key factor, Upset Watch's `backs_dog` / `why_text`) keeps reading a nine-stat-only fit, trained exactly as today: games with three or more prior games per team, unshrunk values, no Elo, no margin. Only the edge score (meter, home chip, Game of the Week closeness, Upset Watch's internal chance) reads the new model. So the engine holds two fits: `train` as it is for the card, and a new edge fit. Card output for a given game should not change; a test should pin that.

### Upset Watch scope (my call)

Upset Watch stays out of games where either team has fewer than three prior FBS games, as today, even though those games now have an edge score: its "why" needs swing drivers. Add the explicit filter in `upset_picks`, since the edge score no longer does it implicitly.

### Score and labels

- The 0-10 score stays a percentile of the absolute linear score against training games; the scale is rebuilt from the new model over all training games.
- Even / Slight / Big cutoffs are re-run with `cfbm.cli edge-cutoffs` and are the owner's pick (gate 3).

### Knock-on effects (expected, not bugs)

- Live edge scores and some labels move.
- Game of the Week closeness uses the edge score, so some picks change; Shootout and Upset Watch picks follow because they skip the Game of the Week id. Rebuild data after the model change.
- Upset Watch's internal chance comes from the same linear model, so it changes too (gate 2).
- `web/lib/swing.ts` mirrors `EDGE_SLIGHT` / `EDGE_BIG`; keep in sync if the cutoffs change.

## Gates (hard stops: show the owner the numbers, wait for his answer)

1. **Model.** Leave-one-season-out, 2015-2025 minus 2020, against the current model on the same games. Report log loss and winner picks for: all games; weeks 5+ (the 5613 the current model scores, target at or below about 0.546); weeks 1 to 4 (must beat nothing-shown, and should be near the Elo-only 0.5203 or better). Include the market line for reference and the by-season table. Fail if weeks 5+ is not better than 0.5626.
2. **Upset Watch.** Re-run `cfbm.cli upset-backtest` on the new model, judged on the same games as the current bar (both teams with three or more prior games); show the all-weeks number for reference only. Current bar: weekly underdog covers more than 50% and wins outright more often than the book says (now 52.7%, 31.0% vs 25.9%). The audit suggests this may fail, because the better model disagrees with the market less (large disagreements fell from 607 games to 203, against-the-spread record on those about 50%). If it fails, the owner chooses: keep Upset Watch on the current nine-stat model (two models in the engine), or change its rule. Do not pick for him.
3. **Cutoffs.** Show the `edge-cutoffs` table on the new model plus 2026 to date at the suggested and the current (2.0 / 8.0) cutoffs. Owner picks.

No web or published-data change before all three gates are answered.

## How the audit numbers were measured (so gate 1 is comparable)

- Game set: FBS-vs-FBS games with a decided result, `TRAIN_SEASONS`; 7791 games. Every one has a spread (consensus, else first provider), so no game is dropped for the market comparison.
- "Weeks 5+" in this document means the 5613 games the current model scores (three or more prior FBS games per team, all nine stats present). It reproduces `edge_backtest.held_out` exactly (0.5626).
- "Weeks 1 to 4" means the other 2178 games (2166 are calendar weeks 1 to 5; 12 are later games after thin schedules).
- Market chance: `1 / (1 + exp(spread / k))`, k = 8.7 fitted by log loss on all 7791 games.
- Elo-only 0.5203 / 74.3%: fitted leave-one-season-out on the unscored games only, on the 1722 of them that also had a prior-season stat value (so 2015 and 2021 are missing). Treat it as a rough reference, not a bar; gate 1 should report Elo-only on the full 2178 alongside the new model.
- Scoring margin in the audit used FBS-vs-FBS games only, clipped to plus or minus 28 per game, unshrunk.
- The audit scripts are throwaway and not in the repo. The plan's first task adds a reproducible `cfbm.cli` backtest command that prints these tables, and confirms the 0.5626 / 0.5315 baseline before changing anything.

## Constraints

- Not for gambling: unchanged rules; the only published win % remains DraftKings' own on Upset Watch.
- Stats strictly before kickoff; FCS games excluded; postseason ordered by date.
- Backtests run on cached data; a live build stays at about 11 CFBD calls.
- Never push while a refresh run is in progress; pushes need the owner's "done" each time.
- No en or em dashes in site copy; no animations.

## Left to the builder

- Shrink grid and exact fallback for early-game opponent adjustment.
- Whether margin is computed in `swing_data.py` or a small new module; how Elo reaches `training_frame` and `overall_linear`.
- Test layout. Existing counts: engine 309, web 213.

## Caveat to carry into the plan

CFBD's Elo is someone else's rating and is computed by them; we trust that `PregameElo` on historical rows is the value before that game. The builder should sanity-check this once (a team's pregame Elo for game N+1 should equal its postgame Elo for game N), and stop and report if it does not hold.
