# CFB Matchups

**Not for gambling or betting. CFB Matchups is a personal statistics project.**

Most college football prediction sites tell you who's favored and stop there. CFB Matchups breaks every FBS game down on the numbers and shows the reasoning:

- **Unit vs. unit.** Each team's pass protection against the other team's pass rush, and its passing offense against the other's pass defense, with national ranks and an edge in plain words (Even / Slight / Clear).
- **Opponent splits.** How a quarterback has played across his whole college career, including other schools, against top-third, middle-third and bottom-third pass defenses. The tier this game falls in is highlighted. The same splits cover offensive lines against pass rushes, and defenses against passing offenses.

It covers the current season and the previous one, and refreshes twice a week during the season.

## How it works

```
CollegeFootballData API ──► engine/ (Python) ──► web/public/data/*.json ──► web/ (Next.js static site)
```

- `engine/` pulls play-by-play and box scores, caches them on disk, computes everything, and writes static JSON.
- `web/` is a static Next.js site that only reads that JSON. It never calls the stats API.
- `.github/workflows/refresh.yml` reruns the engine on Sunday and Wednesday mornings (UTC) and commits new data. The host redeploys on push.

## Run it locally

You need [uv](https://docs.astral.sh/uv/), Node 20+ and a free API key from [collegefootballdata.com/key](https://collegefootballdata.com/key).

```bash
# 1. API key (kept out of git by .gitignore)
echo 'CFBD_API_KEY=your-key' > .env

# 2. Engine: tests, then build the data (the first build makes ~200 API calls and takes a few minutes)
cd engine
uv run pytest
uv run python -m cfbm.cli build --out ../web/public/data

# 3. Website
cd ../web
npm install
npm test
npm run dev        # http://localhost:3000
```

## Methods

**Data.** Everything comes from the free [CollegeFootballData.com](https://collegefootballdata.com) API: play-by-play with per-play expected points added (PPA, CFBD's version of EPA), passing box scores, season advanced stats and schedules.

**Dropbacks.** Completions, incompletions, passing touchdowns, sacks and interceptions. Scrambles aren't labeled in the free data, so they count as runs.

**Garbage time** is removed everywhere. A play counts as garbage time when the margin before the snap is more than 38 points in the 2nd quarter, 28 in the 3rd, or 22 in the 4th.

**Passing downs** are 2nd-and-8 or longer and 3rd/4th-and-5 or longer.

**Tiers.** For each skill, FBS teams are ranked and split into thirds: tier 1 is the top third. Opponents are ranked on that skill's own numbers, never on AP rank or record.

| Skill | Ranked by |
|---|---|
| Pass defense | EPA allowed per dropback (lower is better) |
| Passing offense | EPA per dropback |
| Pass rush | Average of standardized sack rate and front-seven havoc rate |
| Pass protection | Sack rate allowed (lower is better) |

In a game's breakdown, opponents from earlier seasons are tiered on their full-season numbers. Opponents from the game's own season are tiered on numbers up to kickoff, so past games show what the site would have said beforehand. Games against non-FBS teams are left out of tiers and splits.

**Pressure isn't measured directly.** True pressure rate and time to pressure come from paid charting services. The free play-by-play doesn't label scrambles or throwaways (we checked: 2 scrambles mentioned in about 21,000 runs), so the pass rush is measured by sack rate, passing-down sack rate and front-seven havoc. **Completion % over expected (CPOE)** isn't in the free data either, so it isn't shown.

**Starting quarterback.** A QB is a game's primary passer when he throws at least 75% of his team's attempts. Games where QBs split time count for nobody. The matchup page uses the primary passer from the team's most recent game. Week-1 games have no starter yet.

**Windows.** QB splits cover his whole FBS career since 2021, across schools, joined on the player's CFBD id. Team-unit splits cover the game's season and the one before it.

**Early season.** For a regular-season game in weeks 1 to 4, team numbers blend last season with this season. This season's weight is (week − 1) ÷ 4, so week 1 is all last season and week 5 is all this season. Those pages carry an "early-season data" label.

**Small samples.** Every split row shows games and dropbacks. A row with fewer than 3 games or 60 dropbacks is labeled "Small sample".

**Edges** compare the two sides' national percentiles on a stat. A gap under 15 points is "Even", 15 to 35 is "Slight", and more than 35 is "Clear".

**Bowls and the playoff** show a note that opt-outs and transfers can make rosters differ from season numbers. Neutral-site games are labeled as such.

## Not for gambling

This project shows no betting lines, spreads, odds, win probabilities or predicted scores, and it isn't meant for wagering of any kind. It's a personal statistics project.

## Credits

Data: [CollegeFootballData.com](https://collegefootballdata.com).
