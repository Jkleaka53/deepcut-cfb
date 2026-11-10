# Spike notes: what free CFBD data supports (2026-11-10)

Pulled 2025 regular-season play-by-play for weeks 5–7 (56,188 plays), week 5 passing box scores, advanced game and season stats, QB PPA by game, 2024 postseason games, and the 2025 FBS team list. 11 API calls total. Raw output is in `engine/spike/out/report.txt`, which is git-ignored scratch.

## Answers

1. **Dropback play types.** These are `Pass Reception` (10,825), `Pass Incompletion` (7,141), `Passing Touchdown` (1,001), `Sack` (1,093), `Pass Interception Return` (381), `Interception Return Touchdown` (53) and `Interception` (2). Rush types are `Rush` and `Rushing Touchdown`. PPA is missing on only 14 of 6,782 dropbacks in week 5.
2. **Scores are post-play.** A touchdown row already includes the touchdown's points: the TD shows 7-0 while the play before it showed 0-0. Pre-play margin is therefore taken from the previous play in the same game, ordered by play id, with scores tracked as home/away and then oriented to the offense. The first play of a game has a margin of 0.
3. **Pressure can't be estimated from play text.** Only 2 of 21,556 rush plays mention a scramble, all from 1 team. 0 of 7,141 incompletions mention a throwaway. Intentional grounding appears 51 times, mostly as `Penalty` plays. **Decision: `PRESSURE_PROXY = "front_seven_havoc"`.** Pass rush is measured by sack rate, front-seven havoc and passing-down sack rate. Pass protection is measured by sack rate allowed. The site and README say pressure isn't directly measured.
4. **CPOE is not available on the free tier.** `/stats/game/advanced` and `/ppa/players/games` have no completion-probability fields. **Decision: `CPOE_AVAILABLE = False`.** It is left out, and the README says so.
5. **Front-seven havoc is available.** `/stats/season/advanced` has `defense.havoc = {total, frontSeven, db}`, e.g. `{0.107, 0.063, 0.044}`.
6. **Player IDs survive transfers.** John Mateer is athlete `4915980` at Washington State in 2024 (primary passer in 12 games) and at Oklahoma in 2025 (11 games). Career splits can join on athlete id.
7. **Postseason week numbering.** Every 2024 postseason game has `week = 1` with `seasonType = postseason`, which matches `order_key` (100 + week).
8. **Call budget.** One `/plays` call returns a whole week (about 18k plays). The initial backfill for 2021–2026 is about 16 play calls + 16 box calls + 2 games + 1 FBS list + 1 season advanced per season, roughly 36 × 6 ≈ 220 calls. Weekly refreshes after that take about 5 calls. This fits comfortably under the free tier.

Other useful facts: box score passing stats are `C/ATT, YDS, AVG, TD, INT, QBR` with athlete `id` and `name`. Games carry `neutralSite`, `venue`, `attendance`, `homeClassification`/`awayClassification`, `completed` and `startDate`. There are 136 FBS teams in 2025.
