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
