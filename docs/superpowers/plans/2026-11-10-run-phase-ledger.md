# SDD ledger — plan: docs/superpowers/plans/2026-11-10-run-phase.md
Pre-flight: T2 consumes T1 profile columns (off_/def_ rush_epa, line_yards, stuff_rate, power_success, second_level, open_field) — consistent; T3 consumes T2 runUnits/runEdge/runBiggestGap — consistent
Task 1: Ruling: test fixes only (rank test asserted wrong team; garbage test lacked a pre-play score) — the code matched the plan — cost if wrong: none
Task 1: complete (commits 00a3b77..aff82c3, tests: uv run pytest -q → 217 passed in 0.62s)
Task 1: Ruling: plan's team_games renamed team_game_stats — swing_data.team_games already imported in export, shadowing broke 21 tests — cost if wrong: none
Task 2: complete (commits aff82c3..d11ec02, tests: uv run pytest -q → 222 passed in 0.64s)
Task 2: Ruling: new row format "yds" (yards per carry, 1 decimal) — line/second-level/open-field are yards, not pct/epa — cost if wrong: web formatting only
Task 3: complete (commits d11ec02..ba353dc, tests: npx vitest run →    Duration  815ms (transform 497ms, setup 0ms, collect 1.54s, tests 232ms, environment 1.37s, prepare 1.00s))
Task 3: Ruling: runView(section) re-uses every passing helper on the run tables instead of parallel run* helpers — less code, same behavior — cost if wrong: none
Task 3: Ruling: GOTW stays passing-only (its 'why' text names passing units) — cost if wrong: GOTW ignores run strength
Final review: opus, 0 Critical, 1 Important, 6 Minor
Final: fixed kneel-downs counted as runs — test_kneel_downs_are_not_runs RED→GREEN, suite 224/224
Final: fixed (re-graded Minor→Important: home chip most often named the least reliable stat) power_success off the home Edge chip — test_home_chip_skips_short_yardage RED→GREEN, suite 224/224; web 170/170
Final: minor (deferred): edge card footnote says "passing and running" even for old JSON without runUnits (none in built data)
Final: minor (deferred): fumbled runs excluded from run stats (consistent with strip-sacks on pass side)
Final: minor (deferred): outer merge adds rare 0-dropback team-games (2 in cache) to split game counts
Final: minor (deferred): 3rd/4th-down rushes with distance <= 0 (48 in cache) count as power conversions
Final: minor (deferred): no fixture for a team present with 0 runs and NaN rates (real data verified)
