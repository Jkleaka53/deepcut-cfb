# SDD ledger — plan: docs/superpowers/plans/2026-11-10-availability-watch.md
Pre-flight: T1 skill frame → T2 watch_list (columns match SKILL_COLUMNS); T3 backup_block → T4 export (qbVs opponent filled from section) → T5 applyWhatIf reads availability[team].backup.cells keyed by unit row key; T5 defaultsOut → T6 loadOut; consistent.
Ruling: default-Out label "No stats last game" instead of spec "Missed last game" — box scores only list players with a stat, so absence ≠ proof of missing — cost: wording
Ruling: receivers ranked by receiving yards, not targets — free box scores carry no targets — cost: a high-target low-yard WR may be left off
Task 1: complete (commits 597b138..f5e62c9, tests: bash -c 'cd engine && uv run pytest -q' → 156 passed in 0.30s)
Task 2: Ruling: watch_list takes roster positions (CFBD /roster, 1 call/season) — without them a trick-pass WR counted as a QB (dropped from WRs, could become backup); unknown position falls back to 5+ attempts or a primary-passer game — cost: one extra API call per refresh
Task 2: complete (commits f5e62c9..03d7de4, tests: bash -c 'cd engine && uv run pytest -q' → 168 passed in 0.33s)
Task 3: complete (commits 03d7de4..94e26fe, tests: bash -c 'cd engine && uv run pytest -q' → 174 passed in 0.33s)
Task 4: Ruling: unknown-position fallback changed from '5+ attempts or primary' to 'QB unless he caught a pass this season' — the export test showed a real 2-attempt backup was dropped — cost: an unlisted RB who threw a pass and never caught one would count as a QB
Task 4: note: test_unknown_position_low_volume_passer_without_catches_is_a_qb was written with the fix, not run RED first (export test was the RED for this change)
Task 4: fixed empty-frame bug (boolean list filter on empty frame dropped columns) — test_no_skill_rows_lists_qbs_only RED→GREEN
Task 4: complete (commits 94e26fe..88077b5, tests: bash -c 'cd engine && uv run pytest -q' → 177 passed in 0.35s)
Task 5: complete (commits 88077b5..fb6086a, tests: bash -c 'cd web && npm test' →    Duration  788ms (transform 275ms, setup 0ms, collect 903ms, tests 153ms, environment 587ms, prepare 740ms))
Task 6: complete (commits fb6086a..118dce2, tests: bash -c 'cd web && npm test 2>&1 | grep -E 'Tests '' →       Tests  136 passed (136))
Task 7: Ruling: banner also shows when a starting QB is Out by default ("<name> Out (no stats last game)"), Reset only when choices differ — spec says banner on differences only, but a default-Out starter would silently show the backup's numbers — cost: wording
Task 7: Ruling: a starter with no backup never defaults Out (switch disabled) — defaultsOut test RED→GREEN — cost: none
Task 7: Ruling: backup with 0 starts shows "No starts yet, so his numbers show as dashes." — cost: wording
Task 7: Playwright 375px light+dark: Carr Out → banner, hero QB Bryce Underwood, INT 130th→105th, EPA 91st→81st, saved; reload kept; Reset cleared key; scrollWidth 360
Task 7: complete (commits 118dce2..5a8f93c, tests: bash -c 'cd web && npm test 2>&1 | grep -E 'Tests '' →       Tests  144 passed (144))
Final review: opus reviewer, 0 Critical, 1 Important, 5 Minor
Final: fixed starter split table shown under backup — 'starter Out removes the starter's own split table' RED→GREEN, web 146/146
Final: fixed (re-graded Minor→Important: stuck UI) stale save locking a no-backup starter Out — 'listedIds leaves out…' RED→GREEN
Final: fixed (re-graded Minor→Important: visibly wrong '139th of 138') backup rank capped at field size — test_rank_never_exceeds_field_size RED→GREEN, engine 178/178
Final: minor (deferred): browser recomputes edges from 1-decimal pct, a 14.96 gap can read slight where engine says even
Final: minor (deferred): a partial box-score fetch (skill rows but no passing rows for a game) can default a starter Out; banner shows it
Final: minor (deferred): Out button red #b42318 is hard-coded, not a token (checked readable in dark)
Post-review: collapsible availability blocks (owner) — watch.test 'collapsible…' + 'banner Change opens blocks' RED→GREEN, web 149
