# SDD ledger — plan: docs/superpowers/plans/2026-11-10-upset-watch.md
Pre-flight: T1 book_prob/spread_prob -> T3 join (consistent); T2 our_prob/gap -> T3 weekly_picks + T4 pick (consistent); T4 upset.json {id,why,odds} -> T5 UpsetPick (consistent).
Task 1: Ruling: plan's test value 0.567 for DK -142/+120 was an arithmetic slip; correct margin-free value is 0.5635 → test asserts 0.563 — cost if wrong: none (formula per plan).
Task 1: complete (commits a6cf4ec..4a8035d, tests: bash -c 'cd engine && uv run pytest -q' → 283 passed in 1.48s)
Task 2: Ruling: plan example gap(0.40, 0.75) = 0.15 was wrong; away dog ours 0.60 vs book 0.25 = 0.35 — cost if wrong: none.
Task 2: complete (commits 4a8035d..ceddf5b, tests: bash -c 'cd engine && uv run pytest -q' → 287 passed in 1.48s)
Task 3: complete (commits ceddf5b..204d105, tests: bash -c 'cd engine && uv run pytest -q' → 291 passed in 1.48s)
Task 3: HARD STOP: planned pick fails both bars (cover 45.7%, upsets 21.7% vs book 23.7%); close-game signal (spread<=7.5, gap>0.10: won 41.1% vs book 36.2%, n=849); weekly close-game pick cover 49.6%. Awaiting owner.
Task 3: iteration (owner 'Iterate first'): opponent adjustment experiment (sdd/adj_experiment.py), w by logloss = 0.8 → weekly pick cover 52.7%, upsets 31.0% vs book 25.9% PASS; awaiting owner on adopting site-wide.
Ruling (owner: site-wide adjustment): model (edge score, driver selection/score, overall edge, GOTW closeness via edge score, Upset Watch) reads opponent-adjusted pregame stats; pulldown ranks, favored team (rank gap) and shown values stay REAL stats so they match other sites — cost if wrong: a driver's size and its shown ranks come from different numbers.
Note: test_pulldowns_show_real_stats_while_model_reads_adjusted was written after the wiring (guard, not RED-first).
Ruling: Shootout keeps raw stats (separate model, not part of the owner's question) — cost if wrong: Shootout misses the same improvement; test later.
Task 3: owner kept EDGE_SCORE 2.0/8.0 with adjusted model (2.5/6.5 Big 78% on 2026). Upset backtest via real code: cover 52.7%, won 31.0% vs 25.9% PASS. Gate cleared.
Task 4: Ruling: why_text handles a dog driver on DEFENSE too ("{dog}'s defense ranks X against a {fav} offense that ranks Y") and a Big favorite ("has {fav} by S of 10") — plan covered offense / slight only — cost if wrong: copy.
Task 4: Ruling: odds_block clamps to 1..99 so the bar never shows 100/0 — cost if wrong: none.
Task 4: Ruling: test WorldClient now uses params.get for seasonType/week (the /lines request has no seasonType; real CFBD returns all season types for a year) — cost if wrong: none.
Task 4: complete (commits 204d105..26a7b7d, tests: bash -c 'cd engine && uv run pytest -q' → 305 passed in 2.14s)
Task 5: Ruling: game-page note adds the heading 'Why that could be wrong' (owner's mockup B wording) above the reason; ShootoutNote generalized to PickNote({tag, heading?, why}); pickFor made generic and returns the pick so the card gets odds — cost if wrong: none.
Task 5: complete (commits 26a7b7d..3695553, tests: bash -c 'cd web && npx vitest run && npx tsc --noEmit && npx eslint app components lib' →    Duration  1.01s (transform 416ms, setup 0ms, collect 2.21s, tests 378ms, environment 1.39s, prepare 1.26s))
Task 6: Ruling: cli upset-backtest 2026 spot check used raw pregame (Michigan-Oregon); fixed to pregame_adjusted, now matches site (wk10 Georgia State at App State, won; wk11 Georgia Southern at Georgia State). Build 11 calls ok.
Task 6: visual 375px light+dark ok: home cards GOTW > Shootout (95px) > Upset (142px with odds bar), game-page Upset note with heading; no sideways scroll.
Final review (opus): 0 Critical, 1 Important. Feature pushed live on owner's "done" BEFORE review returned; fixes go in a follow-up push (needs owner's go).
Final: fixed I1 stale pregame_adjusted cache (module dict keyed on id(tg)) — test_no_stale_results_across_frames RED→GREEN; cache moved to _Data._pre_adj, suite 309/309.
Final: fixed (re-graded up, published defect) "against a Iowa offense" articles — test_why_text_no_bad_articles RED→GREEN; 0 bad articles in rebuilt 2026 data.
Final: fixed (re-graded up, can fail a refresh) moneyline 0 → ZeroDivisionError / bogus 0% — test_zero_moneyline_is_missing RED→GREEN.
Final: fixed (re-graded up) reason could argue for the favorite — test_reason_must_back_the_underdog RED→GREEN; export skips such candidates.
Final: minor (deferred): neutral-site intercept tilts ~1 pt toward CFBD "home" team (pre-existing).
Final: minor (deferred): opponent average includes the head-to-head game (excluding it was checked: log loss slightly worse).
Final: minor (deferred): a driver is sized by adjusted z but its direction comes from real ranks; could show favoring the other team. Guard: drop drivers where signs disagree.
Final: minor (deferred): backtest weekly_picks doesn't skip GOTW/Shootout; spread scale fitted on all seasons (book side only).
Final: minor (deferred): cleanup: bisect imports, duplicated w=0.8 default, config import inside training_frame, games count includes rows with a missing opponent.
