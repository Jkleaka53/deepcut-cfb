# Availability Watch (R2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Availability tab into a what-if: per team, the starting QB, backup QB, top three pass catchers and lead running back, each switchable In/Out; setting the starting QB Out swaps in the backup's real numbers and the page's edges recompute.

**Architecture:** The engine precomputes everything a switch can show (the watch list, each player's share of team production, and the backup QB's offense cells ranked against this season's FBS teams plus his QB-vs-pass-D log). The browser only swaps precomputed values and re-derives edges with a TypeScript port of the engine's edge bands. Choices live in localStorage per game.

**Tech Stack:** Python engine (uv, pandas, pytest), CFBD `/games/players` (receiving, rushing), Next.js 15 static export, React 19, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-redesign-design.md`, section "Next feature (R2): Availability watch". Owner skipped further questions (2026-11-10); calls below marked *(my call)* are the executor's.

## Global Constraints

- Edges stay in words: Even / Slight edge / Big edge. Never odds, percentages of winning, or "50/50".
- Never claim an injury. Default-Out label is a fact from box scores: "No stats last game" *(my call: box scores list only players with a stat, so "missed" can't be proven)*.
- Only automatic guess: a listed player with no stats in the team's most recent game starts Out. Everyone else starts In. Nobody maintains a researched list.
- Research link at the top of each team's list: "Check the official report, then set players In or Out." (report link from R1 `availability[team].report`; Big Ten wording from R1 when no URL).
- Receivers and running back: show share of team production ("31% of receiving yards" / "44% of rushing yards"); switching them changes no numbers.
- QB starter Out: backup's real numbers replace the offense side of that team's passing rows; ranks, verdicts, edge card, biggest edges and the QB card recompute. Thin backup sample (< 3 starts) labeled "Small sample".
- Storage: `cfbm:whatif:<season>:<gameId>`, wrapped in try/catch, page works without it. "Reset to defaults" restores. Banner whenever choices differ from defaults: "What-if: <name> set Out" (names joined by ", ").
- No animations; square corners; light default with dark switch; tokens from `globals.css`.
- What-if controls only for games not yet completed *(my call)*; completed games keep the R1 availability card.
- Receivers ranked by season receiving yards (free box scores have no targets) *(my call)*; lead RB = most carries this season among non-QBs *(my call)*.
- Backup QB = this season's team passer with the most attempts before kickoff, other than the starter *(my call)*; none → backup row reads "No other QB has thrown a pass this season" and the starter's switch is disabled.

## Review Focus

1. **Backup with zero career starts** (only mop-up attempts) → backup cells all null; switching starter Out shows "—" rows, no verdicts, edge line hidden for that side; no crash. (Task 3 + Task 6 tests.)
2. **Old matchup JSON without `players`/`backup`** (merge window) → tab falls back to R1 card, no toggles. (Task 6 test.)
3. **localStorage holding an id no longer listed, or junk JSON** → ignored, defaults used. (Task 6 test.)
4. **Team whose last game had no box score (bye-adjacent cancellation)** → "last game" = most recent game with any box rows for that team; nobody wrongly defaulted Out. (Task 2 test.)
5. **Starter is also the season's only passer, backup none** → starter switch disabled, text explains. (Task 2 + Task 7 test.)

---

### Task 1: Receiving and rushing box scores (engine)

**Files:** Modify `engine/cfbm/fetch.py`, `engine/cfbm/export.py` (`_Data`); Create `engine/cfbm/skill.py`, `engine/tests/test_skill.py`; Modify `engine/tests/test_export.py` (`WorldClient` answers `category=receiving|rushing`).

**Interfaces — Produces:**
- `fetch.skill_box(client, season, season_type, week, games_list, category: str) -> list[dict]` (same cacheable rule as `player_box`).
- `skill.skill_games(box: list[dict], season: int, season_type: str, week: int, category: str) -> pd.DataFrame` with columns `SKILL_COLUMNS = ["game_id","season","order","team","athlete_id","name","category","count","yards"]`; `count` = REC or CAR, `yards` = YDS; unparseable stats → 0; `order = order_key(season_type, week)`.
- `_Data.skill` DataFrame for the live season only (current season's completed weeks).

- [ ] Step 1: tests `test_skill_games_parses_receiving` (REC 7 / YDS 64 → count 7, yards 64), `test_skill_games_parses_rushing`, `test_bad_stat_is_zero`.
- [ ] Step 2: run, expect FAIL (no module).
- [ ] Step 3: implement; wire `_Data.skill` (2 calls per completed live-season week).
- [ ] Step 4: `cd engine && uv run pytest -q` → PASS.
- [ ] Step 5: commit `feat(engine): receiving and rushing box scores`.

### Task 2: Watch list (engine)

**Files:** Create `engine/cfbm/watch.py`, `engine/tests/test_watch.py`.

**Interfaces — Produces:** `watch_list(passers, skill, team, season, before_order, starter: tuple[int,str] | None) -> dict` returning
`{"players": [Player...], "backupId": int | None}` where Player = `{"athleteId", "name", "role": "QB"|"QB2"|"WR"|"RB", "share": float|None, "shareOf": "receiving yards"|"rushing yards"|None, "noStatsLastGame": bool}`.
Order: starter (role QB), backup (role QB2, no switch), top 3 by receiving yards (role WR; any position, excluding QBs), lead RB by carries (role RB, excluding QBs and anyone already listed). `share` = player yards / team yards for that category this season before kickoff, rounded to 3 places. "Last game" = the team's most recent game (before kickoff, this season) present in `passers` or `skill`. `noStatsLastGame` = player has no row in any category in that game (QBs: in `passers`).

- [ ] Step 1: tests `test_order_and_roles`, `test_backup_most_attempts_not_starter`, `test_no_backup`, `test_share_of_receiving_and_rushing`, `test_no_stats_last_game_flag`, `test_last_game_is_latest_with_any_rows` (Review Focus 4), `test_rb_not_double_listed`.
- [ ] Step 2: run, FAIL.
- [ ] Step 3: implement.
- [ ] Step 4: PASS.
- [ ] Step 5: commit `feat(engine): availability watch list`.

### Task 3: Backup QB block (engine)

**Files:** Create `engine/cfbm/backup.py`, `engine/tests/test_backup.py`.

**Interfaces — Consumes:** `team_stats._side`, `qblog.qb_log`, `tiers.METRIC_DIRECTION`, `units.TABLES`. **Produces:**
- `rank_against(value: float|None, field: pd.Series, direction: int) -> tuple[int|None, float|None]` — rank = 1 + number of field values strictly better (direction-adjusted), pct = (n − rank)/(n − 1)·100 (n = non-null field size; matches `assign_tiers` method="min"); value None → (None, None).
- `backup_block(rows: pd.DataFrame, name: str, athlete_id: int, profile: pd.DataFrame, ranked_index, games_by_id, ranks) -> dict` = `{"athleteId","name","games": int,"smallSample": bool,"cells": {row_key: {"value","rank","pct"}},"qbVs": {"name","opponent":None,"oppRank":None,"of":None,"games":[...]}}` where `rows` are the backup's career team-game rows before kickoff (games he was primary passer), cells cover every passing row with an offense metric, field = `profile.loc[ranked_index, metric]`. No rows → games 0, all cells null. `smallSample` = games < 3.

- [ ] Step 1: tests `test_rank_against_higher_better`, `test_rank_against_lower_better`, `test_rank_against_none`, `test_block_cells_and_sample`, `test_block_no_starts_all_null` (Review Focus 1).
- [ ] Step 2: FAIL. Step 3: implement (aggregate rows with `_side(rows.assign(team="__backup__"), "team", "off")`).
- [ ] Step 4: PASS. Step 5: commit `feat(engine): backup QB numbers ranked against FBS`.

### Task 4: Export wiring (engine)

**Files:** Modify `engine/cfbm/export.py`, `engine/tests/test_export.py`.
- `matchup()`: `availability[team]` gains `players` and `backup` (backup qbVs gets `opponent`/`oppRank`/`of` filled from the same section's `qbVs`). Completed games get the same data (UI decides).
- [ ] Step 1: test `test_availability_watch_block` (keys present; `players[0].role == "QB"` when a starter exists; `backup` None or has `cells`).
- [ ] Step 2: FAIL. Step 3: implement. Step 4: full engine suite PASS. Step 5: commit `feat(engine): export availability watch data`.

### Task 5: What-if engine in the browser (web)

**Files:** Create `web/lib/whatif.ts`, `web/lib/whatif.test.ts`; Modify `web/lib/types.ts`, `web/lib/normalize.ts`.

**Interfaces — Produces:**
- `edge(offPct, defPct): Edge` (bands: |off−def| < 15 even, < 35 slight, else clear; side by sign; null input → null) and `sideEdge(rows)`, `biggestGap(rows)` — exact ports of `units.py` (`sideEdge` maps mean gap g through `edge(50+g/2, 50-g/2)`).
- `applyWhatIf(m: Matchup, out: Set<number>): Matchup` — for each team whose starter id ∈ out and whose `backup` exists: replace offense cells of that team's passing section by `backup.cells[row.key]` (missing key → null cell), recompute each row `edge`, section `edge` and `biggestGap`, swap `section.qbVs` for `backup.qbVs`, set `quarterbacks[team] = {athleteId, name}` of the backup. Never mutates input.
- `defaultsOut(m): Set<number>` = ids with `noStatsLastGame` (QB2 rows excluded).
- `TeamAvailability` gains `players?: WatchPlayer[]`, `backup?: Backup | null`.

- [ ] Step 1: tests — edge bands mirror `test_edge_bands` cases; `sideEdge` clear-defense case from `test_side_edge_average_gap`; `applyWhatIf` swaps cells and recomputes edge; input untouched; backup with null cells → rows null, no verdict, section edge null (Review Focus 1); no backup → unchanged; `defaultsOut`.
- [ ] Step 2: FAIL. Step 3: implement. Step 4: `npm test` PASS. Step 5: commit `feat(web): what-if recompute`.

### Task 6: Saved choices (web)

**Files:** Create `web/lib/choices.ts`, `web/lib/choices.test.ts`.
- `loadOut(season, id, defaults: Set<number>, listed: Set<number>): Set<number>` (stored `{in: number[], out: number[]}` overrides on top of defaults; ids not in `listed` ignored; junk → defaults), `saveOut(season, id, out, defaults)` (stores only differences; equal to defaults → removes key), `differs(out, defaults): boolean`.
- [ ] Tests: round trip, junk JSON, unknown id (Review Focus 3), storage throws, reset removes key. FAIL → implement → PASS → commit `feat(web): saved what-if choices`.

### Task 7: Availability watch UI (web)

**Files:** Create `web/components/matchup/AvailabilityWatch.tsx`, `web/components/matchup/WhatIfBanner.tsx`, `web/lib/watch.test.tsx`; Modify `web/app/game/page.tsx`, `web/app/globals.css`.
- Page holds `out` state (from `loadOut`), renders everything from `applyWhatIf(m, out)`; Hero/QB card/edges all read the derived matchup.
- Tab label "Availability" stays; section heading "Availability watch". Per team card: R1 QB flags, then the research line with the report link, then rows: name, role line (QB: "Starting QB"; QB2: "Backup QB · takes over if <starter> is Out" + "Small sample" tag when `backup.smallSample`; WR/RB: "<pct>% of receiving yards"), "No stats last game" tag when flagged, and a two-button square In/Out switch (`aria-pressed`). QB2 has no switch. Starter switch disabled when `backup` is null, with "No other QB has thrown a pass this season".
- `WhatIfBanner` under the hero when `differs`: "What-if: Tommy Carr set Out" + "Reset to defaults" button.
- Completed games or data without `players` (Review Focus 2) → R1 `AvailabilityCard`.
- [ ] Tests (renderToString): rows and roles; switch toggles call back; disabled starter switch with text (Review Focus 5); banner text; completed game → R1 card. FAIL → implement → PASS.
- [ ] Playwright at 375px, Michigan at Oregon: set Tommy Carr Out → banner shows, Michigan's passing rows change, reload keeps it, Reset restores; dark mode readable; no horizontal scroll.
- [ ] Commit `feat(web): availability watch what-if tab`.

### Task 8: Docs, data, review, preview

- [ ] README Methods: availability watch paragraph (what switches change and don't, "No stats last game" meaning). Spec: append "R2 built" calls list.
- [ ] Local data build; `npm test && npm run build`.
- [ ] Final whole-branch review (fresh reviewer, most capable model); fix Critical/Important with RED→GREEN.
- [ ] Commit docs and data separately. ASK THE OWNER before pushing the `availability-watch` branch for a preview; merge only after "done".
