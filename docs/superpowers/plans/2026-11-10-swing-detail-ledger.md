# SDD ledger — plan: docs/superpowers/plans/2026-11-10-swing-detail.md
Pre-flight: T1 produces driver.detail {meaning,format,offValue,defAllows,fbsAvg,why} -> T2 consumes same names (consistent). T1 needs model seasons + matchupWinRate; MODEL fixture in tests must add both.
Task 1: complete (commits 7fc6f98..d3b558a, tests: bash -c 'cd engine && uv run pytest -q' → 252 passed in 1.13s)
Task 2: complete (commits d3b558a..5e51069, tests: bash -c 'cd web && npx tsc --noEmit && npx vitest run' →    Duration  918ms (transform 340ms, setup 0ms, collect 1.89s, tests 307ms, environment 1.50s, prepare 1.06s))
Task 3: Ruling: matchupWinRates 2015-2025: pass_ppa .643, pass_sr .642, pd_sr .634, rush_ppa .643, rush_sr .647, sd_sr .663, explosive .520, stuff .597, line_yards .633. Explosive (proven) at 52% would make 'decide games ... won 52%' read as a contradiction; added WHY_WEAK wording under 0.55 (test test_why_is_honest_when_a_stat_alone_is_near_a_coin_flip) — cost if wrong: one sentence of copy.
Task 3: Ruling: visual check found rank column wrapping/overflowing the card at 375px and no hide label; fixed widths (42/22/36, nowrap ranks) and added Show/Hide the stats labels (test 'summary offers show and hide labels') — cost if wrong: none.
Final: fixed I1 'won X%' computed on the net of both sides (f_k) but shown under a one-side driver, so both teams' items read "won 66%" in 518/1124 games — now _side_win_rate per offense-vs-defense side, wording names "this offense against this defense"; test_side_win_rate_counts_each_side_of_the_ball RED→GREEN, suite 255/255. New rates: pass_ppa .603, pass_sr .604, pd_sr .593, rush_ppa .589, rush_sr .597, sd_sr .614, explosive .515 (WHY_WEAK), stuff .562, line_yards .581
Final: fixed I2 stuff cue read backwards with the suffix — offense-led marker; test_stuff_cue_reads_the_right_way RED→GREEN, suite 255/255
Final: minor (deferred): "defense allows" label reads oddly for stuff (latent; stuff not proven)
Final: minor (deferred): old-JSON flat path renders .swing-match as inline span (2px margin lost)
Final: minor (deferred): formatStat can print "-0.00"/"+0.00" for values rounding to zero
Final: minor (deferred): missing seasons/matchupWinRate fall back to 2015/0.5 copy instead of dropping why
Final: minor (deferred): test_detail_values_none_when_missing never exercises the None branch of _val
