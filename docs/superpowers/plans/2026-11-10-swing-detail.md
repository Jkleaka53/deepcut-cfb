# Swing Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each reason in "What could swing this game" becomes a pulldown that opens in place. Opened, it shows what the stat means, the actual numbers and ranks behind the edge, why the stat matters, and a clearer, checkable "what to watch".

**Architecture:** The engine adds a `detail` block to each swing driver: plain-English meaning, the offense's pregame value, what the defense allows, the FBS average, a value format, and a "why it matters" sentence built from a per-stat historical rate the swing model now computes. Cues are rewritten. The web turns each driver `<li>` into a native `<details name="swing">` (closed by default, one open at a time, no JS), with the old one-line layout as the summary.

**Tech Stack:** Python (uv, pandas, numpy, pytest), Next.js 15 static export, React 19, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-edge-score-shootout-upset-design.md`, "Slice 2: Swing detail". Mockup: `docs/superpowers/specs/2026-11-10-mockups/swing-detail.html`.

## Global Constraints

- Not for gambling: no win % for this game, no predicted score. The only rate shown is the historical "won the game X% of the time" line, which describes past seasons in general (owner approved it explicitly). Never for this matchup.
- The model is never published (no `model.json`; `test_swing_block_with_injected_model` enforces it). The historical rate reaches the page only as text inside each driver.
- Pulldown, opens in place on the game page, closed by default, one open at a time (owner).
- Plain English. "Standard downs" never appears without its definition. It must be clear that "first and second down" means any series, not the first two plays of a drive (owner's question).
- No animations, square corners, tokens only, light + dark, works at 375px.
- Data JSON (`web/public/data`) only changes through `cfbm.cli build`.

## My calls

- **"Won this matchup"** = the team with the better side of that stat's matchup (sign of `f_k` in the training frame). `matchupWinRate_k` = the share of training games with `f_k != 0` where that team won. Computed in `swing_model.train`, rounded to 3 places.
- **"Why it matters" copy** (engine-built string), with `{n}` = the count of proven features, `{since}` = the first training season, `{pct}` = `round(100 * matchupWinRate)`:
  `"One of the {n} stats the model found actually decide games. Since {since}, the team with the better side of this matchup won {pct}% of the time."`
- **The table** in the opened view has three rows, labeled `"{offense} offense"`, `"{defense} defense allows"` and `"FBS average"`. Columns are the value and the rank (`"8th of 134"`; blank for the average). The rank comes from the existing `offRank` / `defRank` / `of`. The FBS average = the mean of `pre[f"off_{k}"]` over teams in `pre`.
- **Value formats by key:** `pct` for `sd_sr`, `pd_sr`, `pass_sr`, `rush_sr`, `stuff` (e.g. 52.1%). `epa` for `pass_ppa`, `rush_ppa` (signed, 2 decimals, e.g. +0.21). `num` for `explosive`, `line_yards` (2 decimals).
- **Old JSON** (drivers without `detail`): render as today, with no pulldown.
- **Scope of the copy rewrite:** the spec says to rewrite "all nine CUES and EXPLAIN texts". Here that means the nine swing stats (`MEANING` is new, replacing nothing). The unit-table row `EXPLAIN` strings in `units.py` describe different stats and stay as they are.
- **Section heading inside the open view:** "Why {favors} has the edge" (spec mockup), using `d.favors`.
- **Cue structure:** each cue = a marker sentence (below) + the same suffix: `" If {off} does that often, {off}'s offense is winning this matchup; if not, {def}'s defense is."` This replaces "this edge is playing out", which read wrong when the defense was the one with the edge.

### Copy (exact)

MEANING:
- `sd_sr`: "How often the offense has a successful play on normal downs: every 1st down, 2nd-and-7 or shorter, and 3rd or 4th-and-4 or shorter, on any set of downs in a drive (not just the first two plays). Successful means gaining half the yards needed on 1st down, 70% on 2nd, and all of it on 3rd or 4th."
- `pd_sr`: "How often the offense has a successful play when it's behind schedule: 2nd-and-8 or longer, and 3rd or 4th-and-5 or longer. Successful means gaining 70% of the yards needed on 2nd down, and all of it on 3rd or 4th."
- `pass_sr`: "How often a pass play is successful: half the yards needed on 1st down, 70% on 2nd, all of it on 3rd or 4th. Sacks count as pass plays."
- `rush_sr`: "How often a run is successful: half the yards needed on 1st down, 70% on 2nd, all of it on 3rd or 4th."
- `pass_ppa`: "Points added per pass: how much the average pass play moves the offense toward scoring, based on down, distance and field position. Above zero helps the offense."
- `rush_ppa`: "Points added per run: how much the average run moves the offense toward scoring, based on down, distance and field position. Above zero helps the offense."
- `explosive`: "How big the good plays are: the average points added on the offense's successful plays. High numbers mean chunk gains, not just steady ones."
- `stuff`: "How often a run is stopped at or behind the line of scrimmage. Lower is better for the offense, higher is better for the defense."
- `line_yards`: "Yards per carry credited to the offensive line: the first 4 yards count fully, yards 5 to 10 count half, and losses count extra."

CUE markers (the suffix above is appended):
- `sd_sr`: "Watch {off} on 1st down: gaining 4 or more yards keeps them out of 3rd-and-long."
- `pd_sr`: "Watch {off} on 3rd-and-5 or longer: converting there keeps drives alive."
- `pass_sr`: "Watch whether {off}'s passes gain enough to stay ahead of the chains, not just whether they're caught."
- `pass_ppa`: "Watch {off}'s first few drives through the air: completions of 15 or more yards."
- `rush_ppa`: "Watch for {off} runs of 10 or more yards against {def}."
- `rush_sr`: "Watch whether {off}'s runs gain 4 or more yards on 1st down."
- `explosive`: "Watch for {off} plays of 20 or more yards; one or two can decide it."
- `line_yards`: "Watch {off}'s runs between the tackles: 4 or more yards a carry means the line is winning."
- `stuff`: "Watch how often {def} stops {off}'s runs at or behind the line."

## Review Focus

1. **Old JSON without `detail`** (a cached page): the driver renders exactly as today, with no `<details>` and no crash. → Task 2 test `old driver without detail renders flat`.
2. **A NaN value** (the stat is missing for the defense team): the table cell shows "n/a", not "NaN%". → Task 1 test `test_detail_values_none_when_missing`, Task 2 test `missing value shows n/a`.
3. **A defense-favored driver:** the heading says "Why {defense} has the edge", and the cue suffix still reads correctly. → Task 2 test `heading names the favored team`.
4. **The `stuff` direction** (lower is better for the offense): the raw values shown aren't direction-flipped, and the meaning says which way is good. → Task 1 test `test_stuff_values_raw`.
5. **Long team names at 375px** ("Louisiana-Monroe defense allows"): the table wraps without sideways scroll. → Task 3 visual check.

---

### Task 1: Engine: driver detail and the historical rate

**Files:**
- Modify: `engine/cfbm/swing_model.py` (`train`), `engine/cfbm/swing.py` (`CUES`, new `MEANING`, `FORMAT`, `CUE_SUFFIX`, driver build)
- Test: `engine/tests/test_swing_model.py`, `engine/tests/test_swing.py`

**Interfaces:**
- Produces:
  - `train(...)["features"][k]["matchupWinRate"]: float` (0-1, 3 decimals).
  - Each driver gains `detail: {"meaning": str, "format": "pct"|"epa"|"num", "offValue": float|None, "defAllows": float|None, "fbsAvg": float|None, "why": str}`. Values are raw pregame means (`pre.loc[off, f"off_{k}"]`, `pre.loc[dfn, f"def_{k}"]`), rounded to 4 places, with None for NaN.
  - The driver's `cue` is rebuilt as marker + suffix.

- [ ] **Step 1: Write failing tests:**
  - `test_swing_model.py::test_matchup_win_rate`: on `_synthetic()`, `0.5 < m["features"]["a"]["matchupWinRate"] <= 1` and `abs(m["features"]["b"]["matchupWinRate"] - 0.5) < 0.05`.
  - `test_swing.py::test_driver_detail_shape`: using `MODEL` (each feature gets `"matchupWinRate": 0.64`, and `"seasons": [2015, 2016]` added to MODEL) and the existing Oregon/Michigan pre, every driver has `set(d["detail"]) == {"meaning", "format", "offValue", "defAllows", "fbsAvg", "why"}`; for an `sd_sr` driver, `"not just the first two plays" in meaning`, `format == "pct"`, and `why == "One of the 4 stats the model found actually decide games. Since 2015, the team with the better side of this matchup won 64% of the time."`
  - `test_swing.py::test_cue_suffix_names_both_sides`: every cue ends with `f"If {d['offense']} does that often, {d['offense']}'s offense is winning this matchup; if not, {d['defense']}'s defense is."`, and no cue contains "this edge is playing out".
  - `test_swing.py::test_detail_values_none_when_missing`: set Michigan's `def_pass_ppa` to NaN in the pre where Oregon's pass_ppa driver fires. That driver is skipped today when the advantage is NaN, so assert instead: no driver anywhere has a NaN `offValue`/`defAllows` (each is a float or None).
  - `test_swing.py::test_stuff_values_raw`: a `stuff` driver (give `stuff` `proven` + importance in a local model copy) has `offValue == round(pre.loc[off, "off_stuff"], 4)`, not negated.
- [ ] **Step 2:** `cd engine && uv run pytest tests/test_swing.py tests/test_swing_model.py -q`. Expected: the new tests FAIL (KeyError / assertion).
- [ ] **Step 3: Implement.** In `train`, compute `matchupWinRate` per feature from `frame[f"f_{k}"]` and `frame["home_win"]` (see My calls). In `swing.py`, add `MEANING`, `FORMAT`, the rewritten `CUES`, and `CUE_SUFFIX` with the exact copy above. In `swing_block`, `n = sum(f["proven"] for f in feats.values())` and `since = min(model["seasons"])`; build `detail` per candidate. FBS average = `float(pre[f"off_{k}"].mean())`.
- [ ] **Step 4:** `uv run pytest -q`. Expected: all pass. Update the existing tests that asserted old cue text, and note each in the ledger.
- [ ] **Step 5: Commit** `feat(engine): swing drivers carry stat detail and a clearer cue`.

### Task 2: Web: the pulldown

**Files:**
- Modify: `web/lib/types.ts` (`Driver.detail?: DriverDetail`), `web/components/matchup/SwingCard.tsx`, `web/lib/swing.ts` (`formatStat`), `web/app/globals.css`
- Test: `web/lib/swing-detail.test.tsx`

**Interfaces:**
- Consumes: the Task 1 `detail` shape.
- Produces: `formatStat(v: number | null | undefined, f: "pct" | "epa" | "num"): string` → `"52.1%"`, `"+0.21"` / `"-0.05"`, `"1.27"`, `"n/a"` for null/undefined/NaN.

- [ ] **Step 1: Write failing tests** (renderToString; a driver fixture with `detail` = `{meaning:"M", format:"pct", offValue:0.521, defAllows:0.47, fbsAvg:0.44, why:"W"}`, offense Ole Miss, defense Missouri, favors Ole Miss, offRank 8, defRank 96, of 134):
  - `formatStat`: `(0.521,"pct")==="52.1%"`, `(0.214,"epa")==="+0.21"`, `(-0.05,"epa")==="-0.05"`, `(1.274,"num")==="1.27"`, `(null,"pct")==="n/a"`, `(NaN,"num")==="n/a"`.
  - `driver with detail is a closed details`: the html contains `<details`, contains `name="swing"`, and does not contain ` open`.
  - `opened content shows meaning, table, why, cue`: contains `M`, `Ole Miss offense`, `52.1%`, `8th of 134`, `Missouri defense allows`, `47.0%`, `96th of 134`, `FBS average`, `44.0%`, `W`, and the cue text.
  - `heading names the favored team`: contains `Why Ole Miss has the edge`; with `favors:"Missouri"`, contains `Why Missouri has the edge`.
  - `missing value shows n/a`: `defAllows:null` → contains `n/a`, not `NaN`.
  - `old driver without detail renders flat`: no `detail` → no `<details`, label and cue still present.
- [ ] **Step 2:** `cd web && npx vitest run lib/swing-detail.test.tsx`. Expected: FAIL.
- [ ] **Step 3: Implement.** Each driver with `detail` renders `<details name="swing" className="swing-item">`. The `<summary>` holds today's number, label, edge badge and matchup line, plus a chevron (`ChevronDown` from lucide-react, rotated by CSS on `[open]`, with no transition). The body has three small labeled blocks, "What it means", "Why {favors} has the edge" (the table) and "Why it matters", then "What to watch" (cue). Labels use the `.swing-sub` style family. The table uses `table-layout: fixed` with wrapping first-column text. If TypeScript rejects `name` on `<details>`, pass it via a spread (`{...{ name: "swing" }}`) and ledger it.
- [ ] **Step 4:** `npx vitest run && npx tsc --noEmit && npx eslint components lib`. Expected: all pass, no errors.
- [ ] **Step 5: Commit** `feat(web): swing reasons open to show the stats behind them`.

### Task 3: Rebuild, verify, review, ship

- [ ] **Step 1:** Check no refresh run is in progress (`gh run list --repo Jkleaka53/deepcut-cfb --workflow refresh.yml -L 1` → completed). Then `cd engine && uv run python -m cfbm.cli build`. Expected: done, CFBD calls ≈ 10. Then `cd ../web && npm run build`. Expected: exit 0.
- [ ] **Step 2:** Spot-check the data: `sd_sr` drivers this season show a `why` with a believable rate (50-80%). Record the nine `matchupWinRate`s in the ledger. If any proven stat is ≤ 50%, stop and rule (the "why" line would be misleading).
- [ ] **Step 3:** Serve `web/out` and check at 375px, light and dark: a game page with 3+ drivers. All closed at load; opening one closes another; a long-name team table wraps; no horizontal scroll (`scrollWidth <= 375`). Screenshots go to absolute paths in the workspace; delete `.playwright-mcp` afterwards.
- [ ] **Step 4: Commit data** `data: build with swing detail`.
- [ ] **Step 5:** Opus final review on the code-only diff (exclude `web/public/data`). Fix findings TDD-style.
- [ ] **Step 6:** Show the owner. Push to `main` only after he says "done" (check for refresh runs first). Copy the ledger to `docs/superpowers/plans/2026-11-10-swing-detail-ledger.md`, delete the branch and workspace, and update the project memory.
