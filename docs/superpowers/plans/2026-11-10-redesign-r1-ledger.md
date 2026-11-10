# SDD ledger — plan: docs/superpowers/plans/2026-11-10-redesign-r1.md
Spec: docs/superpowers/specs/2026-11-10-redesign-design.md
Branch: redesign (in main checkout, not a worktree; never main)
Pre-flight:
- T1->T8/T9: teams.json fields {school,id,abbr,conference,fill,textLight,textDark,logo,logoDark} match TeamInfo + logoPath. OK.
- T2->T8/T10: homeRank/awayRank match. OK.
- T3->T8/T11: weather {status,label,icon,tempF,precipPct,windMph,gustMph,asOf}, venue {name,city,state,grass,dome}. OK.
- T4->T8/T11: cell pct, explain, hint, Section.edge/biggestGap, GameSummary.gap {key,label,favors}. OK.
- T5->T11: availability {team:{flags,report:{conference,url,when}}}. OK.
- T7 theme.ts -> T9 logoPath(theme). OK.
Task 1: Ruling: fetch.team_info takes live=False kwarg (plan said cacheable when not live but omitted the param) — needed to honor cacheability — cost if wrong: none
Task 1: complete (commits 4f6930b..b991391, tests: bash -c 'cd engine && uv run pytest -q' → 110 passed in 0.27s)
Task 2: complete (commits b991391..dd97a5b, tests: bash -c 'cd engine && uv run pytest -q' → 117 passed in 0.29s)
Task 3: Ruling: games.json now written after weather is attached (moved write below the loop) and matchup game summaries carry the same weather — keeps one source per game — cost if wrong: none
Task 3: complete (commits dd97a5b..880ea37, tests: bash -c 'cd engine && uv run pytest -q' → 127 passed in 0.29s)
Task 4: Ruling: side_edge maps the mean gap through edge() by passing (50+g/2, 50-g/2) so the existing 15/35 bands apply unchanged; hint for offense-less rows (front7) = 'Defense: lower is better' only when defense is lower-better, else None — cost if wrong: wording
Task 4: complete (commits 880ea37..1e44864, tests: bash -c 'cd engine && uv run pytest -q' → 131 passed in 0.28s)
Task 5: Ruling: Big Ten report URL left out (bigten.org blocks automated checks; no confirmable page) — Big Ten teams show "No official availability report" until the owner supplies a URL — cost if wrong: missing link for Big Ten games
Task 5: Ruling: SEC/ACC/Big 12 links point at the conference availability pages (SEC fbreports; ACC/Big 12 policy+report pages) — cost if wrong: link lands on policy page
Task 5: complete (commits 1e44864..f39f4fd, tests: bash -c 'cd engine && uv run pytest -q' → 138 passed in 0.29s)
Task 6: Ruling: YAML check uses y[true] since Ruby parses the 'on' key as boolean — verification only — cost: none
Task 6: complete (commits f39f4fd..dc1772f, tests: bash -c 'ruby -ryaml -e 'y=YAML.load_file(".github/workflows/refresh.yml"); exit((y["on"]||y[true])["schedule"].size==4 ? 0 : 1)' && echo 4 schedules' → 4 schedules)
Task 7: Ruling: kept legacy table.stats/.tag/.callout styles restyled to tokens (SplitTable survives into Task 11); old .game-row/.controls styles dropped — old home page looks plain until Task 10 — cost: none on branch
Task 7: complete (commits dc1772f..f2ef292, tests: bash -c 'cd web && npm test' →    Duration  357ms (transform 40ms, setup 0ms, collect 45ms, tests 8ms, environment 344ms, prepare 130ms))
Task 8: Ruling: new format tests live in lib/format.redesign.test.ts (not appended to format.test.ts) so the old edgeText/rankText tests can be deleted cleanly in Task 11 — cost: none
Task 8: complete (commits f2ef292..8efe523, tests: bash -c 'cd web && npm test && npx tsc --noEmit' →    Duration  399ms (transform 110ms, setup 0ms, collect 163ms, tests 28ms, environment 379ms, prepare 221ms))
Task 9: Ruling: light/dark logos both rendered and swapped by CSS on data-theme (no client theme read in TeamLogo) to avoid a flash of the wrong logo; logo-tile (white square) used for hero over team color — cost: two img tags per logo
Task 9: complete (commits 8efe523..146f6a5, tests: bash -c 'cd web && npm test && npx tsc --noEmit' →    Duration  400ms (transform 152ms, setup 0ms, collect 220ms, tests 35ms, environment 409ms, prepare 291ms))
Task 10: Ruling: season switch is a native <select> styled as a chip at the end of the week row; current week chip auto-scrolled to centre (instant, no animation); side column capped at 42% so team names aren't cut by the gap badge — cost: wording/layout only
Task 10: Ruling: local data build (Task 12 step 2) run early for the 375px check; generated data left uncommitted until Task 12 — cost: none
Task 10: complete (commits 146f6a5..b9f5732, tests: bash -c 'cd web && npm test && npx tsc --noEmit' →    Duration  427ms (transform 166ms, setup 0ms, collect 248ms, tests 48ms, environment 425ms, prepare 389ms))
Task 11: Ruling: active tab tracked with a passive window scroll listener (last section whose top passed the tab bar) instead of IntersectionObserver — same behaviour, simpler — cost: none
Task 11: Ruling: html/body overflow-x changed hidden -> clip; 'hidden' made body a scroll container and silently broke every position:sticky (top bar, filter chips, tabs). Found in the 375px check — cost: none (clip needs Safari 16+, older Safari just loses the overflow guard)
Task 11: Ruling: legend text hard-codes "138 FBS teams" per spec copy; ranks are among FBS teams with data, which may differ slightly — cost: wording
Task 11: Ruling: EdgeCard sentence for mixed/one-sided cases = "X's defense is ahead when Y passes" / "X's passing game is ahead of Y's defense"; all-even = "These passing games are evenly matched." Plus "Not a prediction." footnote — cost: wording
Task 11: complete (commits b9f5732..d71c9aa, tests: bash -c 'cd web && npm test && npx tsc --noEmit && npm run build' → ○  (Static)  prerendered as static content)
Task 12: Ruling: whole-branch final review run BEFORE the push question so the preview the owner sees already has its fixes; push still awaits owner — cost: none
Task 12: complete (commits d71c9aa..bca7c86, tests: bash -c 'cd engine && uv run pytest -q && cd ../web && npm test' →    Duration  435ms (transform 98ms, setup 0ms, collect 220ms, tests 46ms, environment 457ms, prepare 472ms))
Final review: fresh reviewer (opus) — 0 Critical, 4 Important, 7 Minor; all 4 Important re-graded and kept
Final: fixed TBA kickoffs show fake time / wrong day — test_game_summary_exports_tbd_flag + fixes.test "TBA kickoffs" (TZ pinned to Pacific) RED→GREEN, suite engine 141/141, web 87/87
Final: fixed dark-mode bars invisible — test_bar_on_keeps_team_hue + fixes.test "dark-mode bars" RED→GREEN; 0 of 138 barDark below 3:1 on #13171c; suite green
Final: Ruling: reviewer's suggested textDark for bars rejected — Michigan and Oregon textDark are both gold, so the bar became one colour; new barDark = team primary lightened in place (keeps hue) + 2px gap between halves — cost: none
Final: fixed Big Ten told "no report exists" — test_report_for_known_conference_without_link + fixes.test "availability wording" RED→GREEN; Big Ten now "Check the Big Ten's official availability report." — suite green
Final: fixed old-format data shows empty Biggest gaps card and false availability lines — fixes.test "old-format data hides new sections" (visibleTabs) RED→GREEN; suite green
Final: Ruling: added web/vitest.config.mts (@ alias, JSX, TZ=America/Los_Angeles) so component tests can render — cost: none
Final: minor (deferred): weather at the 15.5–16 day edge shows nothing instead of "Forecast closer to kickoff"
Final: minor (deferred): past games not marked completed still make an Open-Meteo call each run
Final: minor (deferred): "did not play last game" really means "threw no pass last game"
Final: minor (deferred): favorite star buttons sit inside the row link (invalid nesting for screen readers)
Final: minor (deferred): fetch-logos.mjs finds no data from a checkout path containing spaces (use fileURLToPath)
Final: minor (deferred): /venues cached forever; new or renamed stadiums never picked up
Final: minor (deferred): no color-scheme:dark, so the native season dropdown and scrollbars stay light in dark mode
Post-review: owner asked GAP -> Edge. Chip = 'Edge: <stat> · <ABBR>'; matchup badge 'Biggest edge', card 'Biggest edges' — edge-label.test RED→GREEN
Post-review: owner asked for Game of the Week in this update. test_gotw (5) + test_gotw_json + lib/gotw.test (6) RED→GREEN; engine 147, web 95
Post-review: Ruling: GOTW eligible = games with an AP Top 25 team when the week has any (pure unit score picked UMass at Toledo in week 11) — rank never enters the score itself — cost if wrong: a strong unranked matchup can't be picked in a week with ranked games
Post-review: Ruling: GOTW weights 0.6 strength / 0.4 closeness, swing factors deferred to Slice 2; card shows under any filter the game passes — cost: pick/visibility choice
Post-review: QB splits rework (owner picked layout A). test_qblog (4) + test_qb_vs_block + lib/qbsplit.test (17) RED→GREEN; qbcard.test written after the component (render check, not TDD). engine 152, web 112
Post-review: Ruling: 'as good or better' includes the line rank; pts/pass weighted by dropbacks; small sample < 3 games; postseason stage from CFBD notes (CFP vs Bowl); unit split tables moved out of 'More' into their own cards per owner — cost: wording/layout
Post-review: collapsible QB groups (owner) — qbgroup.test RED→GREEN (2 of 3 failed first; 'holds all tables' passed pre-change since content already existed), web 115
