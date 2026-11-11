# Upset Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each week the site picks the game where the pros are most likely to be wrong: the underdog by DraftKings' odds is the team our edge score likes better than the odds do. It shows a slim card under Game of the Week with DraftKings' win odds as a two-color bar. Our reason ("Why that could be wrong") goes on the game page.

**Architecture:** `cfbm/upset.py` turns DraftKings moneylines into a margin-free home win %. It compares that with our internal pregame win chance (the logistic of `edge_score.overall_linear`, never exported) and picks per week the underdog with the biggest gap. Our chance must exceed the book's, and the book's underdog chance must be at most 45%. A leave-one-season-out backtest on 2015-2025 (book chance from spreads, curve fitted on the history) gates the web work. The export writes `{season}/upset.json` with `{id, why, odds: {source, home, away}}` per week.

**Tech Stack:** Python (uv, pandas, numpy, pytest), Next.js 15 static export, React 19, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-edge-score-shootout-upset-design.md`, "Slice 4: Upset Watch" (including "Owner decisions (2026-11-10, after checking the data)") and builder-check decisions 2, 3, 4, 5.

## Global Constraints

- The only win % exported anywhere is DraftKings' own, in `upset.json` `odds`, as whole numbers labeled `"source": "DraftKings"`. No spread, moneyline, or any of OUR win %, score, margin or total, in any file or on the page.
- Upset Watch card: slim, under Game of the Week (and under the Shootout card), using the same team-color split. The reason lives on the game page, not the home page (owner's call on the Shootout card, applied here too).
- If the pick is the Game of the Week or the Shootout pick, take the next game. With no lines or no qualifying game, hide the card.
- HARD STOP after Task 3: backtest numbers go to the owner before any web work. Pass bar: the picks' underdogs **cover** (win outright, or lose by less than the spread) more than 50% of the time, AND win outright more often than the book's own average chance for those picks.
- CFBD budget: `/lines` is one call per season. Training seasons are cached for good; the live season refreshes on each build (+1 call per refresh).
- No animations, square corners, tokens only, light + dark, works at 375px.

## My calls

- **Book chance from moneylines** (display, 2026): American odds to raw chance: `100/(ml+100)` if `ml > 0`, else `-ml/(-ml+100)`. Home chance = `raw_home / (raw_home + raw_away)`. Provider `"DraftKings"` only; no DraftKings moneyline → no pick for that game.
- **Book chance from spreads** (backtest only): `p_home = 1/(1+exp(spread/k))` (CFBD `spread` is from the home side, negative = home favored). `k` is fitted by least squares on 2015-2025 outcomes. Spread source per game: `consensus` if present, else the first provider with a spread.
- **Our chance** (internal): `1/(1+exp(-overall_linear(...)))`. Home field is included, as the spec requires.
- **Candidates:** book underdog chance ≤ `DOG_MAX = 0.45`, and our underdog chance > the book's. **Gap** = our underdog chance minus the book's. Pick = biggest gap per week, skipping the GOTW and Shootout ids. Same week keys as GOTW.
- **Reason** (game page). It is our edge score's view in words, plus the underdog's strongest swing factor:
  - The underdog's top swing driver that favors it: `"{dog} has the edge in {label}: {dog}'s offense ranks {off} against a {fav} defense that ranks {def} of {n}."`
  - Then one of:
    - `"Our edge score has it even."` (band even)
    - `"Our edge score leans {dog}, {score} of 10."` (dog favored)
    - `"Our edge score has {fav} by only {score} of 10."` (favorite, slight)
  - If no driver favors the underdog, only the second sentence.
- **Odds bar:** DraftKings home/away %, rounded to whole numbers, adding up to 100. Away on the left, home on the right (matches the edge meter), in team fills, with the label "DraftKings odds".

## Review Focus

1. **A game with Bovada but no DraftKings moneyline**: it never qualifies for display, and no odds come from another book. → Task 1 test `test_book_prob_needs_draftkings`.
2. **The pick equals the GOTW or the Shootout pick**: take the next-biggest gap. → Task 4 test `test_pick_skips_gotw_and_shootout`.
3. **The book's favorite is also ours by more** (no disagreement): never picked, even if it's the only game with a line. → Task 2 test `test_no_pick_without_disagreement`.
4. **Our win % leaking**: `upset.json` odds keys are exactly `{source, home, away}`, the why text has no `%`, and summaries and matchups gain no new numeric fields. → Task 4 test `test_upset_exports_only_draftkings_odds`.
5. **Neutral-site games**: no home tilt in our chance, and away/home in the odds keep the CFBD orientation. → Task 2 test `test_neutral_site_no_home_tilt`.

---

### Task 1: Lines and book chance

**Files:**
- Modify: `engine/cfbm/fetch.py` (`lines(client, season, live) -> list[dict]`: `client.get("/lines", {"year": season}, cacheable=not live)`)
- Create: `engine/cfbm/upset.py` (`book_prob`, `spread_of`, `spread_prob`, `fit_spread_scale`)
- Test: `engine/tests/test_upset.py`

**Interfaces:**
- Produces:
  - `book_prob(game_lines: dict, provider: str = "DraftKings") -> float | None`: home chance, margin removed; None without both moneylines from that provider.
  - `spread_of(game_lines: dict) -> float | None`: the consensus spread if present, else the first provider with a spread.
  - `spread_prob(spread: float, k: float) -> float`.
  - `fit_spread_scale(spreads: np.ndarray, home_win: np.ndarray) -> float`: k by grid search over 5.0-25.0 in steps of 0.1, minimizing log loss.

- [ ] **Step 1: Write failing tests:**
  - `test_book_prob_removes_margin`: DraftKings home -142, away +120 → `round(book_prob(...), 3) == 0.567` (raw 0.5868 / 0.4545).
  - `test_book_prob_needs_draftkings`: only Bovada moneylines → None; DraftKings with a null moneyline → None.
  - `test_spread_of_prefers_consensus`: lines `[{provider teamrankings, spread -3}, {provider consensus, spread -4.5}]` → -4.5; with no consensus → -3; none → None.
  - `test_spread_prob_direction`: `spread_prob(-7, 15) > 0.5 > spread_prob(7, 15)` and `spread_prob(0, 15) == 0.5`.
  - `test_fit_spread_scale_recovers_k`: synthetic outcomes drawn with k=14 over 20,000 spreads → `abs(fit - 14) < 1`.
- [ ] **Step 2:** `cd engine && uv run pytest tests/test_upset.py -q`. Expected: FAIL (ImportError).
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `uv run pytest -q`. Expected: all pass.
- [ ] **Step 5: Commit** `feat(engine): DraftKings and spread win chances for Upset Watch`.

### Task 2: Our chance and the gap

**Files:**
- Modify: `engine/cfbm/upset.py`
- Test: `engine/tests/test_upset.py`

**Interfaces:**
- Consumes: `edge_score.overall_linear(model, pre, home, away, neutral)`.
- Produces:
  - `our_prob(model, pre, home, away, neutral) -> float | None` (home chance; internal only).
  - `gap(our_home: float, book_home: float) -> tuple[str, float] | None`: returns `("home"|"away", gap)` for the book's underdog when its book chance ≤ DOG_MAX and our chance for it is higher; else None.

- [ ] **Step 1: Write failing tests:**
  - `test_gap_picks_book_underdog`: `gap(0.48, 0.30) == ("home", approx 0.18)`; `gap(0.40, 0.75) == ("away", approx 0.15)`.
  - `test_no_pick_without_disagreement`: `gap(0.20, 0.30) is None` (we like the favorite more).
  - `test_close_odds_not_an_upset`: `gap(0.60, 0.47) is None` (book underdog above 0.45).
  - `test_neutral_site_no_home_tilt`: a hand model with only a home coefficient (`home.coef = 0.5`, every feature coefficient 0, intercept 0) → `our_prob(..., neutral=True) == 0.5` and `our_prob(..., neutral=False) > 0.5`. Use the same model shape as `test_edge_score.py`'s fixture.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `uv run pytest -q`. Expected: all pass.
- [ ] **Step 5: Commit** `feat(engine): Upset Watch compares our edge with the book`.

### Task 3: Backtest and HARD STOP

**Files:**
- Create: `engine/cfbm/upset_backtest.py`
- Modify: `engine/cfbm/edge_backtest.py` (`held_out` also returns `game_id` and `lin`; existing columns unchanged), `engine/cfbm/cli.py` (subcommand `upset-backtest`)
- Test: `engine/tests/test_upset_backtest.py`
- Output: `docs/superpowers/plans/2026-11-10-upset-report.md`

**Interfaces:**
- Produces:
  - `join(held: pd.DataFrame, lines_by_id: dict[int, dict], games_by_id: dict[int, dict], k: float) -> pd.DataFrame`, one row per game with a spread: `season, week_key, game_id, our_home, book_home, spread, home_margin`.
  - `weekly_picks(df) -> pd.DataFrame`: one row per week, the biggest-gap candidate, with `dog_won` (outright), `dog_covered` (won, or lost by less than the spread), `book_dog` (book chance for the dog).
  - `summary(picks) -> dict`: `{"weeks", "coverRate", "upsetRate", "bookUpsetRate" (mean book_dog)}`.
  - The CLI prints the summary overall and per season. It also prints the 2026 week 10 and week 11 picks (from DraftKings moneylines and the full-history model), and a control: the cover rate of ALL ≤45% underdogs, which should be about 50%.

- [ ] **Step 1: Write failing tests:**
  - `test_cover_definition`: home dog at spread +7 (home underdog): losing by 3 → covered and not won; losing by 10 → neither; winning → both. Away dog at spread -7 (home favored): the mirror cases.
  - `test_weekly_picks_biggest_gap`: a 3-game week where only game 2 qualifies (book dog 0.30, ours 0.45) → game 2 picked; a week with no qualifier → no row.
  - `test_summary_rates`: 4 picks with dog_covered [1,1,0,1], dog_won [1,0,0,0], book_dog [0.3]*4 → coverRate 0.75, upsetRate 0.25, bookUpsetRate 0.3.
  - `test_held_out_keeps_old_columns`: `held_out` output still has `season, score, favored_won`, plus `game_id, lin`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement. Then run `uv run python -m cfbm.cli upset-backtest`. Expected: the summary, per-season lines, the 2026 picks and the control cover rate. Fetches 11 historical `/lines` seasons (2 cached already).
- [ ] **Step 4:** Write the report (numbers, the per-season spread, 2026 picks, verdict against the pass bar) and commit `feat(engine): Upset Watch backtest`.
- [ ] **Step 5: HARD STOP.** Show the owner the headline in plain words. If the bar fails, give the options (iterate, drop the card, ship without it) and wait.

### Task 4: Export the pick

**Files:**
- Modify: `engine/cfbm/export.py` (`_Data` gets `self.lines = {gid: game_lines}` for display seasons via `fetch.lines(client, s, s == live)`; after GOTW and Shootout, write `upset.json`), `engine/cfbm/upset.py` (`why_text`, `pick`, `odds_block`)
- Test: `engine/tests/test_upset.py`, `engine/tests/test_export.py`

**Interfaces:**
- Produces:
  - `odds_block(book_home: float) -> {"source": "DraftKings", "home": int, "away": int}`, where home is rounded and away = 100 - home.
  - `why_text(m: dict, dog: str, fav: str) -> str`, from the matchup's swing drivers, overallEdge and per My calls.
  - `pick(cands: list[tuple[dict, float, dict]], skip: dict[str, set[int]]) -> dict[str, dict]`. Items are `(cfbd_game, gap, {"why", "odds"})`; `skip[week]` holds the GOTW and Shootout ids.
  - File `{season}/upset.json` = `{week: {"id", "why", "odds"}}`.

- [ ] **Step 1: Write failing tests:**
  - `test_odds_block_sums_to_100`: `odds_block(0.567) == {"source": "DraftKings", "home": 57, "away": 43}`.
  - `test_pick_skips_gotw_and_shootout`: gaps 0.3 (id 1, GOTW), 0.25 (id 2, Shootout), 0.2 (id 3) → id 3.
  - `test_why_text_with_driver`: a hand matchup whose top driver favoring the dog is Explosive plays (dog offense rank 9, fav defense rank 101, of 134), overallEdge slight for the favorite at 3.1 → the exact two sentences in My calls.
  - `test_why_text_without_driver`: no dog driver, even band → `"Our edge score has it even."`
  - `test_export.py::test_upset_exports_only_draftkings_odds`: extend `WorldClient` with a `/lines` response (DraftKings moneylines on a few games, one Bovada-only), then build with the hand models and MIN_PRIOR patched to 1.
    - `upset.json` values have keys exactly `{id, why, odds}`, and the odds keys are exactly `{source, home, away}` with `source == "DraftKings"`.
    - `why` has no `%`.
    - No picked id equals its week's GOTW or Shootout id.
    - The Bovada-only game is never picked.
    - `games.json` and the matchups gain no key containing `prob`, `moneyline`, `spread` or `odds`.
  - `test_export.py::test_upset_file_empty_without_lines`: the default `WorldClient` → `upset.json == {}`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `uv run pytest -q`. Expected: all pass.
- [ ] **Step 5: Commit** `feat(engine): Upset Watch pick with DraftKings odds in the data`.

### Task 5: Web: the card, the odds bar and the game-page note

**Files:**
- Create: `web/components/UpsetCard.tsx`
- Modify:
  - `web/components/PickCard.tsx`: an optional `children` slot under the teams row.
  - `web/components/matchup/ShootoutNote.tsx` → rename to `PickNote.tsx` with props `{ tag, why }`, and update its callers and tests.
  - `web/lib/data.ts`: `loadUpset(season)`; a missing file → `{}`.
  - `web/lib/types.ts`: `UpsetPick { id; why; odds: { source: string; home: number; away: number } }`.
  - `web/app/page.tsx`: the card under the Shootout card.
  - `web/app/game/page.tsx`: a note under the Shootout note.
  - `web/app/globals.css`.
- Test: `web/lib/upset.test.tsx`

**Interfaces:**
- Produces: `UpsetCard({ game, odds, teams })`, which renders `PickCard` with tag "Upset Watch" and an `.odds-bar` child.

- [ ] **Step 1: Write failing tests:**
  - `UpsetCard shows the source and both whole-number odds`: contains `DraftKings odds`, `43%` and `57%`, with the away team's % first.
  - `odds bar widths follow the odds`: the away segment has `width:43%`, the home segment `width:57%`.
  - `no reason on the home card`: no `Why that could be wrong`.
  - `game page note`: `PickNote tag="Upset Watch"` shows the tag and the why.
  - `hidden without a pick or when the filter hides it` (reuse `pickFor` with an upset map).
- [ ] **Step 2:** `cd web && npx vitest run lib/upset.test.tsx`. Expected: FAIL.
- [ ] **Step 3:** Implement. The odds bar is a 20px-tall flex row of two segments in the team fills (falling back to ink), with the team abbr and % in white, 12px, bold. The caption "DraftKings odds" sits under it, 11px, in the card's white text.
- [ ] **Step 4:** `npx vitest run && npx tsc --noEmit && npx eslint app components lib`. Expected: all pass.
- [ ] **Step 5: Commit** `feat(web): Upset Watch card with DraftKings odds`.

### Task 6: Rebuild, verify, review, ship

- [ ] **Step 1:** Make sure no refresh run is in progress. Then `uv run python -m cfbm.cli build` (expected calls ≈ 11) and `npm run build` (exit 0).
- [ ] **Step 2:** Check that `upset.json` has a week 11 entry, and record in the ledger which game it is, its odds and its why.
- [ ] **Step 3:** Visual check at 375px in light and dark: the home page shows GOTW, then Shootout, then Upset Watch; the Upset game page shows its note; nothing scrolls sideways. Delete `.playwright-mcp` afterwards.
- [ ] **Step 4:** Commit the data. Run an Opus final review on the code-only diff, then show the owner. Push only on "done". Copy the ledger to `docs/superpowers/plans/2026-11-10-upset-watch-ledger.md` and update the project memory.
