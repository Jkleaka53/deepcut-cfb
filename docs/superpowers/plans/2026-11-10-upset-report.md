# Upset Watch backtest (2026-11-10)

Leave-one-season-out over 2015-2025 minus 2020: our pregame chance from a model that never saw that season; pros' chance from the spread (consensus, else first provider), curve fitted on the history (k = 8.5). 5613 games with model + spread.

## As planned: biggest gap each week (book underdog at or under 45%)

| | Result | Bar | Verdict |
|---|---|---|---|
| Underdog covered | 45.7% (129 weeks) | > 50% | FAIL |
| Underdog won outright | 21.7% | > book's 23.7% | FAIL |

Per season the cover rate swings from 7.7% (2017) to 69.2% (2016): one pick a week is mostly noise. Control: all at-or-under-45% underdogs cover 49.4%.

## Where there is a signal: close games

All candidates by gap size: cover 47-53% in every bin, no steady trend. By spread size (gap > 0.10):

| Spread | Games | Covered | Won | Book said |
|---|---|---|---|---|
| 3.5 or less | 324 | 52.8% | 49.4% | 41.6% |
| 4 to 7.5 | 525 | 52.2% | 36.0% | 32.9% |
| 8 to 14.5 | 613 | 47.0% | 19.4% | 20.7% |
| 15+ | 519 | 48.0% | 7.3% | 8.7% |

Close games (spread 7.5 or less), underdogs we like by more than 10 points vs all others:

| | Games | Won | Covered | Book said |
|---|---|---|---|---|
| We like the dog (gap > 0.10) | 849 | 41.1% | 52.4% | 36.2% |
| Others | 1667 | 36.5% | 48.5% | 37.1% |

One weekly pick restricted to close games: cover 49.6%, won 37.6% vs book 35.9% (125 weeks): still under the cover bar.

## 2026 (DraftKings moneylines, full-history model)

- Wk 10 top: North Carolina at UConn (DK UConn 28%; UNC won 38-21), Georgia State at App State (Georgia State won 39-23 as the dog), Florida State at Boston College (FSU won 31-24).
- Wk 11 top: Michigan at Oregon (DK Michigan 22%), Georgia Southern at Georgia State, Western Michigan at Akron.

## Verdict

Fails the spec's bar as planned. The pros' line is hard to beat; our model adds a modest, real-looking edge only in close games (+5 points of outright wins over 849 games), and a single weekly pick is too noisy to show it.

## Iteration (owner chose "Iterate first"): opponent-adjusted stats

Each team's season-to-date stat is adjusted for its opponents, as of kickoff only: offense stat minus w x (that opponent's defense average so far minus the league average so far), and the mirror for defense. Same leave-one-season-out test.

| w | Model log loss | Favored won | Weekly pick covered | Won outright | Book said |
|---|---|---|---|---|---|
| raw (0) | 0.5764 | 70.2% | 45.7% | 21.7% | 23.7% |
| 0.4 | 0.5662 | 71.1% | 51.6% | 32.8% | 25.5% |
| 0.6 | 0.5632 | 71.0% | 57.8% | 34.4% | 26.0% |
| 0.8 | **0.5626** | 70.8% | 52.7% | 31.0% | 25.9% |
| 1.0 | 0.5647 | 70.2% | 54.4% | 29.6% | 25.2% |
| 1.4 | 0.5777 | 69.2% | 48.8% | 27.2% | 24.8% |

w chosen by model log loss alone (0.8), not by the upset numbers. Every w from 0.4 to 1.0 passes both bars. At 0.8 the planned weekly pick PASSES: covered 52.7% (> 50%), won outright 31.0% vs book 25.9%.

Adopting it changes the swing model, so it moves the live edge scores, swing factors and Game of the Week closeness as well; the Even/Big cutoffs would be re-run.

## Adopted (owner: site-wide, 2026-11-10)

Real code (config.OPP_ADJUST = 0.8) reproduces the experiment: weekly pick covered 52.7%, won outright 31.0% vs book 25.9% (129 weeks). PASS.
2026 wk 11 pick: Michigan at Oregon (DraftKings: Michigan 22%).

Edge label lines re-checked on the adjusted model: the backtest suggests Even < 2.5 / Big >= 6.5 (Big 85.3% over 2015-2025), but on 2026's 283 finished games Big at 6.5 was right 100/128 (78%) vs 55/65 (85%) at 8.0. Owner kept 2.0 / 8.0. With 2/8, 2026 labels move little (Even 105 to 115, Slight 331 to 318, Big 101 to 104; favored team flipped in 2 of 537).
