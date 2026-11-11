# Edge Score: Prior Strength and Scoring Margin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The edge score reads pregame Elo and capped scoring margin alongside its nine stats, and scores every FBS-vs-FBS game including weeks 1 to 4, with no visible change to the site.

**Architecture:** A new edge model (`engine/cfbm/edge_model.py`) is trained on all decided FBS-vs-FBS games with thin samples shrunk toward the league average. It replaces the nine-stat swing model as the source of the 0-10 score only. The swing model stays as it is and keeps driving the swing-factor card, so the engine holds two fits.

**Tech Stack:** Python (uv, pandas, numpy), existing numpy logistic fit (`swing_model.fit_logit`), Next.js static export (no web code change expected).

**Spec:** `docs/superpowers/specs/2026-11-10-edge-prior-strength-design.md` (read it first; it defines the game sets behind every number below).

## Global Constraints

- No visual change to the site; nothing says or implies it competes with oddsmakers.
- Never publish our win %, predicted margin, the model, or the Elo and margin inputs in any JSON.
- Stats strictly before kickoff; Elo must be the pregame value; FCS games excluded; postseason ordered by date.
- No new CFBD endpoints; backtests run on cached data; a live build stays at about 11 CFBD calls.
- Swing drivers stay the nine matchup stats, on the nine-stat fit, with ranks and shown numbers on real stats.
- No web or published-data change before gates 1, 2 and 3 are answered by the owner.
- Never push while a refresh run is in progress (`gh run list --limit 1`); every push needs the owner's "done".
- No en or em dashes in site copy; no animations.
- Never read or print `.env`.
- Run engine commands from `engine/` with `uv run`; tests `uv run pytest -q` (309 today), web `npx vitest run` (213 today).
- Work on a branch `edge-prior-strength`; ledger in `.superpowers/sdd/edge-prior-strength/`.

## Review Focus

1. A game whose row lacks `homePregameElo` or `awayPregameElo` (FCS opponents, odd fixtures): expect no edge score and no crash, exactly like a game with no edge today.
2. Week 1, both teams with zero games: expect a score from Elo and home field alone, no NaN in the score, and the swing card still showing its "fewer than 3 games" note.
3. One team with games and the other with none (week 2 after a bye or FCS opener): expect the played team's stats to count, shrunk, and the other team at league average.
4. A team's stats from the game being previewed leaking into its own features (bowls share week 1): expect margin and stats to use only earlier `order` values.
5. Upset Watch picking a week 1 to 4 game because every game now has an edge score: expect it to keep skipping games where either team has fewer than 3 prior FBS games.

Each has a test in the task that owns the code (Tasks 2, 2, 2, 2, 5).

## File Structure

| File | Responsibility |
|---|---|
| `engine/cfbm/edge_model.py` (new) | Margin table, shrunk pregame table, edge features, training frame, edge fit |
| `engine/cfbm/edge_audit.py` (new) | Held-out comparison tables against the market (backtest only) |
| `engine/cfbm/edge_score.py` | Score and band from the edge model's features |
| `engine/cfbm/edge_backtest.py` | `held_out` accepts any fit function |
| `engine/cfbm/swing.py` | `swing_block` takes the overall edge as an argument |
| `engine/cfbm/export.py` | Trains both fits, computes edge features per game, wires Upset Watch |
| `engine/cfbm/upset.py`, `cli.py`, `config.py` | Chance source, commands, constants |

---

### Task 1: Baseline audit command and Elo sanity check

**Files:**
- Create: `engine/cfbm/edge_audit.py`, `engine/tests/test_edge_audit.py`
- Modify: `engine/cfbm/cli.py` (new `edge-audit` subcommand)

**Interfaces:**
- Produces:
  - `edge_audit.log_loss(p: np.ndarray, y: np.ndarray) -> float`
  - `edge_audit.market_frame(games_by_id: dict[int, dict], lines_by_id: dict[int, dict], fbs_by_season: dict[int, set[str]]) -> pd.DataFrame` with columns `game_id, season, home_win, spread, book_home`; one row per decided FBS-vs-FBS game with a spread; `book_home = upset.spread_prob(spread, k)` with `k = upset.fit_spread_scale` over these rows.
  - `edge_audit.compare(held: pd.DataFrame, market: pd.DataFrame, subset: pd.Series | None = None) -> dict` returning `{"games", "modelLogLoss", "modelPicks", "marketLogLoss", "marketPicks"}`; `held` is `edge_backtest.held_out` output (uses `game_id`, `lin`), joined on `game_id`.
  - `edge_audit.elo_continuity(games: list[dict]) -> float`: share of consecutive same-season games per team where pregame Elo equals the team's previous postgame Elo.

- [ ] **Step 1: Write failing tests**

```python
def test_log_loss_matches_hand_value():
    assert round(log_loss(np.array([0.8, 0.3]), np.array([1.0, 0.0])), 4) == 0.2899

def test_compare_counts_picks_from_sign_of_lin():
    held = pd.DataFrame({"game_id": [1, 2], "lin": [2.0, 1.0]})
    market = pd.DataFrame({"game_id": [1, 2], "season": [2024, 2024], "home_win": [1, 0],
                           "spread": [-7.0, 3.0], "book_home": [0.69, 0.41]})
    out = compare(held, market)
    assert out["games"] == 2 and out["modelPicks"] == 0.5 and out["marketPicks"] == 1.0

def test_elo_continuity_is_one_when_pregame_equals_last_postgame():
    games = [_g(1, "A", "B", "2024-09-01", hpre=1500, hpost=1520, apre=1500, apost=1480),
             _g(2, "A", "C", "2024-09-08", hpre=1520, hpost=1530, apre=1400, apost=1390)]
    assert elo_continuity(games) == 1.0
```

- [ ] **Step 2: Run** `uv run pytest tests/test_edge_audit.py -q`. Expected: FAIL, module not found.
- [ ] **Step 3: Implement the four functions and the `edge-audit` command.** The command loads `training_data`, games and lines for `config.TRAIN_SEASONS` (as `upset_backtest` in `cli.py` does), prints `compare` for the current model, the by-season table, and `elo_continuity` per season.
- [ ] **Step 4: Run the tests** (PASS), then `uv run python -m cfbm.cli edge-audit`. Expected: games 5613, model log loss 0.5626 and picks 70.8%, market 0.5315 and 72.6%, k 8.7. **If these do not reproduce, stop and report.** Expected Elo continuity at or above 0.99 in every season; **if lower, stop and report** (spec caveat).
- [ ] **Step 5: Commit** `feat(engine): edge-audit baseline against the market`.

### Task 2: Margin, shrunk pregame table and edge features

**Files:**
- Create: `engine/cfbm/edge_model.py`, `engine/tests/test_edge_model.py`
- Modify: `engine/cfbm/config.py` (add `EDGE_MARGIN_CAP = 28`, `EDGE_SHRINK_K = 2.0` as a provisional value Task 3 confirms)

**Interfaces:**
- Consumes: `swing_data.KEYS`, `DIRECTION`, `stat_cols`, `pregame_adjusted`.
- Produces:
  - `EDGE_KEYS: list[str] = KEYS + ["elo", "margin"]`
  - `team_margins(games: list[dict], fbs_by_season: dict[int, set[str]], orders: dict[int, int], cap: float = config.EDGE_MARGIN_CAP) -> pd.DataFrame` with columns `game_id, season, team, order, margin`; two rows per decided FBS-vs-FBS game, margin clipped to plus or minus `cap`.
  - `margin_before(tm: pd.DataFrame, season: int, before_order: int) -> pd.DataFrame` indexed by team, columns `games, margin` (mean of earlier games).
  - `shrunk_pregame(pre: pd.DataFrame, margin: pd.DataFrame, k: float) -> pd.DataFrame` indexed by team (union of both inputs), columns `stat_cols() + ["margin"]`. Each value is `(team value - mean of that column over teams present) * n / (n + k)`, where `n` is the team's `games` in the table the column came from. NaN becomes 0.0.
  - `features(sp: pd.DataFrame, home: str, away: str, elo_home: float | None, elo_away: float | None) -> dict[str, float] | None`. None when either Elo is missing. A team absent from `sp` counts as all zeros. For each `k` in `KEYS`: `DIRECTION[k] * ((sp[home].off_k + sp[away].def_k) - (sp[away].off_k + sp[home].def_k))`; `"elo"`: `elo_home - elo_away`; `"margin"`: `sp[home].margin - sp[away].margin`.

- [ ] **Step 1: Write failing tests** (Review Focus 1 to 4):

```python
def test_margin_is_capped_and_only_counts_earlier_games():
    tm = team_margins([_game(1, "A", "B", 45, 3, week=1), _game(2, "A", "C", 10, 20, week=2)], FBS, ORDERS)
    assert margin_before(tm, 2024, 2).loc["A", "margin"] == 28      # 42 capped
    assert margin_before(tm, 2024, 3).loc["A", "margin"] == 9       # (28 - 10) / 2
    assert "A" not in margin_before(tm, 2024, 1).index              # nothing before week 1

def test_bowl_game_does_not_see_its_own_margin():
    # two postseason games both labeled week 1; orders 101 and 102
    assert margin_before(tm, 2024, 101).loc["A", "games"] == 12

def test_shrink_pulls_thin_samples_toward_zero():
    sp = shrunk_pregame(PRE, MARGIN, k=2.0)          # team A: 1 game, team B: 8 games, same raw gap from mean
    assert abs(sp.loc["A", "off_pass_ppa"]) == pytest.approx(abs(sp.loc["B", "off_pass_ppa"]) * (1/3) / (8/10))
    assert not sp.isna().any().any()

def test_features_with_no_games_is_elo_only():
    f = features(pd.DataFrame(columns=stat_cols() + ["margin"]), "H", "A", 1600, 1500)
    assert f["elo"] == 100 and all(f[k] == 0 for k in KEYS) and f["margin"] == 0

def test_one_team_with_no_games_sits_at_league_average():
    f = features(shrunk_pregame(PRE_ONLY_HOME, MARGIN_ONLY_HOME, 2.0), "H", "A", 1500, 1500)
    assert f["pass_ppa"] != 0 and not any(math.isnan(v) for v in f.values())

def test_features_none_without_elo():
    assert features(SP, "H", "A", None, 1500) is None
```

- [ ] **Step 2: Run** `uv run pytest tests/test_edge_model.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the five functions.**
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `feat(engine): margin, shrunk pregame and edge features`.

### Task 3: Edge training frame, fit, shrink choice, then GATE 1

**Files:**
- Modify: `engine/cfbm/edge_model.py`, `engine/cfbm/edge_backtest.py`, `engine/cfbm/export.py`, `engine/cfbm/cli.py`, `engine/cfbm/config.py`
- Test: `engine/tests/test_edge_model.py`, `engine/tests/test_edge_backtest.py`
- Create: `docs/superpowers/plans/2026-11-10-edge-prior-strength-report.md`

**Interfaces:**
- Consumes: Task 2 functions; `swing_model.fit_logit`; `plays.game_orders`; `swing_data.apply_orders`.
- Produces:
  - `edge_model.frame(tg: pd.DataFrame, games_by_id: dict[int, dict], fbs_by_season: dict[int, set[str]], k: float = config.EDGE_SHRINK_K) -> pd.DataFrame` with columns `game_id, season, home_win, home, scored_before` plus `f_<key>` for every `EDGE_KEYS` entry. One row per decided FBS-vs-FBS game with both Elo values. `scored_before` is True when both teams have 3 or more prior FBS games (the current model's set). It builds one shrunk table per `(season, order)` from `pregame_adjusted(..., w=config.OPP_ADJUST)` and `margin_before`, the same calls the live build makes, so training and build cannot drift.
  - `edge_model.train(frame: pd.DataFrame) -> dict`: `{"seasons", "games", "intercept", "home": {"coef"}, "features": {key: {"coef", "mean", "sd"}}, "scale": {"overall": [101 quantiles of abs linear score]}}`, values rounded as `swing_model.train` rounds them, scale built from the rounded values.
  - `edge_backtest.held_out(frame, tg=None, keys=KEYS, fit=None)`: `fit(train_rows) -> model`; default keeps today's behaviour. Output gains a `scored_before` column when the frame has one.
  - `export.edge_training_frame(client, seasons, k=config.EDGE_SHRINK_K) -> pd.DataFrame | None` and `export.train_edge_model(client, seasons) -> dict | None`.
  - `cli edge-audit` extended: for k in `(0, 1, 2, 3, 5)` print `compare` on all games, on `scored_before`, and on the rest; plus Elo-only (`keys=["elo"]`) on the rest, and the by-season table at the chosen k.

- [ ] **Step 1: Write failing tests**

```python
def test_frame_keeps_early_games_and_flags_them():
    fr = frame(TG, GAMES, FBS, k=2.0)
    wk1 = fr[fr.game_id == WEEK1_ID].iloc[0]
    assert not wk1.scored_before and wk1.f_pass_ppa == 0 and wk1.f_elo == 120

def test_frame_matches_live_features_for_the_same_game():
    row = frame(TG, GAMES, FBS, k=2.0).set_index("game_id").loc[MID_ID]
    sp = shrunk_pregame(pregame_adjusted(TG_FBS, 2024, ORDER, w=config.OPP_ADJUST), margin_before(TM, 2024, ORDER), 2.0)
    live = features(sp, HOME, AWAY, 1550, 1500)
    assert all(row[f"f_{k}"] == pytest.approx(live[k]) for k in EDGE_KEYS)

def test_train_scale_is_monotone_and_has_101_points():
    m = train(frame(TG, GAMES, FBS, k=2.0))
    q = m["scale"]["overall"]
    assert len(q) == 101 and q == sorted(q) and set(m["features"]) == set(EDGE_KEYS)

def test_held_out_accepts_a_fit_function():
    df = held_out(FRAME, keys=EDGE_KEYS, fit=train)
    assert {"season", "game_id", "lin", "score", "favored_won", "scored_before"} <= set(df.columns)
```

- [ ] **Step 2: Run** `uv run pytest tests/test_edge_model.py tests/test_edge_backtest.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** `frame`, `train`, the `held_out` change, the two `export` helpers and the CLI extension.
- [ ] **Step 4: Run** the tests (PASS), then `uv run python -m cfbm.cli edge-audit`.
- [ ] **Step 5: Choose k** by lowest all-games log loss; ties go to the smaller k. Set `config.EDGE_SHRINK_K` with a comment carrying the numbers (style of `OPP_ADJUST`).
- [ ] **Step 6: Write the report** with: all games, weeks 5+ (`scored_before`), weeks 1 to 4, each as new model vs current model (weeks 5+ only) vs market vs Elo-only (early only); the k table; by season. Fail line: weeks 5+ log loss must be below 0.5626 (audit expectation about 0.546).
- [ ] **Step 7: Commit** `feat(engine): edge model with Elo and margin, held-out report`.
- [ ] **Step 8: GATE 1. Stop. Show the owner the report tables and wait.** If it fails the line, stop the plan.

### Task 4: Upset Watch and cutoff backtests on the new model, then GATES 2 and 3

**Files:**
- Modify: `engine/cfbm/cli.py` (`edge_cutoffs`, `upset_backtest`), `engine/cfbm/upset_backtest.py` only if `join` needs the new column
- Append to: `docs/superpowers/plans/2026-11-10-edge-prior-strength-report.md`

**Interfaces:**
- Consumes: `export.edge_training_frame`, `edge_model.train`, `edge_backtest.held_out(..., keys=EDGE_KEYS, fit=train)`.

- [ ] **Step 1:** Point `edge_cutoffs` at the edge model's held-out frame (all games). Point `upset_backtest` at the same frame filtered to `scored_before`, and print the all-games summary as a second, labeled line. No published data changes.
- [ ] **Step 2: Run** `uv run pytest -q`. Expected: PASS (update any CLI test that pinned the old source).
- [ ] **Step 3: Run** `uv run python -m cfbm.cli upset-backtest` and `edge-cutoffs`. Add to the report: Upset Watch cover rate, outright rate and book rate against the bar (cover above 50%, outright above the book; today 52.7%, 31.0% vs 25.9%), per season; the band table at the suggested cutoffs and at 2.0 / 8.0; 2026 finished games at both cutoff pairs (favored team's win rate per band and game counts), computed from a local, unpublished build into a temp directory.
- [ ] **Step 4: Commit** `feat(engine): backtests read the edge model`.
- [ ] **Step 5: GATES 2 and 3. Stop. Show the owner both tables and wait.** Record his answers in the report:
  - Gate 2: passes, or he chooses "Upset Watch stays on the nine-stat model", or "change its rule" (a rule change is a new design, outside this plan; in that case Task 5 keeps Upset Watch on the nine-stat model until then).
  - Gate 3: his cutoff pair.

### Task 5: Wire the edge model into the build

**Files:**
- Modify: `engine/cfbm/edge_score.py`, `engine/cfbm/swing.py`, `engine/cfbm/export.py`, `engine/cfbm/upset.py`, `engine/cfbm/config.py`
- Test: `engine/tests/test_edge_score.py`, `test_swing.py`, `test_export.py`, `test_upset.py`

**Interfaces:**
- Consumes: Tasks 2 and 3.
- Produces:
  - `edge_score.linear(model: dict, feats: dict[str, float], neutral: bool) -> float` and `edge_score.edge(model: dict, feats: dict[str, float] | None, home: str, away: str, neutral: bool) -> dict | None` returning `{"edge", "team", "score"}` as `overall_edge` does today.
  - `swing.swing_block(model, home, away, pre, neutral, raw=None, overall: dict | None = None)`: no longer computes the overall edge; it puts `overall` in `overallEdge` in both the normal and the "too early" return.
  - `export.build(..., model=None, edge_model=None, ...)`; `export.matchup(d, g, model=None, edge_model=None)`; `_Data` gains a cached `edge_feats(g, order) -> dict | None` built from `shrunk_pregame` and `features` with `g["homePregameElo"]`, `g["awayPregameElo"]`.
  - `upset.our_prob(edge_model: dict, feats: dict | None, neutral: bool) -> float | None` when gate 2 passed. If the owner chose the nine-stat model, `our_prob` and `edge_score.overall_linear` stay exactly as they are and only the filter below is added.
  - `export.upset_picks`: skip a game when either team has fewer than `MIN_PRIOR` games in `_pregame(d, g, order)`.
  - `config.EDGE_SCORE_SLIGHT` / `EDGE_SCORE_BIG` set to the gate 3 answer, comment updated.

- [ ] **Step 1: Write failing tests**

```python
def test_edge_uses_elo_when_stats_are_empty():
    e = edge(EDGE_MODEL, {**{k: 0.0 for k in KEYS}, "elo": 400.0, "margin": 0.0}, "H", "A", neutral=True)
    assert e["team"] == "H" and e["score"] > 0

def test_edge_none_without_features():
    assert edge(EDGE_MODEL, None, "H", "A", False) is None

def test_swing_card_is_unchanged_by_the_edge_model():
    before = json.loads((FIXTURES / "swing_block_pin.json").read_text())   # captured from main before this task
    after = swing_block(SWING_MODEL, HOME, AWAY, PRE, False, raw=RAW, overall=None)
    assert after["drivers"] == before["drivers"] and after["keyRows"] == before["keyRows"]

def test_early_game_has_edge_score_and_too_early_note(tmp_path):
    m = _build_and_load(tmp_path, WEEK1_ID)
    assert m["swing"]["overallEdge"]["score"] >= 0 and m["swing"]["drivers"] == []
    assert "fewer than 3 games" in m["swing"]["note"]

def test_game_without_elo_has_no_edge(tmp_path):
    assert _build_and_load(tmp_path, NO_ELO_ID)["swing"]["overallEdge"] is None

def test_upset_watch_skips_games_with_thin_samples(tmp_path):
    assert str(WEEK2_KEY) not in _build_upset(tmp_path)

def test_published_json_has_no_elo_or_margin(tmp_path):
    # extend BANNED in test_export.py with "elo", "pregameelo", "homepregameelo", "awaypregameelo"
```

Capture `swing_block_pin.json` from the current code first (a short script in the test's fixture setup, run once on `main`). Add `homePregameElo` / `awayPregameElo` to the `WorldClient` game fixtures, leaving one game without them.

- [ ] **Step 2: Run** `uv run pytest -q`. Expected: the new tests FAIL.
- [ ] **Step 3: Implement.** Remove `edge_score.overall_edge`; remove `overall_linear` too unless gate 2 kept Upset Watch on the nine-stat model.
- [ ] **Step 4: Run** `uv run pytest -q` (PASS) and confirm `test_export.py`'s check that `model.json` is not written still passes and covers the edge model.
- [ ] **Step 5: Commit** `feat(engine): edge score reads the edge model in the build`.

### Task 6: Rebuild, check the site, hand to the owner

**Files:**
- Modify: `web/lib/swing.ts` only if the cutoffs changed (`EDGE_SLIGHT` / `EDGE_BIG`), `web/public/data/**` (rebuilt), `README.md` if it describes the model's inputs
- Append to: the report

- [ ] **Step 1:** Check no refresh run is in progress, then `cd engine && uv run python -m cfbm.cli build` (about 100s). Confirm "CFBD calls made" is about 11.
- [ ] **Step 2:** Compare old and new labels with `uv run python scripts/edge_report.py <old 2026 dir> <new 2026 dir> <out.md>` (copy `web/public/data/2026` aside before building). Add to the report: label counts before and after, how many favored teams flipped, and which Game of the Week, Shootout and Upset Watch picks changed in 2026.
- [ ] **Step 3:** `cd web && npx vitest run && npm run build`. Expected: PASS. If cutoffs changed, update `swing.ts` and its tests first.
- [ ] **Step 4:** Preview (`npx serve out -l 4319`) and check by eye: a 2026 week 1 game page shows the edge meter and the "fewer than 3 games" swing note; the week 1 home chips show edge labels; a week 11 game's swing pulldowns match the live site; nothing mentions odds beyond Upset Watch's DraftKings bar. Kill the server after.
- [ ] **Step 5: Commit** code and data separately (`feat(web): ...` if any, `data: rebuild on edge model`).
- [ ] **Step 6:** Final review by a fresh reviewer on the most capable model over the code-only diff (`git diff main HEAD -- . ':!web/public/data'`), with the spec and the Review Focus list. Fix findings.
- [ ] **Step 7: Stop. Show the owner the before-and-after summary and the local preview. Push and merge only on his "done"** (check for a running refresh first). Then copy the ledger to `docs/superpowers/plans/2026-11-10-edge-prior-strength-ledger.md`, delete the workspace and the branch.
