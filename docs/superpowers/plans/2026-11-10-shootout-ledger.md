# SDD ledger — plan: docs/superpowers/plans/2026-11-10-shootout.md
Pre-flight: T1 side_features/training_rows -> T2 fit/game_score (consistent X_KEYS); T2 -> T3 held_out uses fit+predict on rows; T2 game_score + T4 pick (consistent); T4 shootout.json {id,why} + shootoutWatch -> T5 (consistent).
Task 1: Ruling: _priors counts NaN games as 0 in the mean (pre-existing behavior, kept so the swing model doesn't change); plays NaN is rare; build-time pregame() uses pandas mean which skips NaN — cost if wrong: slightly low training pace for a team with a missing plays value.
Task 1: complete (commits b5a983e..d6be111, tests: bash -c 'cd engine && uv run pytest -q' → 259 passed in 1.14s)
Task 2: complete (commits d6be111..4d54c3b, tests: bash -c 'cd engine && uv run pytest -q' → 263 passed in 1.14s)
Task 3: complete (commits 4d54c3b..6d0b340, tests: bash -c 'cd engine && uv run pytest -q' → 266 passed in 1.16s)
Task 3: HARD STOP: plan model fails WVU-TTU bar (10th); drives+sum experiment passes both; awaiting owner
Task 3: Ruling (owner): pace = drives (not plays), game score = combined expected scoring (not weaker side); plan's 'both offenses must qualify' min rule dropped; backtest 24.6% top-3 (2.48x), WVU-TTU 2nd. CLI 2026 check still prints both 'min'/'sum' columns, now identical — cost if wrong: cosmetic CLI output.
Task 4: Ruling: why_text opens "Both offenses score efficiently and both defenses give it up" only when both offenses are top third AND both defenses bottom third, else "Lots of expected scoring" — the plan's fixed opener would be false for e.g. two good offenses with good defenses — cost if wrong: copy tweak.
Task 4: Ruling: pick() input is (game dict, score, why string) not (summary, score, why_ctx) — week key needs seasonType/week from the CFBD game — cost if wrong: none (internal).
Task 4: Ruling: test_availability_watch_block failed once (qbVs.of None, line 273) in 1 of ~24 full runs; 0/10 with and 0/10 without this change — pre-existing order/timing flake, unrelated to shootout, not chased — cost if wrong: an intermittent CI red.
Task 4: complete (commits 7d251ef..4b6e94f, tests: bash -c 'cd engine && uv run pytest -q' → 273 passed in 1.46s)
Task 5: Ruling: PickCard also shows the final score (away – home) for finished weeks, mirroring the GOTW card — plan listed kickoff only — cost if wrong: one line removed. gotwFor kept as an alias of pickFor so existing callers and tests stay unchanged.
Task 5: complete (commits 4b6e94f..6afed42, tests: bash -c 'cd web && npx vitest run && npx tsc --noEmit && npx eslint app components lib' →    Duration  1.06s (transform 508ms, setup 0ms, collect 1.92s, tests 267ms, environment 1.08s, prepare 1.15s))
Task 6: Ruling: shootout reason drops the pace sentence unless at least one team is top half in drives per game — live wk10 pick (Boise-CSU) read 'Pace: 118th and 101st', which argues against the pick — cost if wrong: one line restored.
Task 6: build ok (10 calls); 2026 wk10 pick = Boise State at Colorado State (actual 102, week's highest); WVU-TTU = Shootout watch chip (GOTW Georgia-Ole Miss). Visual 375px light+dark ok, no sideways scroll.
Final review (opus): 0 Critical, 0 Important. Suites: engine 274, web 198.
Final: minor (deferred): _priors NaN handling biases cols-path training priors low after a missing value (0 missing in cache today; latent).
Final: minor (deferred): 2025 shootout picks in-sample (2025 in TRAIN_SEASONS), same as GOTW/swing.
Final: minor (deferred): why_text rank pool includes teams with 1-2 prior games, not MIN_PRIOR set.
Final: minor (deferred): copy: "Both offenses score efficiently" fires up to rank ~46 of 138; text never says defense rank 1 = best.
Final: minor (deferred): fit() LinAlgError if every row drops on NaN (degenerate input only).
Final: minor (deferred): _shoot_pregame refilters all seasons per game (build time only).
Final: minor (deferred): shootout card shows alone when a filter hides the GOTW but not the shootout pick.
Owner change: card slimmed (~95px vs GOTW 250px) with GOTW team-color split; 'Why watch' removed from home; reason shown as 'Shootout of the Week' note under the game page hero (pickWhyFor). web 202 tests.
