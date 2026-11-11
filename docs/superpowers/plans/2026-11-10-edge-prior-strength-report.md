# Edge model with prior strength: backtest report (2026-11-10)

Leave-one-season-out over 2015-2025 minus 2020, FBS-vs-FBS games with a result (7791). Market chance from the closing spread (k = 8.7). Reproduce with `uv run python -m cfbm.cli edge-audit`.

## Gate 1: model accuracy

New model = nine opponent-adjusted stats + pregame Elo difference + scoring margin to date (capped at 28 a game) + home field, trained on every game.

| Games | New model | Current model | Elo + home only | Market |
|---|---|---|---|---|
| Weeks 5+ (the 5613 the current model scores) | 71.7%, 0.5473 | 70.8%, 0.5626 | | 72.6%, 0.5315 |
| Early games (2154 the current model cannot score) | 73.6%, 0.5215 | no score | 74.5%, 0.5194 | 76.5%, 0.4731 |
| All 7791 | 72.3%, 0.5404 | | 71.8%, 0.5445 | 73.7%, 0.5154 |

Each cell: winner picked, log loss (lower is better).

- Fail line (weeks 5+ below 0.5626): PASS at 0.5473. About half of the gap to the market on those games is closed (0.0311 to 0.0158).
- The audit's rough expectation was 0.546 and 72.3% on weeks 5+; the real model lands at 0.5473 and 71.7% because it is now fitted on early games too.
- Early games: the new model is slightly behind Elo alone (0.5215 vs 0.5194). One or two games of stats add a little noise on top of Elo.
- Coverage goes from 72% of games to 100%.

### Shrink strength

| k | All games | Weeks 5+ | Early |
|---|---|---|---|
| 0 | 0.5404 | 0.5476 | 0.5215 |
| 1 | 0.5405 | 0.5476 | 0.5219 |
| 2 | 0.5407 | 0.5478 | 0.5223 |
| 3 | 0.5410 | 0.5480 | 0.5225 |
| 5 | 0.5412 | 0.5483 | 0.5228 |

Chosen: k = 0 (lowest; all within 0.001). A team's numbers are centered on the league average and not shrunk further; a team with no games sits at the average. ("Weeks 5+" here is 5637 games: both teams with three or more prior games.)

### By season (new model, all games; winner picked, log loss)

| Season | New model | Market | Early games: new | Early: market |
|---|---|---|---|---|
| 2015 | 76.3%, 0.5020 | 78.0%, 0.4828 | 76.5%, 0.5016 | 81.2%, 0.4308 |
| 2016 | 72.8%, 0.5527 | 73.0%, 0.5447 | 78.9%, 0.4799 | 81.8%, 0.4680 |
| 2017 | 72.0%, 0.5353 | 74.9%, 0.4939 | 72.0%, 0.5190 | 77.5%, 0.4405 |
| 2018 | 73.2%, 0.5202 | 73.7%, 0.5012 | 74.3%, 0.5277 | 72.9%, 0.5124 |
| 2019 | 72.7%, 0.5183 | 74.8%, 0.4903 | 75.1%, 0.4862 | 78.3%, 0.4481 |
| 2021 | 70.0%, 0.5504 | 72.7%, 0.5250 | 72.2%, 0.5318 | 74.2%, 0.4850 |
| 2022 | 69.8%, 0.5800 | 72.3%, 0.5514 | 69.5%, 0.5909 | 74.6%, 0.5385 |
| 2023 | 73.7%, 0.5456 | 73.5%, 0.5105 | 77.0%, 0.4928 | 77.9%, 0.4300 |
| 2024 | 69.4%, 0.5600 | 70.7%, 0.5356 | 68.2%, 0.5518 | 71.3%, 0.4932 |
| 2025 | 72.8%, 0.5380 | 73.4%, 0.5185 | 72.9%, 0.5310 | 75.1%, 0.4838 |

### Elo check

Pregame Elo on a game row equals the team's postgame Elo from its previous FBS-vs-FBS game in 99.6% to 100% of cases every season, so the rating holds nothing from the game it is used for. CFBD puts an unrelated placeholder on FBS-vs-FCS rows from 2022 on; the model never reads those rows.

## Gate 1 answer

Owner: continue (2026-11-10).

## Gate 2: Upset Watch on the new model

`uv run python -m cfbm.cli upset-backtest`. Judged on games where both teams have three or more prior games (5637), one pick a week, 127 weeks.

| | New model | Current nine-stat model | Bar |
|---|---|---|---|
| Underdog covered | 47.2% | 52.7% | above 50% |
| Underdog won outright | 31.5% | 31.0% | above the book |
| Book said | 28.9% | 25.9% | |

Verdict: FAIL on the cover bar, pass on outright wins. As the audit predicted, a model that knows prior strength disagrees with the market less, and what disagreement is left is not better than the spread. All weeks including early games (reference only): covered 44.3%, won 30.4% vs book 28.8% over 158 weeks.

By season, covered: 2015 69%, 2016 50%, 2017 42%, 2018 25%, 2019 38%, 2021 38%, 2022 62%, 2023 46%, 2024 58%, 2025 43%.

All underdogs we like by more than 10 points, by spread size:

| Spread | Games | Covered | Won | Book said |
|---|---|---|---|---|
| 3.5 or less | 226 | 54.4% | 48.2% | 41.8% |
| 4 to 7.5 | 279 | 50.5% | 36.6% | 33.3% |
| 8 to 14.5 | 213 | 49.3% | 23.0% | 21.1% |
| 15+ | 107 | 48.6% | 12.1% | 9.8% |

Control: every underdog at or under 45% covers 49.4%.

## Gate 3: Even / Slight / Big cutoffs on the new model

`uv run python -m cfbm.cli edge-cutoffs`. Held-out, all 7791 games; 2026 is the 562 finished games scored by the full-history model.

| Cutoffs | | Even | Slight | Big |
|---|---|---|---|---|
| 2.0 / 8.0 (current) | 2015-2025 | 1517 games, favored won 54.0% | 4685, 71.8% | 1589, 91.3% |
| | 2026 | 106, 50.0% | 355, 73.5% | 101, 89.1% |
| 1.0 / 5.5 (backtest's suggestion) | 2015-2025 | 738, 52.0% | 3532, 63.8% | 3521, 85.0% |
| | 2026 | 50, 54.0% | 266, 63.9% | 246, 84.1% |

2026 at 2.0 / 8.0, split: early games Even 40 (57.5%), Slight 137 (79.6%), Big 47 (93.6%); weeks 5+ Even 66 (45.5%), Slight 218 (69.7%), Big 54 (85.2%).

The suggestion would label 45% of all games Big. At 2.0 / 8.0 the three labels separate more cleanly than they do today (current model, held-out: Even 53.5%, Slight 69.1%, Big 85.3%).

## Gate 2 and 3 answers

Owner (2026-11-10): Upset Watch stays on the nine-stat model; cutoffs stay 2.0 / 8.0.

## Rebuild: 2026 before and after

Local build on the edge model, 11 CFBD calls. 562 finished FBS-vs-FBS games.

| Label | Before | After | Before: favored won | After: favored won |
|---|---|---|---|---|
| Even or no score | 295 (71 Even + 224 unscored) | 106 | | 50% |
| Slight | 202 | 355 | 66% | 74% |
| Big | 65 | 101 | 85% | 89% |

- Weeks 1 to 4 (215 games that had no score): 37 Even, 131 Slight, 46 Big; one game went Big to Slight.
- Later weeks: 307 labels unchanged; Slight to Even 55, Even to Slight 71, Slight to Big 25, Big to Slight 34, Even to Big 1.
- Swing-factor drivers: unchanged in all 761 matchups with a swing card. Home-page key factors: 0 changed.
- Shootout of the Week: 0 of 10 weeks changed. Upset Watch: 0 of 9 weeks changed.
- Game of the Week changed in 6 of 14 weeks, because its closeness term reads the edge score:
  - Week 5: Alabama at Mississippi State became Florida at Missouri
  - Week 6: UCLA at Oregon became Georgia at Alabama
  - Week 7: Notre Dame at BYU became Missouri at Ole Miss
  - Week 8: Houston at Utah became Ole Miss at Texas
  - Week 11 (current): #2 Utah at #22 Arizona became #11 Wake Forest at #25 SMU (edge 0.5 vs Utah-Arizona 1.5; Wake-SMU was 2.4 before)
  - Week 12: #1 Georgia at #20 South Carolina became #24 LSU at #9 Tennessee (edge 0.5; Georgia's edge went 3.7 to 6.6)
- Preview check: a week 1 game page (North Carolina vs TCU) shows "TCU · Slight edge · 4.8" with the meter and the "fewer than 3 games" swing note; week 1 home chips show edge labels; no mention of odds outside Upset Watch's DraftKings bar. Web tests 213 passed, static build clean.
