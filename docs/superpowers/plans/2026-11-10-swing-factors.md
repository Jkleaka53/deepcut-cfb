# Slice 2: What Could Swing This Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every matchup page gets a "What could swing this game" card (3 to 5 proven drivers, then labeled storylines), an overall game edge weighted by a model trained on past seasons, KEY badges on the passing rows the model ranks highest, a "Key: <factor>" home chip, and swing factors joining the Game of the Week score.

**Architecture:** The engine trains a logistic regression (numpy, IRLS, no new dependency) on ~10 seasons of CFBD `/stats/game/advanced` rows, using matchup differentials known before kickoff. The model is exported once per build (`model.json`). Per matchup the engine scores each factor = importance × gap × volatility, picks the top drivers, computes storylines from schedule/venue/QB data, and writes them into the matchup JSON. The web only renders.

**Tech Stack:** Python (uv, pandas, numpy, pytest), CFBD `/stats/game/advanced` + `/games`, Next.js 15 static export, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-10-cfb-matchups-design.md` section 3 "What could swing this game", Overall game edge, Game of the Week; `docs/superpowers/specs/2026-11-10-redesign-design.md` "Highlights before and after Slice 2". Owner skipped questions (2026-11-10); *(my call)* marks executor decisions.

## Global Constraints

- Edges in words only: Even / Slight edge / Big edge. Never win %, predicted score, point margin, odds, "50/50".
- Features are season-to-date averages **before kickoff**, never the game's own stats.
- 3 to 5 drivers, each with a one-line "watch for this" cue. Storylines always show sample size, are labeled "Storyline", and never outrank drivers.
- No animations; square corners; light default + dark; tokens.
- CFBD free tier: training data is cached (past seasons never refetched).

## My calls (record in spec at the end)

- Training seasons 2015–2025 minus 2020 (COVID schedules); a game trains only if both teams have ≥ 3 prior FBS-vs-FBS games that season. Live season is scored, not trained on.
- FEATURES (offense stat, CFBD path, direction for offense): `pass_ppa` passingPlays.ppa +1 "Points added per pass"; `pass_sr` passingPlays.successRate +1 "Successful passes"; `pd_sr` passingDowns.successRate +1 "Passing-down success"; `rush_ppa` rushingPlays.ppa +1 "Points added per run"; `rush_sr` rushingPlays.successRate +1 "Successful runs"; `sd_sr` standardDowns.successRate +1 "Early-down success"; `explosive` explosiveness +1 "Big plays"; `stuff` stuffRate −1 "Runs stuffed"; `line_yards` lineYards +1 "Yards the line creates". Defense side uses the same field from the `defense` block (what the defense allows; lower is better for the defense except `stuff`).
- Game feature f = (home.off − away.def_allowed) − (away.off − home.def_allowed) per stat (direction-adjusted), standardized by training mean/sd; plus `home` = 1 unless neutral site. Target = home win.
- Importance = |standardized coefficient|. Proven = 95% bootstrap interval (200 resamples, seed 7) excludes 0.
- Volatility = within-team game-to-game sd ÷ between-team sd of season means (training data), per stat.
- Matchup factor: two per stat (one per side's offense vs the other's defense). gap_z = (off − def_allowed, direction-adjusted, minus training mean of that per-side advantage) ÷ training sd. score = importance × |gap_z| × volatility. Drivers = proven factors, top by score, max 5, min 3 when 3 proven exist, skip |gap_z| < 0.25.
- Overall edge = importance-weighted mean of per-side percentile gaps across factors, mapped through edge(50+g/2, 50−g/2), named for the team it favors.
- KEY badge on a passing row whose parent feature is among the drivers: epa_per_db→pass_ppa, success_rate→pass_sr, pd_epa→pd_sr; sack/int/havoc rows have no parent. No KEY row in a block → keep "Biggest edge".
- Storylines (all labeled, with sample): QB home vs road record (non-neutral games, this game's site); QB night games (local kickoff ≥ 7 PM) when this game is at night; rest: coming off a bye (≥ 13 days) or a short week (≤ 5 days); travel ≥ 1,000 miles for the road team (venue coords vs its home venue); big stadium (attendance ≥ 80,000 venue history) QB record when this game is in one. Each needs ≥ 2 games of sample to show; sorted by sample size.
- GOTW score adds 0.15 × (drivers count / 5) and renormalizes (0.5 strength, 0.35 closeness, 0.15 swing). "Why" mentions "N swing factors".

## Review Focus

1. Early season (team with < 3 games): no driver for that side's factors, card says so plainly; no crash.
2. Neutral-site / postseason: `home` feature 0, home/road storyline skipped.
3. A matchup where nothing passes the 0.25 gap floor → card shows "No big swing factors: these teams match up evenly on the stats the model trusts."
4. Missing venue coords or attendance → that storyline skipped, others still shown.
5. Old JSON without `swing` → card hidden, "Biggest edge" and Edge chip behave as R1.

---

### Task 1: Training frame (engine)
Files: `cfbm/fetch.py` (+`game_advanced(client, season, live)`), create `cfbm/swing_data.py`, `tests/test_swing_data.py`.
Produces: `FEATURES: list[tuple[key, path, direction, label]]`; `team_games(adv) -> DataFrame[game_id, season, order, team, opponent, off_<k>..., def_<k>...]`; `pregame(tg, before_order, season) -> DataFrame[team, games, off_<k>, def_<k>]` (means of prior games); `training_frame(tg, games_by_id, fbs_by_season) -> DataFrame[game_id, season, home_win, home, f_<k>...]`.
Tests: nested path parse; pregame uses only earlier games; game dropped when a team has < 3 priors; neutral → home 0; tie games dropped; FCS opponents excluded.

### Task 2: Model (engine)
Create `cfbm/swing_model.py`, `tests/test_swing_model.py`.
Produces: `fit_logit(X: ndarray, y: ndarray, l2=1e-3) -> ndarray`; `train(frame, tg) -> dict` = `{"seasons", "games", "features": {k: {"coef", "lo", "hi", "proven", "importance", "volatility", "mean", "sd", "sideMean", "sideSd"}}, "home": {...}}`.
Tests: recovers sign/size on synthetic data (y from known logits, n=4000, coef within 0.15); noise feature not proven; volatility of constant-per-team stat ≈ 0; deterministic with seed.

### Task 3: Matchup swing (engine)
Create `cfbm/swing.py`, `tests/test_swing.py`.
Produces: `swing_block(model, home, away, pre: DataFrame, ranked_pct: dict, neutral) -> {"drivers": [...], "overallEdge": {"edge", "team"}|None, "keyRows": {offenseTeam: [row_key]}, "note": str|None}`; driver = `{key, label, offense, defense, edge(word band), favors, offRank, defRank, of, cue, score}`. CUES dict per feature with {off}/{def}.
Tests: top by score; unproven excluded; gap floor; max 5; early-season side skipped with note; overall edge favors right team; keyRows mapping; Review Focus 1 and 3.

### Task 4: Storylines (engine)
Create `cfbm/storylines.py`, `tests/test_storylines.py`.
Produces: `storylines(game, qbs, qb_logs, games_by_id, venues, team_home_venue) -> list[{text, sample, kind: "storyline"}]`.
Tests: home/road record text; neutral skips it (RF 2); bye and short week; travel ≥ 1000 mi via haversine; missing coords skipped (RF 4); night only when this game is night; sample < 2 hidden.

### Task 5: Export (engine)
Modify `cfbm/export.py` (+ `_Data.adv` for training seasons and live season, `model.json`), `cfbm/gotw.py`, tests.
- matchup: `swing: {drivers, storylines, overallEdge, note}`; unit rows `key: bool`; game summary `keyFactor` (top driver label) for home chips; GOTW new weights + why.
- Tests: swing present with ≤ 5 drivers; keyFactor; gotw score uses swing count.

### Task 6: Web
Create `components/matchup/SwingCard.tsx`, tests `lib/swing.test.tsx`; modify types, normalize (`swing ?? null`), Preview in `app/game/page.tsx` (card first in Preview), `EdgeCard` (overall line "Overall: Slight edge Oregon"), HeadToHead badge (KEY when `row.key` true, else Biggest edge), ScoreRow chip ("Key: Big plays · ORE" when keyFactor, else Edge).
- Card: "What could swing this game", drivers numbered (label, "Oregon offense vs Michigan defense · 12th vs 88th · Big edge Oregon", cue), then "Storylines to watch" with "Storyline · 4 games" tags, footnote "Ranked by how much each stat has decided games since 2015, how far apart these teams are on it, and how much it swings week to week. Not a prediction."
- Tests: renders drivers in order, storyline label+sample, note when no drivers, hidden when swing null (RF 5), KEY badge, chip text.
- Playwright 375px light/dark.

### Task 7: Docs, data, review, preview
README methods paragraph; spec "Slice 2 built" calls line; data build; final review (opus); fix; ask before pushing a preview; live only after "done".
