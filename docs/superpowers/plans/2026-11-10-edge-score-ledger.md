# SDD ledger — plan: docs/superpowers/plans/2026-11-10-edge-score.md
Pre-flight: T1 produces intercept+scale+groups -> T2 consumes (consistent); T2 to_score/linear -> T3 frame form (T3 needs frame-form linear; rule: add helper frame_linear in edge_backtest); T2 overall_edge/section_edge -> T4 (consistent); T4 data contract -> T6 (consistent).
Task 1: complete (commits d8aeae0..05975dd, tests: bash -c 'cd engine && uv run pytest -q' → 232 passed in 0.73s)
Task 2: complete (commits 05975dd..7a6a671, tests: bash -c 'cd engine && uv run pytest -q' → 240 passed in 0.67s)
Task 3: Ruling: plan said Even cutoff = largest c where the CUMULATIVE favored win rate below c is <= 0.58; on real data that made Even 40% of games (scores <4, local win rate up to 64%), wider than the bug being fixed. Changed to the first half-point score window whose own win rate tops 0.58 (test test_even_cutoff_uses_local_rate_not_cumulative). Result Even <2.0, Big >=7.5 — cost if wrong: Even band one notch narrow/wide; one constant to change.
Task 3: complete (commits 7a6a671..f87242a, tests: bash -c 'cd engine && uv run pytest -q' → 244 passed in 0.69s)
Task 4: Ruling: privacy test needs real scores but the export test world has no advanced stats and no team reaches 3 prior games; added AdvClient (synthetic advanced stats) and monkeypatched MIN_PRIOR=1 in that one test; score-range check limited to edge objects (drivers also carry an unrelated "score") — cost if wrong: test less strict than intended.
Task 4: Ruling: gotw why() reads rowEdge, falling back to edge for old JSON/test fixtures — cost if wrong: none (GOTW picks unchanged).
Task 4: complete (commits f87242a..8a372eb, tests: bash -c 'cd engine && uv run pytest -q' → 250 passed in 1.12s)
Task 5: complete (commits 8a372eb..05c99c6, tests: bash -c 'cd engine && uv run pytest -q' → 250 passed in 1.45s)
Task 5: HARD STOP reached; awaiting owner on report (2 pass bars + contradictions failed)
Task 5: Ruling (owner): Big cutoff 8.0, section lines stay row-based; removed section scoring (section_edge/section_linear, pass/run quantiles, PASS_KEYS/RUN_KEYS, rowEdge, edgeScore/runEdgeScore) as dead code; test_nan_feature_skipped rewritten onto overall_linear (behavior already existed, so it passed on first run) — cost if wrong: re-adding section scoring later.
Task 6: Ruling: Section.edgeScore/runEdgeScore types dropped (owner kept section lines table-based); EdgeCard takes home/away props for the meter ends; two older tests given those props — cost if wrong: none.
Task 6: complete (commits 6b7d547..c86a8a0, tests: bash -c 'cd web && npx tsc --noEmit && npx vitest run' →    Duration  854ms (transform 471ms, setup 0ms, collect 1.83s, tests 321ms, environment 1.44s, prepare 998ms))
Task 7: Ruling: meter fill uses --accent, not the team color (Ole Miss navy vanished on the dark track); EdgeMeter teams prop dropped — cost if wrong: less team color on the meter.
Final: fixed model.json published (intercept + score quantiles + coefs let anyone turn an edge score into our own win %) — test_swing_block_with_injected_model now asserts no model.json, RED→GREEN, suite 247/247; nothing in web read the file
Final: minor (deferred): neutral sites lean ~0.06 logit (<=0.4 score) toward the listed home team (intercept/centering don't flip)
Final: minor (deferred): edge cutoffs duplicated in web/lib/swing.ts and engine config.py; no test ties them
Final: minor (deferred): home row can show "EDGE: <stat> · A" next to "SLIGHT EDGE · B 2.4" favoring different teams
Final: minor (deferred): .badge-plain lacks the .sr-side wrap/right-align override that .badge-accent has
Final: minor (deferred): stray trailing blank line in engine/tests/test_gotw.py
Final: minor (deferred): Even cutoff rule uses ~280-game half-point windows (+-3% noise) if re-run
