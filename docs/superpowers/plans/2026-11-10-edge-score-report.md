# Edge score report (2026 finished games: 562)

| Label | Old games | New games | Old: favored won | New: favored won | Old: decided by 21+ | New: decided by 21+ |
|---|---|---|---|---|---|---|
| Even | 182 | 55 | n/a (0/0) | n/a (0/0) | 25% | 31% |
| Slight | 137 | 218 | 69% (95/137) | 62% (136/218) | 32% | 22% |
| Big | 19 | 65 | 89% (17/19) | 85% (55/65) | 58% | 54% |

Section labels that lean against most of their own table: 0 of 1437 (0%).

## Spec examples

- Missouri at Ole Miss (wk 7, final 3-31): old even; new slight Ole Miss 3.7
- Florida at Missouri (wk 5, final 17-45): old even; new slight Florida 2.2
- Texas A&M at LSU (wk 4, final 6-35): old even; new clear LSU 8.2

## First run (Big at 7.5, section lines on the new score)

## Same games, old vs new

- On the 153 games the old label called, the new score always picks the same team, and the favored team won 72% under both.
- On the 130 games the old label called "Even", the new score picks a side, and that side won 62%.
- New Big by week: weeks 4-6, 38 games, 79%; week 7 on, 50 games, 82%. Held-out 2015-2025 backtest: 85%.

## Pass bar (plan Task 5 Step 4)

- New Even covers fewer 21+ blowouts by share: FAIL (31% vs 25%; Even shrank from 182 to 55 games)
- New Big favored win rate >= 85%: FAIL on 2026 (81%); PASS on held-out 2015-2025 (85.3%)
- More Big games than the old 40 Clear: PASS (88 finished 2026 games)
- Section contradictions <= 5%: FAIL (12%)

## Owner decisions after the first run (2026-11-10)

- Big line raised from 7.5 to 8.0 (2026 Big games: 85% of 65, was 81% of 88).
- Passing/running lines stay table-based (side_edge over the rows shown); the 0-10 score drives only the overall meter and the home chip. Section contradictions are now 0.
