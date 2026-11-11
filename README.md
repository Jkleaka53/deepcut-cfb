# DeepCut CFB

**Not for gambling or betting. DeepCut CFB is a personal statistics project.** Not affiliated with any team, conference or the NCAA.

Most college football prediction sites tell you who's favored and stop there. DeepCut CFB breaks every FBS game down on the numbers and shows the reasoning:

- **Unit vs. unit.** Each team's pass protection against the other team's pass rush, and its passing offense against the other's pass defense, with national ranks and an edge in plain words (Even / Slight / Clear).
- **Opponent splits.** How a quarterback has played across his whole college career, including other schools, against top-third, middle-third and bottom-third pass defenses. The tier this game falls in is highlighted. The same splits cover offensive lines against pass rushes, and defenses against passing offenses.

- **Game day context.** AP Top 25 ranks, each school's colors and logo, the stadium, and a kickoff weather forecast.
- **Availability.** What each team's own box scores say about its quarterback (who started last game, any change), plus a link to the conference's official availability report.

It covers the current season and the previous one, and refreshes four times a week during the season.

## How it works

```
CollegeFootballData API ──► engine/ (Python) ──► web/public/data/*.json ──► web/ (Next.js static site)
```

- `engine/` pulls play-by-play and box scores, caches them on disk, computes everything, and writes static JSON.
- `web/` is a static Next.js site that only reads that JSON. It never calls the stats API.
- `.github/workflows/refresh.yml` reruns the engine on Sunday and Wednesday mornings, Friday evening and Saturday morning (UTC) and commits new data. The host redeploys on push. The Friday and Saturday runs keep kickoff weather fresh.
- Team logos are downloaded during the site build (`web/scripts/fetch-logos.mjs`) and never committed. A logo that fails to download shows the team's abbreviation instead.

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

**QB vs. pass defenses.** The QB splits tab shows this week's opponent's pass-defense rank (EPA allowed per dropback, 1st = best), the quarterback's record in his starts against pass defenses ranked that well or better and against worse ones, and every start against an FBS team sorted by that opponent's rank, with a line where this week's opponent falls. Past seasons use each opponent's full-season rank; the current season uses the rank up to kickoff. "Record" is his team's result in games he started. Points per pass is weighted by dropbacks. The team unit splits (pass protection, pass defense, pass rush) follow in their own cards.

**Running game.** Built from the same play-by-play as the passing numbers, with garbage time and games against FCS teams left out, and only games before kickoff. Runs are CFBD "Rush" plays, so QB scrambles count; sacks and kneel-downs never do. Per carry: *yards the line creates* counts losses at 120%, the first 4 yards in full, yards 5 to 10 at half and nothing past 10 (the Football Outsiders rule); *yards past the line* counts the yards a run gains between 5 and 10; *breakaway yards* counts every yard past 10; *runs stuffed* are runs for no gain or a loss; *short-yardage runs converted* covers 3rd or 4th and 2 or less, and runs from the 2 or closer. Each side is ranked nationally and compared like the passing rows. These track CFBD's own season numbers closely (2025 correlations 0.88 to 0.94; 0.67 for short yardage, the smallest sample, which is also left out of the home page Edge chip).

**What could swing this game.** A logistic regression trained on about ten seasons of FBS games (2015 to 2025, skipping 2020) learns which stat matchups, known before kickoff, have tracked with winning: each team's season-to-date average plus what the opponent's defense allows, for passing and rushing efficiency, success rate, early-down and passing-down success, big plays, stuffed runs and line yards. Only stats with a clearly positive effect (95% bootstrap interval above zero) count as proven drivers. Each matchup factor is scored as importance x the size of the gap x how much the stat swings week to week; the top 3 to 5 are shown with a "watch for this" line. Storylines (QB at home or on the road, in night games, in big road stadiums; rest days; long travel) are small samples, always labeled with their sample size, and never outrank drivers. Not a prediction: no win odds, scores or margins.

**The edge score.** The overall edge is a separate 0 to 10 score. It combines the same nine matchups with each team's prior strength (an Elo rating that carries over from past results), its scoring margin so far this season (capped at 28 points a game) and home field, and it is scored against how lopsided past games were: under 2 is Even, 2 to 8 is Slight, 8 and up is Big. Early in the season, before teams have played much, it leans on prior strength, so every FBS game has a score from week 1. The swing factors above still need three games per team. The model itself is not published.

**Availability watch.** For games not yet played, the Availability tab lists each team's starting QB, backup QB (the season's other QB with the most attempts), top three receivers by receiving yards and lead rusher, each with an In/Out switch. Read the official conference report (linked), then set players. Setting the starting QB Out swaps in the backup's numbers from his own career starts, ranked against this season's FBS offenses, and every edge on the page recomputes. Receivers and backs show their share of team yards only; switching them changes no numbers, because free data can't honestly measure one player's effect on a unit. A player with no box-score line in his team's most recent game starts Out, tagged "No stats last game" (a fact, never an injury claim). Choices are saved on your device per game; "Reset to defaults" restores them.

**Starting quarterback.** A QB is a game's primary passer when he throws at least 75% of his team's attempts. Games where QBs split time count for nobody. The matchup page uses the primary passer from the team's most recent game. Week-1 games have no starter yet.

**Windows.** QB splits cover his whole FBS career since 2021, across schools, joined on the player's CFBD id. Team-unit splits cover the game's season and the one before it.

**Early season.** For a regular-season game in weeks 1 to 4, team numbers blend last season with this season. This season's weight is (week − 1) ÷ 4, so week 1 is all last season and week 5 is all this season. Those pages carry an "early-season data" label.

**Small samples.** Every split row shows games and dropbacks. A row with fewer than 3 games or 60 dropbacks is labeled "Small sample".

**Edges** compare the two sides' national percentiles on a stat. A gap under 15 points is "Even", 15 to 35 is "Slight", and more than 35 is "Clear".

**Plain-English stats.** The site labels stats in words ("Interceptions", "Points added per pass") with a one-line explanation. For some stats a lower number is better for one side, for example interceptions for an offense; those rows say so ("Offense: lower is better · Defense: higher is better"). Ranks are always 1st = best for that side, whichever way the number runs.

**The edge card** averages the percentile gap across a passing matchup's stats and maps it to the same Even / Slight / Clear bands. It says who ranks better on these stats, nothing more. The "Biggest edge" badge marks the single stat with the widest gap, and the home page's "Edge: <stat> · <team>" chip names the game's widest gap and the team it favors.

**Game of the Week** is picked from the week's games with an AP Top 25 team (all games if none are ranked). Each is scored 60% on strength (the average national percentile of both passing offenses and both pass defenses) and 40% on closeness (how small the offense-versus-defense gaps are). The card's "Why watch" line says which units rank in the top third of FBS and who holds the edge on paper. It never predicts a winner.

**AP ranks** come from CFBD's copy of the AP Top 25: the latest regular-season poll at or before the game's week. Week 1 uses the preseason poll; bowls and the playoff use the final regular-season poll.

**Weather** comes from [Open-Meteo](https://open-meteo.com): the hourly forecast at the stadium for the kickoff hour (temperature, rain chance, wind). Games more than 16 days out say "Forecast closer to kickoff", indoor stadiums say "Indoors", games with no kickoff time use that day's forecast, and finished games show no weather. Each forecast shows when it was made.

**Availability.** The quarterback check describes what happened in the box scores and never says why: who was the primary passer last game, whether that changed from the game before, and whether the season's usual starter didn't play. It never claims an injury. Links go to the SEC, ACC and Big 12 official availability pages; other conferences show "No official availability report for this game" until a page is confirmed.

**Bowls and the playoff** show a note that opt-outs and transfers can make rosters differ from season numbers. Neutral-site games are labeled as such.

## Not for gambling

This project shows no betting lines, spreads, odds, win probabilities or predicted scores, and it isn't meant for wagering of any kind. It's a personal statistics project.

## License

Code: [MIT](LICENSE). Football data belongs to its sources and is used under [CollegeFootballData.com](https://collegefootballdata.com)'s terms.

## Credits

Data: [CollegeFootballData.com](https://collegefootballdata.com). Weather data by [Open-Meteo.com](https://open-meteo.com), used under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) for non-commercial use. Team names and logos belong to their schools; this project isn't affiliated with any of them.
