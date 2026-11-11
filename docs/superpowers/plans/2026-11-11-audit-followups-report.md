# Audit follow-ups 1-4: backtest report (2026-11-11)

Owner asked for the four follow-ups from the 2026-11-10 edge audit, in order, and said "just start".
Every number is held out by season (each season scored by a model fitted on the others), 2015-2025 minus 2020.
Market = closing spread converted to a win chance (k = 8.5); it is a private yardstick only.

## 1. Garbage-time filter on /stats/game/advanced (`excludeGarbageTime=true`) -- DROPPED

| Model | Raw (current) | Garbage time removed |
|---|---|---|
| Edge model, all 7791 games | 72.3% winners, log loss 0.5404 | 72.2%, 0.5404 |
| Nine-stat model, 5613 games | 70.8%, 0.5626 | 70.9%, 0.5642 |
| Upset rule (weekly pick) | cover 52.7%, won 31.0% vs book 25.9% (129 wk) | cover 55.1%, won 32.3% vs 26.3% (127 wk) |
| Shootout top-3 hits | 29 of 118 | 25 of 118 |

No model got better on log loss; the upset cover bump is within noise (about +-4.4 points on 127 weeks).

## 2. Roster talent (247 composite) + returning production (percentPPA) -- SHIPPED

| Model | Before | With both |
|---|---|---|
| Edge model, all games | 72.3%, 0.5404 | 72.7%, 0.5321 |
| Edge model, weeks 1-4 (2154 games) | 73.6%, 0.5215 | 75.7%, 0.5044 |
| Upset model, 5613 games | 70.8%, 0.5626 | 71.1%, 0.5554 |
| Upset rule | cover 52.7%, won 31.0% vs 25.9% | cover 54.0%, won 38.1% vs 28.2% (126 wk) |

Talent alone and returning production alone each helped; both together helped most.
The edge model with both still fails the upset rule (cover 50.8%, won 34.7% vs 30.5%), so Upset Watch keeps
its own model (nine stats + talent + returning). The swing-factor card stays on the nine stats (talent is not a
matchup stat). Per season the new upset model won outright more often than the old one in 6 of 10 seasons
(tied 2016, 2023, 2025; worse 2021). Cost: 2 CFBD calls per build (live season fetched fresh).

## 3. Turnovers + special teams -- DROPPED

Built from /drives (1 call per season, not ~160): season-to-date turnover margin per game, average starting
field position (own minus opponent's), field-goal rate (pulled toward 75%). On top of item 2:

| Added | Edge model | Upset model / rule |
|---|---|---|
| none | 72.7%, 0.5321 | 0.5554, cover 54.0% |
| turnovers | 73.1%, 0.5316 | 0.5557, cover 54.0% |
| field position | 72.7%, 0.5322 | 0.5529, cover 50.4% |
| FG rate | 72.8%, 0.5323 | 0.5554, cover 57.9% (log loss flat: luck) |
| all three | 73.1%, 0.5318 | 0.5530, cover 53.2% |

Gains are noise-sized, and field position hurt the upset pick.

## 4. Opponent-adjusted Shootout model -- DROPPED

| Adjustment w | Corr. with actual total | Mean miss (pts) | Top-3 hits |
|---|---|---|---|
| 0 (current) | 0.346 | 13.53 | 29 / 118 |
| 0.5 | 0.355 | 13.49 | 30 / 118 |
| 0.8 | 0.350 | 13.51 | 27 / 118 |
| 1.0 | 0.341 | 13.56 | 27 / 118 |

## What the shipped change moved (2026 data, rebuilt 2026-11-11)

- Game of the Week: 5 of 14 weeks, including week 11 Wake Forest at SMU -> Texas at LSU.
- Upset Watch: 5 of 9 weeks (weeks 5, 6, 7, 8, 10); week 11 stays Georgia Southern at Georgia State (edge 2.7 -> 3.4).
- Shootout: no week changed.
- Upcoming games: 28 of 200 changed favored team or went to/from even; 36 changed label.
