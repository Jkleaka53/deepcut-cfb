# SDD ledger — plan: docs/superpowers/plans/2026-11-10-edge-prior-strength.md
Spec: docs/superpowers/specs/2026-11-10-edge-prior-strength-design.md (read). Branch edge-prior-strength from main c51d7c53.
Pre-flight:
- T1 compare(held[game_id, lin]) vs T3 held_out output: held_out already returns game_id+lin; consistent.
- T2 features()/shrunk_pregame vs T3 frame: same names, EDGE_KEYS feature dict keys vs frame cols f_<key>; consistent.
- T3 edge_model.train model dict vs edge_backtest.frame_linear (features[k].coef/mean/sd, home.coef, intercept): consistent.
- T3 held_out(fit=) vs T4 CLI use: consistent.
- T5 edge_score.edge(feats) vs T2 features(): consistent. T5 upset.our_prob depends on gate 2 answer (branch in brief).
Task 1: baseline reproduced: 5613 games, model 0.5626 / 70.8%, market 0.5315 / 72.6%, k 8.7.
Task 1: Ruling: elo_continuity takes fbs= and the gate is judged on FBS-vs-FBS rows — CFBD puts a placeholder Elo (pre == post, unrelated value) on FBS-vs-FCS rows from 2022 on, and the FBS chain skips them; FBS-vs-FBS continuity is 0.9957 to 1.0 every season, all-rows 0.89 to 0.93 in 2022-2025 — cost if wrong: none for the model (it only reads FBS-vs-FBS rows); an FBS team's Elo is not updated by its FCS games.
Task 1: complete (commits d03430e..6dcd9bf, tests: uv run pytest -q → 316 passed in 2.40s)
Task 2: complete (commits 6dcd9bf..227b1a4, tests: uv run pytest -q → 326 passed in 2.42s)
Task 3: Ruling: EDGE_SHRINK_K = 0.0 (plan rule: lowest all-games log loss, ties to smaller k; 0.5404 vs 0.5405..0.5412) — shrink code stays, parameterized — cost if wrong: under 0.001 log loss.
Task 3: Ruling: frame() takes tables= and edge_model.pregame_tables() is public, plus export.edge_training_inputs() — lets the k grid share one slow pass — cost if wrong: none (additive).
Task 3: Ruling: scored_before = both teams >= MIN_PRIOR games in the pregame table (5637 games); gate 1 compared on the current model's exact 5613 ids as well (0.5473 / 71.7%) — cost if wrong: 24 games of mismatch in a label.
Task 3: gate 1 numbers in docs/superpowers/plans/2026-11-10-edge-prior-strength-report.md. WAITING ON OWNER (gate 1) before Task 4.
Task 3: complete (commits 227b1a4..d49b710, tests: uv run pytest -q → 332 passed in 2.90s)
Gate 1: owner said continue.
Task 4: Ruling: 2026 band tables come from scoring 2026's finished games in the CLI (cli._season_scores) instead of a temp-dir build — the build is not wired to the edge model until Task 5 — cost if wrong: none, same model and inputs.
Task 4: gate 2 FAIL on cover (47.2% vs bar 50%; outright 31.5% vs book 28.9%). Gate 3 table in report. WAITING ON OWNER (gates 2 and 3) before Task 5.
Task 4: complete (commits d49b710..1f8d545, tests: uv run pytest -q → 332 passed in 2.93s)
Gates 2+3: owner chose "Upset Watch stays on the nine-stat model" and cutoffs stay 2.0 / 8.0. So in Task 5: upset.our_prob and edge_score.overall_linear stay as they are; only the MIN_PRIOR filter is added to upset_picks.
Task 5: Ruling: Upset Watch's chance stays on the nine-stat model (owner), but backs_dog and why_text read the DISPLAYED edge score (edge model) — the why-line says "Our edge score leans X, n of 10" and must match the meter on the page — cost if wrong: the candidate filter differs slightly from the backtested rule (the backtest never modeled backs_dog).
Task 5: Ruling: team_margins skips a game with completed == False — a game in progress carries points but no result; affects only a build run mid-game — cost if wrong: none for finished games.
Task 5: Ruling: edge_score.overall_edge removed, overall_linear kept (Upset Watch reads it); build() param is edge_model, matchup() param is edge_mdl (the module name is taken inside export.py) — cost if wrong: a rename.
Task 5: Ruling: test fixture's Elo-less game is id 2 (not 5) so the Upset fixture still yields a pick — cost if wrong: none.
Task 5: note: I ran `git checkout cfbm/export.py` to undo a mutation check and it reverted the uncommitted task 5 wiring; reapplied from the same script, suite green (339).
Task 5: complete (commits 1f8d545..6dd0ca6, tests: uv run pytest -q → 339 passed in 3.92s)
Task 6: complete (commits 6dd0ca6..9afe3fd, tests: uv run pytest -q → 339 passed in 4.05s)
Final review: fresh reviewer (fable). Owner said "done" before it returned; main pushed at 9afe3fd0, Vercel success. Fixes on branch edge-review-fixes (NOT pushed, needs fresh OK).
Final: fixed upset-backtest pointed at a model Upset Watch does not use — restored nine-stat path, reran: cover 52.7%, outright 31.0% vs 25.9% (129 weeks); edge model printed as reference (47.2%). No unit test (CLI); verified by output.
Final: fixed missing build-path tests — test_live_edge_inputs_equal_training_inputs_for_every_decided_game, test_a_game_never_feeds_its_own_edge_score, test_neutral_site_drops_home_field_from_the_edge, test_games_against_non_fbs_teams_do_not_feed_the_stats; each fails under the reviewer's mutation (order+1, no margin, ignore neutral, no FBS mask), suite 343/343.
Final: fixed stale README (model.json claim, edge score description) and docstrings (edge_model, gotw) — plan Task 6 README step I had missed.
Final: OPEN for owner: Upset Watch why-lines read the new edge score; 9 of 9 lines changed, wk 7 and wk 9 now say the favorite leads. His call.
Final: minor (deferred): swing_block's neutral parameter is unused.
Final: minor (deferred): export.edge_training_inputs duplicates the loop in training_data / shootout_inputs.
Final: minor (deferred): CLI backtests cache the live season as final (edge-cutoffs, upset-backtest); stale until a build clears it.
Final: minor (deferred): advanced-stat rows have no in-progress guard like team_margins does.
Final: minor (deferred): neutral-site games keep a small tilt to the nominal home team (intercept), as in the old model.
Final: minor (deferred): BANNED key check in test_export is exact-match; eloDiff or marginAvg would pass.
Final: minor (deferred): future games (and a whole preseason) get edge labels from Elo and home field alone.
Final: owner decision — the upset model (nine-stat) makes the upset call, the edge model makes the edge score; so why_text no longer quotes an edge score that favors the favorite. test_why_text_never_quotes_an_edge_score_that_favors_the_favorite RED→GREEN, suite 344/344; rebuilt data: picks unchanged, why-lines for weeks 7, 9, 12 lose the sentence. On branch edge-review-fixes, NOT pushed.
