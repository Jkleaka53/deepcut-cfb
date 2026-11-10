# CFB Matchups Slice 1 (Spike + Pass Phase, Live) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first live version: a weekly-refreshed web app listing every FBS game for 2025 and 2026 with search and favorites, where each FBS-vs-FBS game has a pass-phase matchup page (unit vs. unit tables and opponent-tier splits, this game's tier highlighted).

**Architecture:** A Python engine (`engine/`) pulls CollegeFootballData (CFBD) into a disk cache, computes per-team-game pass stats from play-by-play, ranks teams into thirds per skill, builds splits and unit tables, and writes static JSON into `web/public/data/`. A Next.js static-export site (`web/`) reads that JSON in the browser. A weekly GitHub Actions job runs the engine and commits the JSON; Vercel redeploys on push.

**Tech Stack:** Python ≥3.12 via `uv`, `requests`, `pandas`, `pytest`, `responses` (HTTP mocking). Next.js 15 (App Router, `output: "export"`), TypeScript, Vitest. GitHub Actions, Vercel.

**Spec:** `docs/superpowers/specs/2026-11-10-cfb-matchups-design.md`. Slices 2 to 4 (swing factors, overall edge, Game of the Week, run phase) are out of scope here and get their own plans.

## Global Constraints

- Disclaimer, verbatim, in the footer of every page and as the first line under the README title: **"Not for gambling or betting. CFB Matchups is a personal statistics project."**
- No betting lines, spreads, odds, win percentages, predicted scores or point margins anywhere.
- Free data only: CFBD API at `https://api.collegefootballdata.com`, Bearer auth, key from env var `CFBD_API_KEY`. Never commit the key. Never call CFBD from the website.
- Garbage time excluded everywhere: a play is garbage when the pre-play absolute margin is > 38 in period 2, > 28 in period 3, or > 22 in period 4.
- Passing down: (down == 2 and distance >= 8) or (down in 3, 4 and distance >= 5). Everything else is a standard down.
- Tiers are thirds of FBS for one skill: tier 1 = top third (best), 2 = middle, 3 = bottom. Ranked by the skill's own numbers, never AP rank or record.
- Splits and tiers exclude games against non-FBS opponents.
- Every split row shows games and plays. A row is `smallSample` when games < 3 or plays < 60.
- Player splits cover the whole FBS career since `CAREER_START_SEASON = 2021`, across schools. Team-unit splits cover the current season plus the previous season.
- For a game in week W, stats use only games strictly before it in the same season (postseason games see the full regular season). Past seasons' opponent tiers use that opponent's full-season numbers.
- Early season: for a game with regular-season week W < 5, team numbers = w × this-season + (1 − w) × last-season with w = (W − 1) / 4. A team with no last-season FBS data uses this season only. These pages show "Early-season data: numbers blend last season with this season."
- Bowl and playoff pages show "Bowl rosters can differ from season numbers because of opt-outs and transfers." Neutral-site games show "Neutral site" in place of home/away.
- No NaN or Infinity in JSON. Missing values are `null`.
- No pill-shaped buttons (square corners). Must work at 375px wide with no horizontal scroll. It must not look like a sportsbook.
- Code lives at `~/dev/cfb-matchups`, never under `~/Documents`. `.superpowers/`, `engine/.cache/` and `.env` are git-ignored.
- Creating the GitHub repo, pushing, and connecting Vercel are outward-facing. Do them only after the owner says go (Task 14).

## Review Focus

1. **Starting QB changed mid-season or split time in a game.** The primary passer is the player with ≥ 75% of team attempts. Games below that count for nobody, and the matchup page uses the most recent primary passer. Tests in Task 7.
2. **FBS team playing an FCS opponent.** The game is listed with `hasBreakdown: false`, and FCS games never enter tiers or splits. Tests in Tasks 6 and 8.
3. **Week 1, a team new to FBS, or a team with zero dropbacks against a tier.** Rates come out `null`, not NaN, and the page shows "No games" for that row. Tests in Tasks 5 and 10.
4. **Postseason and neutral-site games.** The week cutoff includes the whole regular season, there is no home/away wording, and the bowl note shows. Tests in Tasks 5 and 10.
5. **Browser storage blocked and accented or special team names** ("Hawai'i", "San José State", "Texas A&M"). Favorites fall back to empty without crashing, and search matches "san jose" and "hawaii". Tests in Task 11.

---

## File Structure

```
cfb-matchups/
  README.md                         disclaimer, what it is, methods, limits
  .gitignore
  .github/workflows/refresh.yml     weekly engine run + commit JSON
  docs/spike-notes.md               spike findings (Task 2)
  engine/
    pyproject.toml
    cfbm/
      config.py        all constants from Global Constraints + spike decisions
      cfbd_client.py   HTTP + disk cache
      fetch.py         incremental pulls (games, plays, player box scores, advanced stats, FBS teams)
      plays.py         raw plays -> normalized PlayFrame
      team_stats.py    team-game pass stats, season profiles, early-season blend
      tiers.py         thirds per skill
      qb.py            primary passer per team-game, career game logs
      splits.py        opponent-tier split tables
      units.py         unit-vs-unit tables + edge
      export.py        JSON writer (contract below)
      cli.py           `uv run python -m cfbm.cli build`
    spike/pressure_spike.py
    tests/ (one test file per module, fixtures in tests/fixtures/)
  web/
    next.config.ts     output: "export"
    lib/types.ts       JSON contract types
    lib/data.ts        fetch helpers
    lib/search.ts      normalize + match
    lib/favorites.ts   localStorage with fallback
    app/layout.tsx     nav + disclaimer footer
    app/page.tsx       home
    app/game/page.tsx  matchup page (?id=)
    components/        GameRow, UnitTable, SplitTable, Disclaimer
    public/data/       generated JSON (committed)
```

## JSON Contract (engine writes, web reads)

Files: `web/public/data/index.json`, `web/public/data/{season}/games.json`, `web/public/data/{season}/matchups/{gameId}.json`, `web/public/data/players.json`.

```ts
// web/lib/types.ts — engine/cfbm/export.py must emit exactly these shapes (camelCase keys)
export type Tier = 1 | 2 | 3;
export type Edge = "even" | "slight-offense" | "clear-offense" | "slight-defense" | "clear-defense" | null;
export interface Index { seasons: number[]; currentSeason: number; currentWeek: number; seasonType: "regular" | "postseason"; generatedAt: string; }
export interface GameSummary { id: number; season: number; week: number; seasonType: "regular" | "postseason"; start: string; home: string; away: string; homeConf: string | null; awayConf: string | null; neutral: boolean; venue: string | null; completed: boolean; homePoints: number | null; awayPoints: number | null; hasBreakdown: boolean; }
export interface UnitRow { key: string; label: string; format: "pct" | "epa"; offense: { value: number | null; rank: number | null }; defense: { value: number | null; rank: number | null }; edge: Edge; }
export interface UnitTable { title: string; offenseTeam: string; defenseTeam: string; rows: UnitRow[]; }
export interface SplitRow { tier: Tier; games: number; plays: number; smallSample: boolean; metrics: Record<string, number | null>; }
export interface SplitTable { title: string; subject: string; tierSkill: TierSkill; seasons: number[]; highlightTier: Tier | null; metricLabels: Record<string, string>; metricFormats: Record<string, "pct" | "epa">; rows: SplitRow[]; }
export type TierSkill = "pass_defense" | "pass_rush" | "pass_offense" | "pass_protection";
export interface Section { offenseTeam: string; defenseTeam: string; units: UnitTable[]; splits: SplitTable[]; }
export interface Matchup { game: GameSummary; earlySeason: boolean; notes: string[]; quarterbacks: Record<string, { athleteId: number; name: string } | null>; sections: Section[]; }
export interface PlayerEntry { athleteId: number; name: string; team: string; position: "QB"; season: number; }
```

`Matchup.sections` always has two entries: away offense vs. home defense first, then home offense vs. away defense. `SplitRow` rows always come in tier order 1, 2, 3, all three present even when a tier has 0 games.

---

### Task 1: Repo, engine skeleton, CFBD client with disk cache

**Files:**
- Create: `.gitignore`, `README.md`, `engine/pyproject.toml`, `engine/cfbm/__init__.py`, `engine/cfbm/config.py`, `engine/cfbm/cfbd_client.py`
- Test: `engine/tests/test_cfbd_client.py`

**Interfaces:**
- Produces: `class CfbdClient(api_key: str, cache_dir: Path, base_url: str = config.CFBD_BASE_URL)` with `get(path: str, params: dict, *, cacheable: bool = True) -> list | dict` and attribute `calls_made: int`. Cache file = `cache_dir / sha1(path + sorted params).json`. Raises `CfbdError` on non-2xx (message includes status and path).
- Produces: `config.py` constants: `CFBD_BASE_URL`, `GARBAGE_MARGIN = {2: 38, 3: 28, 4: 22}`, `CAREER_START_SEASON = 2021`, `DISPLAY_SEASONS = (2025, 2026)`, `PRIMARY_QB_SHARE = 0.75`, `MIN_SAMPLE_GAMES = 3`, `MIN_SAMPLE_PLAYS = 60`, `EARLY_SEASON_LAST_WEEK = 4`, `EDGE_SLIGHT = 15`, `EDGE_CLEAR = 35` (percentile points), `PRESSURE_PROXY = "TBD_BY_SPIKE"`, `CPOE_AVAILABLE = False`, `DISCLAIMER`, `BOWL_NOTE`, `EARLY_NOTE` (exact strings from Global Constraints).

- [ ] **Step 1:** `cd ~/dev/cfb-matchups && git init -b main`. Write `.gitignore` (`.superpowers/`, `engine/.cache/`, `.env`, `__pycache__/`, `.venv/`, `web/node_modules/`, `web/.next/`, `web/out/`). Write `README.md` with the title and the disclaimer line only, for now. `uv init --package --name cfbm engine` (or hand-write `pyproject.toml`, requires-python ">=3.12"), `uv add requests pandas`, `uv add --dev pytest responses`.
- [ ] **Step 2: Write the failing tests** in `engine/tests/test_cfbd_client.py`:

```python
@responses.activate
def test_get_sends_bearer_and_caches(tmp_path):
    responses.get("https://api.collegefootballdata.com/games", json=[{"id": 1}])
    c = CfbdClient("KEY", tmp_path)
    assert c.get("/games", {"year": 2025, "week": 1}) == [{"id": 1}]
    assert c.get("/games", {"week": 1, "year": 2025}) == [{"id": 1}]   # param order irrelevant
    assert len(responses.calls) == 1 and c.calls_made == 1
    assert responses.calls[0].request.headers["Authorization"] == "Bearer KEY"

@responses.activate
def test_uncacheable_always_refetches(tmp_path): ...  # cacheable=False -> 2 HTTP calls for 2 gets

@responses.activate
def test_error_raises_with_status(tmp_path):
    responses.get("https://api.collegefootballdata.com/plays", status=429)
    with pytest.raises(CfbdError, match="429"):
        CfbdClient("KEY", tmp_path).get("/plays", {"year": 2025})
```

- [ ] **Step 3:** Run `cd engine && uv run pytest tests/test_cfbd_client.py -v` → FAIL (import error).
- [ ] **Step 4:** Implement `config.py` and `cfbd_client.py` as specified in Interfaces. An uncacheable response is still written to the cache (it refreshes the file).
- [ ] **Step 5:** Run the tests → PASS.
- [ ] **Step 6:** Commit, including the spec and this plan: `git add -A && git commit -m "chore: scaffold repo, engine package, cached CFBD client"`.

### Task 2: Spike: what the free data really supports (no TDD, throwaway script)

Needs the owner's CFBD API key in `~/dev/cfb-matchups/.env` as `CFBD_API_KEY=...` (ask the owner if it isn't there).

**Files:**
- Create: `engine/spike/pressure_spike.py`, `docs/spike-notes.md`
- Modify: `engine/cfbm/config.py` (set `PRESSURE_PROXY`, `CPOE_AVAILABLE`, `PLAY_TYPES`)

- [ ] **Step 1:** Using `CfbdClient`, pull 2025 regular-season `/plays` for weeks 5–7 (`year`, `week`, `seasonType=regular`), plus `/games/players` for one of those weeks, and `/stats/season/advanced?year=2025`. Record `calls_made`.
- [ ] **Step 2:** Answer each of these in `docs/spike-notes.md`, with counts:
  1. Every distinct `playType` and its count. Which ones are dropbacks (passes, sacks, interceptions, pass TDs)?
  2. Are `offenseScore`/`defenseScore` pre-play or post-play? Check scoring plays.
  3. Scrambles: what share of QB rush plays have play text containing "scramble"? Is it high enough to trust (rough bar: some appear for most teams)? Throwaways: does any incompletion text say "thrown away"? Is intentional grounding a penalty play or does it appear in text?
  4. Does any endpoint give per-game or per-player CPOE on the free tier? Check `/stats/game/advanced` and `/ppa/players/games` fields.
  5. Is `/stats/season/advanced` `defense.havoc.frontSeven` present?
  6. Does the passer's `athleteId` in `/games/players` stay the same across a transfer? Check John Mateer: Washington State 2024 vs. Oklahoma 2025.
  7. Week numbering for postseason (`seasonType=postseason`): what week values appear?
  8. Estimated total call count for the initial backfill (2021–2026).
- [ ] **Step 3:** Decide and write into `config.py`, citing the notes: `PRESSURE_PROXY = "pressure_est"` if scrambles or throwaways are detectable for most teams, else `"front_seven_havoc"`. `CPOE_AVAILABLE`. `PLAY_TYPES = {"pass": {...}, "sack": {...}, "interception": {...}, "rush": {...}}`, the exact strings found. Add regex constants `SCRAMBLE_RE`, `THROWAWAY_RE`, `GROUNDING_RE` if used.
- [ ] **Step 4:** Report findings to the owner in plain words (especially if pressure can't be estimated) before continuing. Commit: `git commit -m "spike: CFBD data capabilities, pressure proxy decision"`.

### Task 3: Normalize play-by-play

**Files:**
- Create: `engine/cfbm/plays.py`, `engine/tests/fixtures/plays_sample.json` (≈15 hand-picked raw plays copied from the spike cache: pass, sack, INT, scramble, rush, punt, penalty, passing-down pass, garbage-time pass, one each in periods 2/3/4 around the thresholds)
- Test: `engine/tests/test_plays.py`

**Interfaces:**
- Produces: `normalize_plays(raw: list[dict], season: int, season_type: str) -> pd.DataFrame` with columns `game_id, season, week, season_type, offense, defense, period, down, distance, play_type, play_text, ppa, margin_pre, is_dropback, is_sack, is_int, is_pressure_est, is_passing_down, is_garbage` (booleans as bool, `ppa` float or NaN).
- Produces: `order_key(season_type: str, week: int) -> int` = week for regular, 100 + week for postseason.

- [ ] **Step 1: Failing tests:** `test_dropback_classification` (pass/sack/INT → dropback, rush/punt/penalty → not, scramble → dropback and pressure_est only when `PRESSURE_PROXY == "pressure_est"`), `test_passing_down_boundaries` ((2,8)→True, (2,7)→False, (3,5)→True, (3,4)→False, (1,10)→False), `test_garbage_thresholds` (period 2 margin 39 → True, 38 → False; period 3 29/28; period 4 23/22; period 1 margin 50 → False), `test_order_key` (`order_key("postseason", 1) > order_key("regular", 15)`).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement using `config.PLAY_TYPES` and the regexes. `margin_pre` comes from the pre-play score semantics found in the spike.
- [ ] **Step 4:** Run → PASS. Commit `feat(engine): normalize play-by-play`.

### Task 4: Incremental data fetch

**Files:**
- Create: `engine/cfbm/fetch.py`
- Test: `engine/tests/test_fetch.py`

**Interfaces:**
- Consumes: `CfbdClient.get`.
- Produces: `fbs_teams(client, season) -> set[str]` (`/teams/fbs?year=`). `games(client, season) -> list[dict]` (regular + postseason, `classification=fbs` filter not used, so FCS opponents still list). `plays(client, season, season_type, week) -> list[dict]`. `player_box(client, season, season_type, week) -> list[dict]` (`/games/players`). `advanced_season(client, season) -> list[dict]`. **Cache rule:** a week's plays/box are fetched with `cacheable=True` only when every game that week is completed (from `games()`); otherwise `cacheable=False`. `games()` for the current season is always uncacheable.

- [ ] **Step 1: Failing tests** with a fake client recording calls: `test_completed_week_uses_cache_flag`, `test_incomplete_week_refetches` (a game with `completed: False` → `cacheable=False`), `test_games_merges_regular_and_postseason`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS. Commit `feat(engine): incremental CFBD fetch`.

### Task 5: Team-game pass stats, season profiles, early-season blend

**Files:**
- Create: `engine/cfbm/team_stats.py`
- Test: `engine/tests/test_team_stats.py`

**Interfaces:**
- Consumes: PlayFrame (Task 3), `order_key`.
- Produces: `team_game_pass(plays: DataFrame) -> DataFrame`, one row per (game_id, offense team), columns `game_id, season, season_type, week, order, team, opponent, dropbacks, epa_sum, success, sacks, ints, pressure_est, pd_dropbacks, pd_epa_sum, pd_sacks`, garbage plays dropped. `success` = count of dropbacks with ppa > 0.
- Produces: `season_profile(tg: DataFrame, season: int, before_order: int | None, havoc: dict[str, float] | None = None) -> DataFrame` indexed by team with columns `games, off_dropbacks, off_epa_per_db, off_sack_rate, off_int_rate, off_pressure_rate, off_pd_epa, def_dropbacks, def_epa_per_db, def_sack_rate, def_int_rate, def_pressure_rate, def_pd_sack_rate, def_front7_havoc`. Rates are totals ÷ totals (not means of game rates). Zero denominator → NaN. `before_order=None` = full season.
- Produces: `blended_profile(tg, season, week: int, season_type: str, havoc_this, havoc_last) -> tuple[DataFrame, bool]` applying the early-season blend from Global Constraints. Returns `(profile, early_season_flag)`.

- [ ] **Step 1: Failing tests:** `test_rates_are_pooled` (game A 10 dropbacks 1 sack, game B 30 dropbacks 0 sacks → sack rate 0.025), `test_before_order_excludes_same_and_later_games`, `test_postseason_sees_full_regular_season` (bowl order 101 includes week 14), `test_week1_uses_last_season_only` (w = 0), `test_week3_blend_weights` (w = 0.5 → value exactly midway), `test_new_fbs_team_uses_this_season_only`, `test_zero_dropbacks_gives_nan_not_error`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS. Commit `feat(engine): team pass stats and season profiles`.

### Task 6: Tiers

**Files:**
- Create: `engine/cfbm/tiers.py`
- Test: `engine/tests/test_tiers.py`

**Interfaces:**
- Consumes: `season_profile` output, `fbs_teams`.
- Produces: `SKILLS = ("pass_defense", "pass_rush", "pass_offense", "pass_protection")`. `assign_tiers(profile: DataFrame, fbs: set[str]) -> DataFrame` indexed by FBS team, columns `{skill}_score`, `{skill}_rank` (1 = best), `{skill}_tier` (1/2/3), plus `{metric}_rank` and `{metric}_pct` (0–100, 100 = best for that side) for every profile rate column. Non-FBS teams are dropped before ranking. Teams with NaN score get tier NaN.
- Skill scores (higher = better): pass_defense = −def_epa_per_db. pass_offense = off_epa_per_db. pass_rush = mean z of def_sack_rate and (def_pressure_rate or def_front7_havoc per `PRESSURE_PROXY`). pass_protection = mean z of −off_sack_rate and −off_pressure_rate (or just −off_sack_rate when the proxy is havoc).
- Thirds: rank by score descending. Tier 1 = ranks 1..ceil(n/3), tier 2 = next ceil(n/3), tier 3 = rest.

- [ ] **Step 1: Failing tests:** `test_thirds_split_of_nine` (3/3/3), `test_thirds_of_134` (45/45/44), `test_fcs_team_excluded`, `test_lower_epa_allowed_is_better_defense`, `test_nan_score_gets_no_tier`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS. Commit `feat(engine): opponent tiers`.

### Task 7: Primary QB and career game logs

**Files:**
- Create: `engine/cfbm/qb.py`, `engine/tests/fixtures/box_sample.json` (trimmed `/games/players` entries)
- Test: `engine/tests/test_qb.py`

**Interfaces:**
- Consumes: raw `/games/players` lists from `fetch.player_box`.
- Produces: `passer_games(box: list[dict], season: int) -> DataFrame` with columns `game_id, season, team, athlete_id, name, attempts, team_attempts, share, is_primary` (`share >= PRIMARY_QB_SHARE`). Attempts are parsed from the `C/ATT` stat.
- Produces: `career(passers: DataFrame, athlete_id: int) -> DataFrame`, that player's primary games across all seasons and teams.
- Produces: `current_starter(passers: DataFrame, team: str, season: int, before_game_ids: set[int]) -> tuple[int, str] | None`, the primary passer of the team's most recent game in `before_game_ids`. If that game has no primary, use the player with the most season-to-date attempts. `None` if no prior games.

- [ ] **Step 1: Failing tests:** `test_share_threshold` (30 of 40 attempts → primary, 29 of 40 → not), `test_split_game_has_no_primary`, `test_career_spans_transfer` (same athlete_id, two teams, two seasons → both included), `test_starter_after_injury` (QB A primary weeks 1–5, QB B weeks 6–7 → B), `test_starter_none_in_week1`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS. Commit `feat(engine): primary passer and career logs`.

### Task 8: Opponent-tier splits

**Files:**
- Create: `engine/cfbm/splits.py`
- Test: `engine/tests/test_splits.py`

**Interfaces:**
- Consumes: `team_game_pass` (Task 5), `assign_tiers` (Task 6), `career` (Task 7).
- Produces: `TierLookup = dict[tuple[int, str], dict[str, int]]`, mapping (season, team) to {skill: tier}. For past seasons it is built from full-season profiles, and for the current season from the season-to-date profile.
- Produces: `split_table(rows: DataFrame, side: Literal["offense", "defense"], opp_skill: str, tiers: TierLookup, highlight: int | None, title: str, subject: str) -> dict` (a `SplitTable` per the JSON contract). `rows` are team-game rows (already filtered to the subject's games). For `side="offense"`, the opponent is `opponent`. For `side="defense"`, the frame is the team's defensive games, i.e. rows where `opponent == team`, and the opponent is `team`. Rows whose opponent has no tier (FCS or NaN) are dropped.
- Metrics per tier (pooled): offense → `epa_per_db`, `success_rate`, `sack_rate`, `int_rate`, `pd_epa_per_db`, plus `pressure_rate` if proxy is `pressure_est`, plus `cpoe` if `CPOE_AVAILABLE` (Task 2 decides the source; add `cpoe_sum`/`cpoe_n` columns to `team_game_pass` in that case). Defense → `epa_allowed_per_db`, `sack_rate`, `int_rate`, plus `pressure_rate` likewise. Labels and formats in `metricLabels`/`metricFormats`. If CPOE is unavailable, README Methods says so.
- Task 10 assembles four tables per section by calling `split_table`:
  1. **QB** (career rows from his primary games) vs. `pass_defense` tiers
  2. **Offense pass protection** (team, current + previous season) vs. `pass_rush` tiers
  3. **Defense** vs. `pass_offense` tiers
  4. **Pass rush** vs. `pass_protection` tiers

  Tables 3 and 4 use the team's defensive rows, current + previous season.

- [ ] **Step 1: Failing tests:** `test_rows_always_three_tiers_in_order` (a tier with no games → games 0, metrics all None), `test_small_sample_flag` (2 games/100 plays → True; 3 games/59 plays → True; 3/60 → False), `test_fcs_opponent_dropped`, `test_highlight_passthrough`, `test_past_game_uses_that_seasons_full_tier` (opponent tier 1 in 2025 full season but tier 3 in 2026 → the 2025 game is bucketed in tier 1), `test_seasons_listed` (output `seasons` = sorted distinct seasons in rows).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS. Commit `feat(engine): opponent-tier splits`.

### Task 9: Unit vs. unit tables

**Files:**
- Create: `engine/cfbm/units.py`
- Test: `engine/tests/test_units.py`

**Interfaces:**
- Consumes: `assign_tiers` output (ranks and pcts) and profile values.
- Produces: `edge(off_pct: float | None, def_pct: float | None) -> str | None`: gap = off_pct − def_pct. |gap| < `EDGE_SLIGHT` → "even". < `EDGE_CLEAR` → "slight-offense"/"slight-defense" by sign. Otherwise "clear-…". None if either side is missing.
- Produces: `unit_tables(off_team: str, def_team: str, profile: DataFrame, ranked: DataFrame) -> list[dict]` returning two `UnitTable`s:
  1. "Pass protection vs. pass rush": sack rate (off_sack_rate vs. def_sack_rate), pressure rate when the proxy is pressure_est, passing-down sack rate (offense pd sacks ÷ pd dropbacks vs. def_pd_sack_rate), and front-seven havoc (defense only, offense side null) when present.
  2. "Passing offense vs. pass defense": EPA/dropback, success rate, INT rate, passing-down EPA.

  Pcts are "higher = better for that side", so the edge math is symmetric.

- [ ] **Step 1: Failing tests:** `test_edge_bands` ((50,50)→even, (60,46)→even since 14, (65,50)→slight-offense, (20,60)→clear-defense, (None,50)→None), `test_unit_rows_have_rank_and_value`, `test_offense_only_row_has_null_defense`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS. Commit `feat(engine): unit vs unit tables`.

### Task 10: Export JSON and the build command

**Files:**
- Create: `engine/cfbm/export.py`, `engine/cfbm/cli.py`
- Test: `engine/tests/test_export.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `build(client, out_dir: Path, seasons=DISPLAY_SEASONS, now: datetime | None = None) -> None`. It writes the four file kinds in the JSON Contract and ensures play/box data exist for `CAREER_START_SEASON..max(seasons)` (career splits need it). `currentSeason`/`currentWeek` = the season and week of the earliest not-yet-completed game, else the last game.
- Produces: `game_summary(raw_game: dict, fbs: set[str]) -> dict`, where `hasBreakdown` = both teams FBS.
- Produces: `matchup(game, ...) -> dict`. `notes` include `BOWL_NOTE` for postseason and `EARLY_NOTE` when early. `quarterbacks` maps each team to its `current_starter` (or null; then the QB split table is omitted for that side). The QB split `highlight` = the opponent's current `pass_defense` tier. The protection split highlight = opponent's `pass_rush` tier, and so on.
- Produces: `to_json_safe(obj) -> obj`, which recursively converts NaN/±inf → None and numpy scalars → Python, and rounds floats to 4 decimals.
- CLI: `uv run python -m cfbm.cli build --out ../web/public/data` reads `CFBD_API_KEY` from the env or `../.env`, uses cache dir `engine/.cache`, and prints `calls_made` at the end.

- [ ] **Step 1: Failing tests** using a small synthetic season (6 FBS teams + 1 FCS team, 3 weeks, built from fixture plays/box via a fake client): `test_files_written` (index, games, players, one matchup per FBS-vs-FBS game, none for the FCS game), `test_no_nan_in_output` (`json.loads` with `parse_constant` that raises on NaN/Infinity), `test_sections_order_away_offense_first`, `test_postseason_note_and_neutral`, `test_early_note_week2`, `test_completed_game_has_points`, `test_missing_starter_omits_qb_table`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5: Real run:** `uv run python -m cfbm.cli build --out ../web/public/data`. Expected: completes, prints calls_made (note it in `docs/spike-notes.md`), and `web/public/data/2025/matchups/` holds ~700+ files. Spot-check the WVU vs. Texas Tech 2025 matchup by hand: the numbers are plausible and every split has 3 rows.
- [ ] **Step 6:** Commit the engine code and the generated data: `feat(engine): JSON export and build command`.

### Task 11: Web app scaffold, types, search, favorites

**Files:**
- Create: `web/` via `npx create-next-app@15 web --ts --app --eslint --no-tailwind --src-dir=false --import-alias "@/*"`, `web/next.config.ts` (`output: "export"`, `images: { unoptimized: true }`), `web/lib/types.ts` (contract above verbatim), `web/lib/data.ts`, `web/lib/search.ts`, `web/lib/favorites.ts`
- Test: `web/lib/search.test.ts`, `web/lib/favorites.test.ts` (Vitest + jsdom: `npm i -D vitest jsdom`, script `"test": "vitest run"`)

**Interfaces:**
- Produces: `normalize(s: string): string` (NFD, strip diacritics and apostrophes, lowercase, `&` → "and", collapse spaces). `matchGame(g: GameSummary, q: string, players: PlayerEntry[]): boolean` matches team names, conferences, or a player name whose `team` and `season` match either side.
- Produces: `getFavorites(): string[]`, `toggleFavorite(team: string): string[]`, `isFavorite(team: string): boolean` under key `"cfbm:favorites"`. All reads and writes are wrapped in try/catch and return `[]`/no-op on failure.
- Produces: `loadIndex()`, `loadGames(season)`, `loadMatchup(season, id)`, `loadPlayers()`, which fetch from `/data/...`.

- [ ] **Step 1: Failing tests:** `normalize("San José State") === "san jose state"`, `normalize("Hawai'i") === "hawaii"`, `normalize("Texas A&M") === "texas aandm"`. `matchGame` finds WVU's game for query "hawkins" via players. `matchGame` finds by conference "big 12". Favorites: toggling adds then removes. With `localStorage.getItem` stubbed to throw, `getFavorites()` returns `[]` and `toggleFavorite` doesn't throw.
- [ ] **Step 2:** `cd web && npm test` → FAIL. **Step 3:** Implement. **Step 4:** `npm test` → PASS. Commit `feat(web): scaffold, data contract, search, favorites`.

### Task 12: Home page

**Files:**
- Create: `web/app/layout.tsx` (nav: "CFB Matchups | Games | My Teams" plus the `Disclaimer` footer on every page), `web/components/Disclaimer.tsx`, `web/components/GameRow.tsx`, `web/app/page.tsx`, `web/app/globals.css`

**Interfaces:**
- Consumes: Task 11 libs and types.
- Layout (approved mockup A, minus Game of the Week, which is Slice 3): **★ My Teams** (this week's games for favorited teams; if none are favorited, show "Star a team to pin its games here") → **All games** with a search box ("Search a team, player or conference..."), a week select (default `index.currentWeek`, includes "Bowls / Playoff"), a conference select, a season select, and sort by kickoff time. Each `GameRow` shows "Away @ Home" (or "Away vs Home · Neutral site"), the kickoff in local time, the final score if completed, ☆/★ toggles per team, and links to `/game?season=…&id=…` only when `hasBreakdown`. Otherwise it shows "No breakdown (FCS opponent)".
- Style: square corners, readable tables, light/dark via `prefers-color-scheme`, no horizontal scroll at 375px.

- [ ] **Step 1:** Build it. **Step 2:** `npm run build` → succeeds with static export into `web/out/`. **Step 3:** Serve `out/` (`npx serve out`) and check in a browser at 1280px and 375px: the disclaimer is visible, search for "hawkins" shows WVU games, a starred team persists across reload, and the week select changes the list. **Step 4:** Commit `feat(web): home page`.

### Task 13: Matchup page

**Files:**
- Create: `web/app/game/page.tsx` (client component reading `season`/`id` from the query string, wrapped in `Suspense`), `web/components/UnitTable.tsx`, `web/components/SplitTable.tsx`

**Interfaces:**
- Consumes: `Matchup` from `loadMatchup`.
- Layout (approved mockup A, long scroll; "What could swing this game" arrives in Slice 2):
  1. Header: "Away @ Home" or "vs … · Neutral site", the date/time, venue, and the final score when completed. `notes` are shown as plain callouts.
  2. For each section: heading "{offenseTeam} passing vs. {defenseTeam} defense", then its unit tables, then its split tables.
- `UnitTable`: columns label | offense value (rank) | defense value (rank) | edge in words. "Even", "Slight edge: {team}", "Clear edge: {team}", with the team derived from offense/defense side. pct → "8.1%", epa → "+0.14"/"−0.08". Rank → "#98".
- `SplitTable`: the title names the subject and skill (e.g. "Michael Hawkins Jr. vs. pass defenses by strength"), with the seasons listed under it ("Seasons: 2024, 2025, 2026"). Rows read "Top third / Middle third / Bottom third", followed by games, plays and the metrics. The highlighted tier row gets a tinted background and "← this game". smallSample rows get a "Small sample" tag, and 0-game rows show "No games".
- Missing matchup file → "No breakdown for this game." with a link home.

- [ ] **Step 1:** Build it. **Step 2:** `npm run build` succeeds. **Step 3:** Browser check, desktop and 375px: open WVU @ Texas Tech 2025, then confirm both sections render, the highlight row appears, small-sample tags appear, and there is no horizontal page scroll (wide tables scroll inside their own container). Open a bowl game and confirm the note shows. **Step 4:** Commit `feat(web): matchup page`.

### Task 14: Weekly automation, README, go live

**Files:**
- Create: `.github/workflows/refresh.yml`
- Modify: `README.md`

**Interfaces:**
- Workflow: triggers `schedule: cron "0 11 * * 0"` and `"0 11 * * 3"` (Sunday morning after Saturday games and Wednesday for midweek MACtion and schedule changes, all UTC) + `workflow_dispatch`. `permissions: contents: write`. Steps: checkout, `astral-sh/setup-uv`, `actions/cache` on `engine/.cache` (key `cfbd-${{ github.run_id }}`, restore-keys `cfbd-`), `uv run python -m cfbm.cli build --out ../web/public/data` with `CFBD_API_KEY: ${{ secrets.CFBD_API_KEY }}`, then commit `web/public/data` only if changed (`git diff --quiet || git commit -m "data: weekly refresh"`) and push. Vercel builds from the push.
- README: the disclaimer line first, what the app does, how to run it locally (engine + web), and a Methods section (data source, garbage time, passing downs, tiers and how each skill is scored, primary-QB rule, career vs. two-season windows, early-season blend, the pressure estimate and its limits per the spike, small-sample rule). Credit CollegeFootballData.com.

- [ ] **Step 1:** Write the workflow and README. Validate the workflow with `gh workflow view` after push, or `actionlint` if installed. Commit `ci: weekly data refresh` and `docs: README methods`.
- [ ] **Step 2: Stop and ask the owner before going outward.** Show them the repo name (suggest `cfb-matchups`, public, under their GitHub account) and wait for a go. Then: `gh repo create cfb-matchups --public --source . --push`. The owner adds the `CFBD_API_KEY` secret (`gh secret set CFBD_API_KEY`, run by them with `!` so the key never passes through the transcript).
- [ ] **Step 3:** The owner connects the repo in Vercel (root directory `web`, framework Next.js) or approves running `vercel` CLI. Trigger the workflow once by hand: `gh workflow run refresh.yml`, then `gh run watch`. Expected: success. If data changed, a commit lands and Vercel deploys.
- [ ] **Step 4: Verify live:** open the Vercel URL and repeat the Task 12–13 checks on the live site. Confirm the disclaimer is on every page.
