# CFB Matchups: Design

Date: 2026-11-10
Status: draft, awaiting owner approval
Working name: CFB Matchups (placeholder, owner may rename)

## Intent

A personal passion project and public GitHub showcase. Most college football prediction sites show who is favored and nothing about why. This web app breaks every FBS game down purely on statistics, at a depth those sites skip: how a specific QB has performed against defenses as good as the one he is about to face, how his offensive line holds up against pass rushes of that quality, and which stats are most likely to swing the outcome.

The owner's example: Michael Hawkins Jr. (WVU) vs. the Texas Tech defense. How does the WVU line hold up against a pass rush like Tech's, and how does Hawkins play when the rush gets home?

**Disclaimer (required):** this project is not for gambling or betting use. It is a personal statistics project. The disclaimer appears in the footer of every page and at the top of the README.

## Goals

1. For any FBS game, show a full statistical picture of how it should play out and why.
2. Opponent splits: show how each key player and unit performed against top-third, middle and bottom-third opponents at the relevant skill (pass defense, pass rush, run defense, etc.), with the tier this game falls in highlighted. This is the heart of the product.
3. Unit vs. unit: put each side's season numbers head to head, with an edge call per phase and the numbers behind it.
4. Rank the factors most likely to change the outcome ("What could swing this game"), split into **Proven drivers** and **Storylines to watch**.
5. Browse all games with search, favorite teams, and a weekly Game of the Week.

## Non-goals

- Betting lines, spreads, over/unders, odds or anything framed as a wager.
- Paid data (PFF etc.). Free data only.
- User accounts or logins.
- FCS and lower divisions.
- Live in-game updates.

## Anti-goals (would be failure even if it works)

- **Looking like a betting site.** No odds formatting, no "lock of the week" language.
- **Verdicts without numbers.** Every edge or ranking shows the stats behind it.
- **Small samples dressed up as truth.** A "0-2 at Death Valley" stat must never read as strongly as a 40-game trend. Every split shows its sample size, and thin samples are labeled.
- **Garbage-time inflation.** Blowout plays must not skew numbers.

## Data

**Source:** CollegeFootballData.com API (api.collegefootballdata.com). The owner signs up for a free API key. Bearer token auth. The free tier has a monthly call limit (about 1,000/month at last check; verify). The pipeline must stay under it by caching raw pulls and only fetching new weeks.

**Endpoints expected to be useful** (verify exact shapes against live responses):
- Games and schedule, venues (attendance, stadium, home/away/neutral, kickoff time)
- Play-by-play (`/plays`), the base for most custom splits
- Team advanced season and game stats (`/stats/season/advanced`, `/stats/game/advanced`): success rate, PPA (CFBD's EPA), explosiveness, standard vs. passing downs, line yards, stuff rate, power success, havoc (front-seven and DB)
- Player PPA by game (`/ppa/players/games`), player game stats, CPOE where provided
- Weather by game, if available on the free tier (verify; drop it if not)

**Definitions** follow CFBD's published metrics page: PPA/EPA, success rate, passing downs (2nd-and-8+, 3rd/4th-and-5+), garbage time (pre-play margin > 38 in Q2, > 28 in Q3, > 22 in Q4), line yards, stuff rate, havoc.

**Known gap, verify first:** true pressure rate and time-to-pressure are not in free data. The plan is an **estimated pressure rate** built from play-by-play: sacks + scrambles + throwaways + intentional grounding, per dropback. CFBD play types label sacks and grounding, but scrambles and throwaways may only be detectable by parsing play text. **The first build task is a spike that measures how reliably these can be identified.** If scrambles/throwaways cannot be found reliably, fall back to sack rate + front-seven havoc + passing-down sack rate as the pass rush proxies, and say so on the page.

**Scope of seasons:** the app displays the current season and last season. The swing-factor model trains on roughly ten past seasons of game data (builder picks the exact range for data quality).

## The three layers of every matchup

### 1. Unit vs. unit

Head-to-head tables for each phase, both teams' numbers side by side with national rank, and an edge column.

Pass phase (built first):
- **Offensive line pass protection vs. defensive pass rush:** sack rate allowed/generated, estimated pressure rate, front-seven havoc, passing-down sack rate.
- **QB/passing offense vs. pass defense:** EPA per dropback, success rate, CPOE (offense) vs. opponent CPOE (defense), explosiveness, INT rate.

Run phase (second, same pattern): line yards, stuff rate, power success, second-level and open-field yards, rushing EPA.

Edge call per row: which side is stronger based on the national percentile gap. The rule (thresholds for "slight" vs. "clear" edge) is the builder's call; it must be shown in plain words with the numbers.

**Overall game edge (owner decision):** each game also gets one overall edge, in words only: **Even / Slight edge [team] / Clear edge [team]**, rolled up from the row edges weighted by the swing-factor model's importance weights. It is used on the home page, in the games list and by Game of the Week. **Never shown as a win percentage, predicted score or point margin.**

### 2. Opponent splits (the heart of it)

For each key player and unit, performance broken into three opponent tiers:
- **Tiers** are thirds of FBS for the relevant skill, ranked by that skill's own numbers from free data (never AP rank or record). Example: pass-defense tier = defenses ranked by EPA allowed per dropback. Pass-rush tier = ranked by sack rate + front-seven havoc (or the estimated pressure rate if the spike succeeds). Run-defense tier = ranked by rushing EPA allowed.
- **Splits shown:** the QB vs. pass-defense tiers (EPA/dropback, CPOE, sack %, INT %, passing-down efficiency); the offensive line vs. pass-rush tiers; flipped, the defense vs. QB/offense tiers and the pass rush vs. pass-protection tiers. The run game follows later with the same pattern.
- **This game's tier is highlighted**: "Tech is a top-third pass rush, so this is the row that matters."
- **Sample size on every row** (games and plays). Rows below a minimum sample get a visible "small sample" label. The builder sets the threshold.
- Garbage time is excluded everywhere.
- **How far back (owner decision):** players (QBs first, then any other key players) use their **whole FBS college career, including previous schools after a transfer** (e.g. John Mateer's Washington State seasons count). Players are matched across seasons and teams by CFBD player ID, with a name+position fallback checked by hand for transfers. Team units (offensive line, pass rush, run defense, etc.) use **this season plus last season**, since rosters turn over. Pages show which seasons a split covers.
- **Opponent tiers for past games** use that opponent's strength over its full season (or season-to-date for the current season), not a snapshot from the week they played. *(My call: early-week snapshots are too noisy.)*
- **Early season:** before about week 5, team numbers blend last season with this season, with this season's weight growing each week. Pages in that window carry an "early-season data" label. *(My call.)*
- For upcoming games, all stats and tiers use data **up to that week only**. For past games, the breakdown uses data as of kickoff, so past pages show what the app would have said beforehand.

### 3. What could swing this game

A ranked list of 3 to 5 factors at the top of the matchup page. Each has a one-line "watch for this" cue (e.g. "If WVU allows a sack on its first two 3rd-and-longs, the protection edge is playing out.").

**Ranking method:**
1. Train a model on historical FBS games (about ten seasons) to learn how strongly each stat differential **known before kickoff** (season-to-date averages as of that week, not that game's own in-game stats) tracks with winning, e.g. passing-down success rate, sack rate, explosiveness, rushing success, turnover margin. *(My call: training on in-game stats would over-rank luck-driven stats like turnover margin, which decide games but barely predict them.)* Training uses team-level game stats from the cheaper advanced-stats endpoints; play-by-play is only pulled for the seasons on display, to fit the free-tier call limit. A logistic regression on standardized differentials is the suggested baseline; the builder may choose something else if it is equally explainable.
1a. **Player factors** (e.g. "Hawkins' turnovers vs top-third defenses") inherit their importance from the team-level stat they belong to (QB turnovers → turnover rate, QB sack rate → sack rate). They count as proven drivers only if that parent stat is a proven driver and the player's split meets the minimum sample; otherwise they are storylines. *(My call.)*
2. For this matchup, score each factor as: **importance** (learned weight) × **size of the gap** between the two sides × **volatility** (how easily that stat swings game to game). High importance plus a real gap plus high volatility means worth watching.
3. Pick the top factors.

**Proven drivers vs. Storylines to watch:** a proven driver is backed by a large sample and a stat the model shows matters. A storyline is a real but small-sample situational stat, like "QB is 0-2 at LSU," always shown with its sample size and clearly labeled. Storylines never outrank proven drivers.

**Situational factors to compute** (candidates for storylines, or for drivers if the data supports it):
- QB and team results/efficiency at home vs. on the road
- Results in large, loud stadiums (by attendance)
- Night vs. day games
- Travel distance, rest days, coming off a bye
- Weather (wind, cold) for pass-heavy teams, if the data is available
- Performance as an underdog vs. as the stronger team on paper
- Turnover luck (fumble recovery rate vs. the ~50% expectation)

## Game of the Week

One game per week, picked by a score that rewards:
- **Strength vs. strength:** top units facing each other (e.g. a top-10 offense vs. a top-10 defense)
- **A close edge picture:** neither side clearly wins on paper
- **The most swing factors in play**

The card always shows a plain-language "why" (e.g. "Best offense vs. best defense in the SEC, edges nearly even, 4 swing factors"). The builder sets the exact weights.

## The web app

Layouts approved from mockups (saved in `.superpowers/brainstorm/`):

**Home page (layout A, stacked):**
1. **Game of the Week** card: matchup, the "why," and the top swing factor. Links to the matchup page.
2. **★ My Teams:** this week's games for favorited teams, each with a one-line edge summary.
3. **All games:** search box (team, player or conference; a player search finds that player's team's games), filters for week and conference, and sort (most interesting by the Game of the Week score, kickoff time).
4. Disclaimer footer.

**Matchup page (layout A, one long scouting-report scroll):**
1. Header: teams, records, date/time, stadium, day/night.
2. **What could swing this game** (highlighted box): proven drivers, then storylines.
3. **Unit vs. unit** tables, pass phase first, then run phase.
4. **Opponent splits** tables, with this game's tier highlighted. Both directions: offense vs. defense tiers and defense vs. offense tiers.
5. Situational section.
6. Final score shown for completed games.
7. Disclaimer footer.

**Favorites:** a ★ on any team. Stored in the browser (localStorage). No accounts.

**Phones:** must work at phone width.

## How it gets built (my calls, owner accepted them as defaults)

- **Stats engine:** Python (pandas or similar). Pulls from CFBD, caches raw responses, computes tiers, splits, unit matchups, swing factors and Game of the Week, and writes JSON files the site reads.
- **Refresh:** a scheduled GitHub Actions job runs weekly in season (and can be triggered by hand). The API key lives in a GitHub Actions secret. The site never calls CFBD directly.
- **Website:** Next.js (React), statically generated from the JSON, hosted on Vercel's free tier.
- **Repo:** one public GitHub repo holding both the Python engine and the web app. The README explains the methods (tiers, swing-factor model, the pressure estimate and its limits) and leads with the disclaimer. `.superpowers/` goes in `.gitignore`.
- **Cost:** free.
- **Project folder:** `~/dev/cfb-matchups` (not under ~/Documents).

## Timeline (owner decision)

**Live during the rest of the 2026 season, as soon as possible**, then keep improving. On 2026-11-10 roughly three regular-season weeks remain, then conference championships, bowls and the College Football Playoff. "Current season" = 2026, "last season" = 2025 for now; both roll forward in 2027.

The build ships in usable slices, each one deployed when it works:

1. **Spike (first days):** CFBD key, pull 2025–2026 play-by-play, measure how well the estimated pressure rate can be built. Decide pressure proxy.
2. **Slice 1, live first:** pass-phase engine (tiers, QB career splits, O-line and pass-rush splits, unit vs. unit, garbage time filtered), the matchup page for the pass phase, the home page with the games list, search and favorites, the disclaimer, **weekly GitHub Actions refresh and Vercel deploy**. Automation comes in this slice, not at the end.
3. **Slice 2:** swing-factor model, overall game edge, situational stats and storylines.
4. **Slice 3:** Game of the Week.
5. **Slice 4:** run phase.

Slices 2 to 4 may land during bowl season. That's fine.

**Postseason handling (needed this season):** neutral-site games (no home/away; the situational section uses "neutral" and skips home/road stories), long layoffs before bowls (rest days becomes a storyline), and bowl opt-outs (CFBD does not reliably report them; show a plain note that bowl rosters may differ from the season numbers). Conference championship and playoff games follow the same rules.

## Left to the builder

- Exact edge thresholds, minimum sample sizes, Game of the Week weights.
- Swing-factor model choice (within "explainable").
- Visual styling, as long as it doesn't look like a sportsbook.
- Data storage format and file layout for the JSON.
- Which "key players" get split tables beyond the starting QB (e.g. top receiver, lead RB).
