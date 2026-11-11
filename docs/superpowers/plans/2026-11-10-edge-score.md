# Edge Score Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every game gets a 0 to 10 edge score (and which team it favors) behind the Even / Slight / Big labels, so "Even" stops covering lopsided matchups. The score is shown as a meter on the game page and as a chip on the home page.

**Architecture:** The swing model (`swing_model.train`) already fits a logistic regression on nine pregame matchup stats plus home field, 2015-2025 minus 2020. The model will also keep its intercept and the training distribution of how lopsided games were. A new `cfbm/edge_score.py` turns a game's pregame stats into a linear score, then into a 0 to 10 number by percentile against training games. The labels come from cutoffs picked by a leave-one-season-out backtest. Passing and running section edges use the same math, limited to their own stat groups and one side of the ball.

**Tech Stack:** Python (uv, pandas, numpy, pytest), Next.js 15 static export, React 19, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-edge-score-shootout-upset-design.md`, "Slice 1: Edge score" and "Decisions from the builder check" 1-4. Mockup A: `docs/superpowers/specs/2026-11-10-mockups/edge-score.html`.

## Global Constraints

- Not for gambling: never export or show our own win %, predicted score, total, margin or spread. Published JSON carries only `score` (0-10, one decimal), favored `team`, and the band label.
- Inputs are only the nine swing-model stats (`swing_data.FEATURES`). No new CFBD calls, no play-by-play backfill.
- Home field counts (the model's `home` coefficient; 0 at neutral sites).
- Stats strictly before kickoff, FBS-vs-FBS only (the existing `pregame` and `MIN_PRIOR = 3` rules).
- Band enum stays `"even" | "slight" | "clear"` in the data. The web already shows `clear` as "Big edge" (`lib/swing.ts` BAND), so there's no rename.
- Game of the Week selection must not change: `gotw.py` keeps reading the old row-based passing edge.
- Design: no animations, square corners, tokens only, light + dark, works at 375px.
- HARD STOP after Task 5: the backtest report goes to the owner before any web work (Task 6).

## My calls

- **Overall linear score** (home perspective, >0 favors home): `L = intercept + home_coef*home + Σ_k coef_k * (f_k - mean_k) / sd_k`, with `f_k = side_advantage(home off_k, away def_k) - side_advantage(away off_k, home def_k)`. All nine coefficients are used, including negative ones (that's what the fit is), not only `importance`.
- **Section linear score** (offense perspective, >0 favors offense): `S = Σ_{k in group} coef_k * (side_advantage(off, def)_k - sideMean_k) / sd_k`. Groups: `PASS = ("pass_ppa", "pass_sr", "pd_sr")`, `RUN = ("rush_ppa", "rush_sr", "stuff", "line_yards")`. `sd_sr` and `explosive` count toward the overall score only.
- **0 to 10 scaling:** `score = 10 * share of training games whose |value| is below this game's |value|`, interpolated over 101 stored quantiles, rounded to 1 decimal. One quantile table each for overall, pass and run. It is a percentile, so it can't be turned back into a win %.
- **Cutoffs:** one pair (`EDGE_SCORE_SLIGHT`, `EDGE_SCORE_BIG`) shared by overall and both sections. The backtest picks them (Task 3) and they're written into `config.py`.
- **Early season** (either team under `MIN_PRIOR` FBS games): the overall edge stays `None` as today. Section edges fall back to the old row-based `side_edge` with `score: None`.
- **Home chip:** a second, plain (not accent) chip after the existing Key/Edge chip: `Slight edge · OM 3.4`. Shown only when the band isn't even and the score exists.
- **Contradiction gate:** a section label "contradicts" its table when it favors one team but the majority of that table's non-even rows favor the other. The report counts these over 2026. If more than 5% of labeled sections contradict, list them in the report for the owner.

## Review Focus

1. **Early-season games** (under 3 FBS games for either team): no score, no crash; section edges keep the old labels; the meter and chip are hidden. → Task 4 test `test_section_edges_fall_back_early`, Task 6 test `meter hidden when overall is null`.
2. **Neutral-site games:** home field contributes 0. → Task 2 test `test_neutral_drops_home_field`.
3. **A stat missing (NaN) for one team:** that stat is skipped, not treated as 0. If every stat in a group is missing, the edge is `None`. → Task 2 test `test_nan_feature_skipped`.
4. **Old JSON without `score`** (cached pages, older seasons): the web falls back to the current "Overall: Slight edge X" text. → Task 6 test `falls back to text when score missing`.
5. **No win-probability-shaped fields published.** → Task 4 test `test_no_gambling_fields_exported`.

---

### Task 1: Model keeps intercept and lopsidedness quantiles

**Files:**
- Modify: `engine/cfbm/swing_model.py` (`train`)
- Test: `engine/tests/test_swing_model.py`

**Interfaces:**
- Produces: `train(...)` output gains `"intercept": float` and `"scale": {"overall": list[float], "pass": list[float], "run": list[float]}`, each a list of 101 ascending quantiles (0%..100%) of the absolute linear score over training rows. Pass and run pool both sides (`ha_k` and `aa_k` columns), centered with `sideMean`. Also add the module constants `PASS_KEYS` and `RUN_KEYS` (tuples above) to `swing_data.py`.

- [ ] **Step 1: Write failing tests** in `test_swing_model.py`, using `_synthetic()` with `keys=["a", "b"]`. Pass and run groups get overridden by a new `groups` parameter: `train(fr, tg, keys=["a","b"], groups={"pass": ("a",), "run": ("b",)})`.
  - `test_train_keeps_intercept`: `isinstance(m["intercept"], float)` and `abs(m["intercept"]) < 0.5`.
  - `test_scale_quantiles_shape`: for each of `overall/pass/run`, `len == 101`, non-decreasing, `q[0] >= 0`.
  - `test_overall_scale_matches_linear`: recompute `|L|` for the frame with the returned coefs, then `np.median(|L|) == pytest.approx(m["scale"]["overall"][50], rel=1e-6)`.
- [ ] **Step 2:** `cd engine && uv run pytest tests/test_swing_model.py -q`. Expected: the 3 new tests FAIL (KeyError / TypeError).
- [ ] **Step 3: Implement.** `train(frame, tg, keys=KEYS, resamples=200, seed=7, groups=None)`. `groups` defaults to `{"pass": PASS_KEYS, "run": RUN_KEYS}`, filtered to `keys`. Store `beta[0]` as `intercept`. Overall quantiles come from `np.abs(X @ beta)`. Group quantiles come from `|Σ coef_k (ha_k - sideMean_k)/sd_k|` concatenated with the same over `aa_k`. Use `np.quantile(..., np.linspace(0, 1, 101))` rounded to 6 places.
- [ ] **Step 4:** Run the same command. Expected: all pass (existing tests too).
- [ ] **Step 5: Commit** `feat(engine): swing model keeps intercept and edge-score quantiles`.

### Task 2: `edge_score.py`

**Files:**
- Create: `engine/cfbm/edge_score.py`
- Test: `engine/tests/test_edge_score.py`

**Interfaces:**
- Consumes: the model dict from Task 1, a `pre` DataFrame (index = team, columns `games`, `off_<k>`, `def_<k>`) from `swing_data.pregame`, `side_advantage`, `PASS_KEYS`, `RUN_KEYS`.
- Produces:
  - `overall_linear(model, pre, home, away, neutral) -> float | None` (None if any team is missing from `pre`, or every feature is NaN)
  - `section_linear(model, pre, off, dfn, keys) -> float | None`
  - `to_score(value, quantiles: list[float]) -> float` (0.0-10.0, 1 decimal)
  - `band(score, slight=config.EDGE_SCORE_SLIGHT, big=config.EDGE_SCORE_BIG) -> "even" | "slight" | "clear"` (`score < slight` → even; `score >= big` → clear)
  - `overall_edge(model, pre, home, away, neutral) -> {"edge", "team", "score"} | None` (team = home if L>0 else away; team None when even)
  - `section_edge(model, pre, off, dfn, group: "pass" | "run") -> tuple[Edge, float] | None`, where Edge is `"even"` or `f"{band}-offense|defense"`, matching `units.edge` strings.
  - `config.EDGE_SCORE_SLIGHT = 1.0`, `config.EDGE_SCORE_BIG = 5.0` (placeholders; Task 3 replaces them).

- [ ] **Step 1: Write failing tests** with a hand-built model (`coef` 1.0 for `pass_ppa`, 0 elsewhere, `mean 0`, `sd 1`, `sideMean 0`, `intercept 0`, `home.coef 0.3`, `scale` = `list(np.linspace(0, 2, 101))` for all three) and `pre` rows built like `tests/test_swing.py::pre`:
  - `test_to_score_percentile`: `to_score(1.0, q) == 5.0`, `to_score(-1.0, q) == 5.0`, `to_score(5.0, q) == 10.0`, `to_score(0, q) == 0.0`.
  - `test_band_cutoffs`: `band(0.9, 1, 5) == "even"`, `band(1.0, 1, 5) == "slight"`, `band(5.0, 1, 5) == "clear"`.
  - `test_overall_favors_better_passing_team`: home pass_ppa off 0.3 / def 0.0, away 0.0 / 0.0, `neutral=True` → `team == home`, `score > 0`.
  - `test_neutral_drops_home_field`: equal teams, `neutral=True` → `edge == "even"` and `score == 0.0`; `neutral=False` → `overall_linear == pytest.approx(0.3)`.
  - `test_section_edge_is_one_sided`: offense pass_ppa 0.4, defense allows 0.2 → result starts with `slight-offense` or `clear-offense`; swapping the values gives `-defense`.
  - `test_nan_feature_skipped`: one team's `off_pass_ppa` is NaN and another feature has coef 1 with real values → not None, and the value equals the sum without the NaN term; all group features NaN → `section_edge(...) is None`.
- [ ] **Step 2:** `uv run pytest tests/test_edge_score.py -q`. Expected: FAIL (module not found).
- [ ] **Step 3: Implement** the functions above. NaN terms are dropped from the sums. `to_score` uses `np.interp(abs(v), q, np.linspace(0, 10, 101))`, rounded to 1.
- [ ] **Step 4:** Run the tests. Expected: PASS.
- [ ] **Step 5: Commit** `feat(engine): edge score from the swing model`.

### Task 3: Leave-one-season-out cutoffs

**Files:**
- Create: `engine/cfbm/edge_backtest.py`
- Modify: `engine/cfbm/export.py` (split `train_model` into `training_data(client, seasons) -> tuple[frame, tg] | None` plus `train_model`, which calls it), `engine/cfbm/cli.py` (new subcommand `edge-cutoffs`), `engine/cfbm/config.py`
- Test: `engine/tests/test_edge_backtest.py`

**Interfaces:**
- Consumes: `train` (Task 1); `to_score` and the linear formula (Task 2, the frame form: training rows already carry `f_k`, `home`, `home_win`).
- Produces:
  - `held_out(frame, tg) -> pd.DataFrame` with columns `season, score, favored_won` (one row per game: fit on every other season, score this season's games with that fold's model and quantiles; `favored_won` = 1 if the team with L's sign won).
  - `pick_cutoffs(df) -> tuple[float, float]`: slight = the largest c on a 0.5 grid where games with `score < c` have a favored win rate ≤ 0.58; big = the smallest c where games with `score >= c` (at least 200 of them) have a favored win rate ≥ 0.85. If big has no such c, use 9.0, and the report must say so.
  - `band_table(df, slight, big) -> list[dict]`: per band `{band, games, favoredWinRate}`.
  - CLI: `uv run python -m cfbm.cli edge-cutoffs` prints both cutoffs and the band table. It uses cached CFBD calls only (the training seasons are already in `engine/.cache`).

- [ ] **Step 1: Write failing tests** on `_synthetic()`-style data (from `test_swing_model.py`, with a `season` spread over 4 values):
  - `test_held_out_one_row_per_game`: `len(out) == len(frame)`, `0 <= score <= 10`.
  - `test_pick_cutoffs_monotone`: on a hand-built df where the win rate rises with score (`favored_won = rng.random() < 0.5 + score/20`), `slight < big` and both lie on the 0.5 grid.
  - `test_band_table_counts_sum`: the games across bands sum to `len(df)`.
- [ ] **Step 2:** `uv run pytest tests/test_edge_backtest.py -q`. Expected: FAIL.
- [ ] **Step 3:** Implement. Use `resamples=0` in folds (bootstrap isn't needed for scoring; make `train` accept 0 and skip the bootstrap, with `lo`/`hi` equal to `coef`).
- [ ] **Step 4:** Run the tests. Expected: PASS. Then run `uv run python -m cfbm.cli edge-cutoffs`. Expected: two cutoffs and a band table printed.
- [ ] **Step 5:** Write the printed cutoffs into `config.EDGE_SCORE_SLIGHT` / `EDGE_SCORE_BIG` with a comment giving the date and band table. Run the full engine suite: `uv run pytest -q`. Expected: all pass.
- [ ] **Step 6: Commit** `feat(engine): pick edge-score cutoffs by leave-one-season-out backtest`.

### Task 4: Wire the score into the data

**Files:**
- Modify: `engine/cfbm/swing.py` (`swing_block` overall), `engine/cfbm/export.py` (`matchup` sections, `game_summary` / build loop), `engine/cfbm/gotw.py`
- Test: `engine/tests/test_swing.py`, `engine/tests/test_export.py`, `engine/tests/test_gotw.py`

**Interfaces:**
- Consumes: `overall_edge`, `section_edge` (Task 2).
- Produces (data contract for Task 6):
  - `swing.overallEdge = {"edge": "even"|"slight"|"clear", "team": str|None, "score": float}` (or `None` early season).
  - Section keys: `edge` / `runEdge` keep their string format and now come from `section_edge(..., "pass" | "run")`. New sibling keys `edgeScore` / `runEdgeScore`: `float | None`. When the swing model or the pregame data is missing, `edge`/`runEdge` = the old `side_edge(rows)` and the score = `None`.
  - Home summary (`games.json` items and `m["game"]`): `edge: {"band", "team", "score"} | null`, copied from `swing.overallEdge` (null when even or missing).
  - `gotw.py` reads a new section key `rowEdge` (the old `side_edge(rows)` value, always set) instead of `edge`, so GOTW picks don't change.

- [ ] **Step 1: Write failing tests:**
  - `test_swing.py::test_overall_edge_has_score`: with `MODEL` extended by `intercept`, `home`, and `scale`, the result's `overallEdge["score"]` is between 0 and 10 and `overallEdge["edge"]` is in the band set.
  - `test_export.py::test_section_edges_fall_back_early`: a game with priors under 3 games → `edgeScore is None` and `edge == side_edge(rows)`.
  - `test_export.py::test_no_gambling_fields_exported`: walk every key in a built matchup JSON and summary; assert no key (case-insensitive) is in `{"winprob", "probability", "prob", "logit", "linear", "predictedtotal", "spread", "margin"}`, and every `score` value is in [0, 10].
  - `test_gotw.py::test_gotw_uses_row_edge`: two sections where `edge` and `rowEdge` disagree → the blurb follows `rowEdge`.
- [ ] **Step 2:** `uv run pytest tests/test_swing.py tests/test_export.py tests/test_gotw.py -q`. Expected: the new tests FAIL.
- [ ] **Step 3:** Implement per the contract. In `swing_block`, replace the averaged `weighted / weight` overall with `overall_edge(...)`. `matchup` needs the same `pre` that `_swing` uses: compute `pregame(...)` once in `matchup` and pass it to both.
- [ ] **Step 4:** Full engine suite `uv run pytest -q`. Expected: all pass. Update existing tests that asserted the old averaged overall, and note each one in the ledger.
- [ ] **Step 5: Commit** `feat(engine): edge score on overall, section and home summary`.

### Task 5: Rebuild, report, HARD STOP

**Files:**
- Create: `engine/scripts/edge_report.py` (args: `old_dir new_dir out_md`)
- Output: `docs/superpowers/plans/2026-11-10-edge-score-report.md`

- [ ] **Step 1:** Make sure no refresh run is in progress (`gh run list --repo Jkleaka53/deepcut-cfb --workflow refresh.yml -L 1` shows completed). Copy the current data: `cp -R ../web/public/data/2026 ../.superpowers/sdd/edge-score/old-2026`.
- [ ] **Step 2:** Rebuild: `cd engine && uv run python -m cfbm.cli build`. Expected: "done", with CFBD calls ≈ 10.
- [ ] **Step 3:** Write `edge_report.py`. Over finished 2026 games that have a swing section, it reports:
  1. counts by overall band, old vs new
  2. favored-team win rate by band, old vs new
  3. the share of "Even" games decided by 21+, old vs new
  4. the contradiction count for section labels (see My calls), listing them if over 5%
  5. the new labels for the three spec examples (Missouri at Ole Miss wk 7, Florida at Missouri wk 5, Texas A&M at LSU wk 4)
  6. the Task 3 held-out band table

  Run it into the report path.
- [ ] **Step 4:** Check the pass bar from the spec: new "Even" covers fewer 21+ blowouts (by share) than old; new "Big" favored win rate ≥ 0.85; Big games outnumber the old 40 Clear. If any fails, say which in the report.
- [ ] **Step 5: Commit** engine + data + report: `data: build with edge scores` (`git add engine docs web/public/data`).
- [ ] **Step 6: HARD STOP.** Show the owner the report's headline numbers in plain words. Do not start Task 6 until he says go.

### Task 6: Web: meter and chip

**Files:**
- Modify: `web/lib/types.ts` (`OverallEdge.score?: number | null`; `Section.edgeScore?`, `runEdgeScore?`; `GameSummary.edge?: { band: "even"|"slight"|"clear"; team: string|null; score: number } | null`), `web/components/matchup/EdgeCard.tsx`, `web/components/ScoreRow.tsx`, `web/lib/swing.ts`, `web/app/globals.css`
- Create: `web/components/matchup/EdgeMeter.tsx`
- Test: `web/lib/edge-meter.test.tsx`

**Interfaces:**
- Consumes: the Task 4 data contract.
- Produces: `EdgeMeter({ overall, home, away, teams })`. `edgeChipText(e: GameSummary["edge"], abbr: string): string | null` in `lib/swing.ts`.

- [ ] **Step 1: Write failing tests** (renderToString, no @testing-library):
  - `meter shows team, band and score`: `{edge:"slight", team:"Ole Miss", score:3.4}` → contains `Ole Miss`, `Slight edge`, `3.4`, and the fill element has `width:17%` (score/10 × 50%) on the Ole Miss side.
  - `meter for even says Even and has no fill`: `{edge:"even", team:null, score:0.6}` → contains `Even` and `0.6`, no fill width.
  - `meter hidden when overall is null`: renders an empty string.
  - `falls back to text when score missing`: an EdgeCard with `overall={edge:"slight", team:"X"}` and no score → contains `Overall: Slight edge X`.
  - `edgeChipText`: `({band:"slight",team:"Ole Miss",score:3.4},"OM") === "Slight edge · OM 3.4"`; `even` → `null`; `null` → `null`.
- [ ] **Step 2:** `cd web && npx vitest run lib/edge-meter.test.tsx`. Expected: FAIL.
- [ ] **Step 3: Implement to mockup A.** Title row: `<Team> · Slight edge · 3.4` (team in the accent color). Below it, a bar with a center line; the fill runs from the center toward the favored team's end, width = score × 5%. End labels: away team on the left, "Even" in the middle, home team on the right. Small legend from the config cutoffs, written out as a web constant: `0-<slight> Even · <slight>-<big> Slight · <big>+ Big` with Task 3's values. The EdgeCard puts the meter where the `edge-overall` line is now. ScoreRow adds a plain `badge` chip from `edgeChipText` after the accent chip. CSS uses tokens only, square corners, no transitions.
- [ ] **Step 4:** `npx vitest run`, then `npm run build`. Expected: all tests pass and the build succeeds (kill any `next dev -p 3123` first).
- [ ] **Step 5: Commit** `feat(web): edge meter on the game page, edge chip on the home page`.

### Task 7: Verify, review, ship

- [ ] **Step 1:** Serve `web/out` and check at 375px, light and dark: Missouri at Ole Miss (wk 7) game page meter; a neutral-site game; an early-season game (wk 2, the meter is hidden); the home week list chips. Screenshots go to absolute paths under the repo; delete `.playwright-mcp` afterwards.
- [ ] **Step 2:** Opus final review on the code-only diff (exclude `web/public/data`). Fix findings and re-run both suites.
- [ ] **Step 3:** Show the owner. Push to `main` only after he says "done". Before pushing, check no refresh run is in progress; if one landed, rebase, drop our data commit, rebuild data and recommit.
- [ ] **Step 4:** Copy the ledger to `docs/superpowers/plans/2026-11-10-edge-score-ledger.md`, delete the workspace and the branch.
