# SDD ledger — plan: docs/superpowers/plans/2026-11-10-swing-factors.md
Pre-flight: T1 FEATURES/team_games/pregame/training_frame → T2 train(frame, tg); T2 model dict keys (mean, sd, sideMean, sideSd, importance, proven, volatility) → T3 swing_block; T3 keyRows/drivers → T5 export → T6 web types. Consistent.
Ruling: owner skipped questions; plan calls are mine, listed in plan "My calls" — cost: owner may want different factors
Task 1: complete (commits 75692f4..28a5e0b, tests: bash -c 'cd engine && uv run pytest -q' → 183 passed in 0.43s)
Task 2: fixed real bug found on real data: side advantage was off − def_allowed; correct is off + def_allowed (same stat seen from both sides) — test_side_advantage_adds_what_the_defense_allows RED→GREEN; univariate pass_ppa coef 0.11 → 0.85
Task 2: Ruling: proven requires a clearly POSITIVE effect (lo > 0) and importance = max(0, coef) — pass_sr got −0.26 from overlap with pass_ppa/sd_sr; showing "better passing success hurts" would be nonsense — cost: pass_sr never becomes a driver/KEY
Task 2: real fit 2015-2025 (no 2020), 5,613 games: proven = sd_sr .77, pass_ppa .34, pd_sr .34, explosive .25; home .28
Task 2: complete (commits 28a5e0b..0509f77, tests: bash -c 'cd engine && uv run pytest -q' → 189 passed in 0.42s)
Task 3: complete (commits 0509f77..fd5cab2, tests: bash -c 'cd engine && uv run pytest -q' → 194 passed in 0.42s)
Task 4: Ruling: big-stadium storyline uses venue capacity (not attendance history) and counts only road/neutral games — a team's own 100k home games would inflate it — cost: wording/sample
Task 4: complete (commits fd5cab2..fbb15af, tests: bash -c 'cd engine && uv run pytest -q' → 201 passed in 0.42s)
Task 5: Ruling: unit-row flag named isKey (plan said key) — UnitRow already has a "key" id field — cost: none
Task 5: Ruling: model is retrained each build from cached past seasons (no stored model); build(model=...) lets tests inject one — cost: ~some seconds per CI run
Task 5: note: export test world has no advanced stats, so the injected-model test exercises the "too early" path end to end; driver ranking is covered by test_swing
Task 5: fixed empty-frame list-filter trap in _swing (and hardened training_frame) — test_swing_block_with_injected_model RED→GREEN, test_empty_input_gives_empty_frame
Task 5: complete (commits fbb15af..0e83b7d, tests: bash -c 'cd engine && uv run pytest -q' → 205 passed in 0.54s)
Task 6: Ruling: swing card sits first in Preview, above The edge; overall line added to The edge card, passing lines kept below it with a footnote — cost: layout
Task 6: Ruling: what-if (QB Out) does not recompute swing factors — they are team-level stats, not QB splits — cost: a user may expect them to move
Task 6: observed: most home chips read "Key: Early-down success" (the model's strongest stat) — honest but repetitive; left for owner
Task 6: Playwright 375 light/dark: Missouri at Georgia 5 drivers + 2 storylines, Overall: Slight edge Georgia, 2 KEY badges, 67/67 week-11 chips Key, scrollWidth 360
Task 6: complete (commits 0e83b7d..3985037, tests: bash -c 'cd web && npm test 2>&1 | grep -E 'Tests '' →       Tests  156 passed (156))
Final review: opus, 1 Critical, 3 Important, 7 Minor
Final: fixed CRITICAL postseason leak (adv order from week, not dates) — export _Data now remaps self.adv via d.orders; training uses apply_orders(game_orders) — test_postseason_priors_follow_dates_not_ids + test_apply_orders_remaps_by_game RED→GREEN
Final: fixed favors/edge mismatch + gap floor never filtering — favors from rank gap, "even" pairs dropped — test_even_matchups_are_not_drivers_and_favors_matches_ranks RED→GREEN (first version passed pre-fix; rewritten with shifted baseline to reproduce); real data: even 0, favors-worse 0, drivers per game now 0-5 spread
Final: fixed (re-graded Minor→Important: whole build crash) NaN stat in _pct_rank — test_missing_stat_for_a_team_skips_that_factor RED→GREEN
Final: fixed (re-graded Minor→Important: wrong on every bowl page) bowl "bye" storyline — test_bowl_games_get_no_rest_storyline RED→GREEN; engine 210/210, web 156/156
Final: minor (deferred): _priors divides by count incl. NaN stats (latent; no NaNs in data)
Final: minor (deferred): percentile ranks include teams with 1-2 FBS games early in the season
Final: minor (deferred): swing_block's neutral param unused
Final: minor (deferred): volatility computed with FCS rows included
Final: minor (deferred): _qb_story picks sentence by substring; export 'top' expression hard to read
