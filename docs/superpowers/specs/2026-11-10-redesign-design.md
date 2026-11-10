# DeepCut CFB Redesign (R1): Design

Status: draft for owner review, 2026-11-10. Builds on `2026-11-10-cfb-matchups-design.md` (the original spec). Where this document and the original disagree on look, layout or the items below, this one wins. Everything else in the original spec (methods, tiers, garbage time, disclaimer, slices 2 to 4) still stands.

## Intent and the why

Slice 1 is live and correct, but the owner finds it "very dry and boring" and hard to read. It is mostly viewed **on phones**. The owner wants it to feel like a familiar sports app (ESPN, the NFL app, Real Sports); the favorite reference is **the ESPN scoreboard with team colors and logos**.

The matchup page must be **a look into the future of the game, not a record of the past**: the most important stats, the edge, what could shift the game, and clear indicators on the stats that matter. The owner also asked for two new features: **kickoff weather** and an **injury/availability section**, because absences can change a game.

Approved mockups live in `.superpowers/brainstorm/19228-1794330210/content/` (git-ignored): `redesign-v3.html` (home + overall look, final logo and color) and `matchup-v4.html` layout **A** (matchup stats).

## Goals

1. A sports-app look: team colors, team logos, condensed scoreboard type, square edges, line icons.
2. Mobile first: everything readable at 375px wide with no sideways scrolling.
3. A forward-looking matchup page where every stat says in plain words who has the edge.
4. Kickoff weather for every upcoming game.
5. An availability section with what free data can honestly support.
6. A Top 25 filter.
7. Light mode by default, with a light/dark switch.

## Non-goals

- Anything that looks like betting (unchanged from the original spec).
- Using weather in any edge or prediction in R1. Weather is shown as information only.
- Scraping injury reports in R1 (see Availability).
- Accounts or logins (unchanged).

## Anti-goals

- **Animation.** Owner decision: **nothing on the logo or anywhere in the app animates.** No count-ups, slide-ins, fades, shimmer, hover glows or animated transitions. State changes (tab, filter, theme) are instant.
- Stats a normal fan can't read: no unexplained jargon as the main label.
- A row that shows two numbers without saying who wins.
- Low-contrast team colors (gold text on white, navy on black).

## Owner decisions (as decided)

- **Logo:** option A, "The Cut": the word DEEPCUT in Barlow Condensed, weight 900, italic, uppercase, sliced along a shallow diagonal with the lower part shifted slightly right, followed by a small **CFB** tag (white text on the indicator blue). Static.
- **Indicator color:** Electric blue. Light theme: accent `#1f6feb`, tint background `#e8f0fe`, accent text `#1a5fd0`. Dark theme: accent `#4c8dff`, tint `#0f2142`, accent text `#7eaaff`. Text on a solid accent is white. This replaces the old amber everywhere (KEY/highlight badges, active tab underline, active chips, the CFB tag, highlighted numbers, highlighted split tier).
- **Type:** Barlow Condensed for team names, headlines, tabs, chips and all numbers; Inter for reading text.
- **Corners:** square everywhere (cards, chips, badges, bars, logo tiles, buttons).
- **Icons:** line icons instead of emoji (weather, wind, rain chance, clock, location, star, search, theme, back, external link, check).
- **Theme:** light by default regardless of the phone's setting; a switch in the top bar flips to dark and is remembered on that device.
- **ReactBits:** the owner asked to use the ReactBits MCP. Every ReactBits candidate (Count Up, Animated List, Fade Content, Spotlight Card, Shiny Text, Decrypted Text) is an animation, so after the no-animation decision **no ReactBits component ships**. This was told to the owner.
- **Matchup stat layout:** layout **A, head to head** (ESPN team-stats style), not the report card.
- **Top 25:** a chip in the filter row, right after All.
- **Rollout:** built on a separate branch with a Vercel preview link. It replaces the live site only after the owner tries the preview and says it is done. Until then, the scheduled refresh keeps running on `main` in the current format: the new engine fields must be additions that do not break the live pages, and generated data in `web/public/data` is never merged from the branch (it is rebuilt on `main` after the merge).
- **Logos:** fetched during each Vercel build and kept out of git (git-ignored), so no team trademarks are stored in the public repo. If the logo download fails, the build still succeeds and shows team abbreviations on a team-color tile instead.
- **Injuries:** option C: ship the safe version now (QB flags + official report links); the owner emails HD Intelligence for permission to show the full reports, and that becomes a later feature if they say yes.

## Visual system

- Colors are tokens on both themes (background, card, ink, muted, line, chip, accent set above). Light background `#f2f3f5`, cards white, ink `#0b1220`. Dark background `#090b0e`, cards `#13171c`, ink `#f3f5f7`.
- **Team colors** come from CFBD `/teams` (`color`, `alternateColor`). Rule for any team color used as a fill behind white text, or as text on a card: it must reach 4.5:1 contrast for normal text and 3:1 for bars and large text in the current theme. If the primary fails, try the alternate; if both fail, darken (light theme) or lighten (dark theme) the primary until it passes. (Example: Michigan navy works on white but is lightened in dark mode; West Virginia gold needs its navy alternate behind white text.)
- **Team logos** come from CFBD `/teams` `logos` (index 0 = for light backgrounds, index 1 = for dark). In the colored hero they sit on a white square tile; in lists they sit directly on the card and use the dark-background version in dark mode.
- Footer on every page: the existing disclaimer, plus "Not affiliated with any team, conference or the NCAA." and "Data: CollegeFootballData.com · Weather: Open-Meteo". The README gets the same affiliation line.

## Home page (scoreboard)

Top to bottom:

1. **Sticky top bar:** logo, search icon (opens the existing search), theme switch.
2. **Week chips** (horizontally scrollable, current week selected) and **filter chips**: All · Top 25 · ★ My Teams · SEC · Big Ten · Big 12 · ACC · Group of 5 · Independents. One filter at a time. Both rows stay pinned while scrolling. Group of 5 = every FBS conference outside the SEC, Big Ten, Big 12 and ACC, including the Pac-12. *(My call.)*
3. **Game of the Week card** (only once Slice 3 exists): diagonal split in the two teams' colors, logos on white tiles, kickoff + stadium, weather, and the one-line "why watch".
4. **★ My Teams** section (if any favorited team plays that week).
5. **Games grouped by day** ("Saturday, Nov 14"), sorted by kickoff. Each row: two lines (away on top, home below) with logo, AP rank if ranked, team name; on the right the kickoff time (viewer's local time) or the final score for completed games, a weather mini (icon + temperature; rain chance if 30% or more; wind if 15 mph or more; "Indoors" for domes) and one highlight chip naming the game's biggest-gap stat (see "Highlights before and after Slice 2").
6. Footer.

The old season/week/conference dropdowns are replaced by the chips. Last season stays reachable with a season switch at the end of the week-chip row.

**Top 25:** uses the **AP Top 25** from CFBD `/rankings` (free tier, verified), the latest poll released before that week's games. A game passes the Top 25 filter if either team is ranked. Week 1 uses the preseason poll; postseason games use the last poll released before them. *(My call.)* Ranks show beside team names on the home page and the matchup hero. The College Football Playoff rankings are not in the feed yet; switching Top 25 to them once published is a possible later change, not part of R1.

## Matchup page

1. **Hero:** diagonal split in both team colors, logos on white tiles, team names in condensed caps with AP rank, each team's starting QB, kickoff day and time, stadium, city and state, grass or turf, then a **weather strip**: condition with icon, temperature in °F, rain chance, wind in mph.
2. **Sticky section tabs:** Preview · Passing game · QB splits · Availability. The page stays one long scroll (the original approved layout); tabs jump to their section and highlight as you scroll past.
3. **Preview:**
   - **The edge** card: one sentence, then one line per side: "[Team] passes → [winner] D · Big edge" (or "slight edge", or "Even"), filled in the winning team's color. When the offense ranks better, the line names the offense: "[Team] passes → [Team] offense · Slight edge". *(My call.)*
   - **What could swing this game** (Slice 2; hidden until it exists).
   - The **three biggest-gap stats** from the passing game, shown in the head-to-head style below.
4. **Passing game:** two blocks, "When [away] passes" and "When [home] passes". Each opens with a two-part header bar in the offense's and the defense's team colors ("Michigan offense | Oregon defense"). Each stat row (layout A):
   - Offense value on the left, defense value on the right; the side with the better rank is bold, the other muted.
   - Centered: a plain-English stat name, a one-line explanation, and a "lower is better" hint where a lower number wins for that side.
   - Under the numbers: each side's rank as an ordinal ("130th", "49th", out of 138), and the verdict in words in the winner's color: "Oregon big edge", "Oregon slight edge" or "Even". Big = the existing Clear band (over 35 percentile points), slight = the Slight band (15 to 35), Even = under 15.
   - One bar split in the two team colors, each side's share proportional to its percentile.
   - Rows are sorted biggest gap first. A missing value shows "—" with no verdict and no bar.
   - A legend at the end: "Rank is out of 138 FBS teams (1st = best for that side). More color in the bar = stronger."
5. **QB splits:** for each starting QB, three tier boxes (top third, middle, bottom third of pass defenses) with EPA per dropback large and games played; this game's tier is outlined in the accent color and labeled "this game". Small-sample tiers keep their label. A "More" control opens the full existing split table (all metrics, plays, seasons covered). The other existing split tables (pass protection vs. pass-rush tiers, defense vs. offense tiers) appear the same way, collapsed by default.
6. **Availability:** see below.
7. Footer.

**Plain-English stat names** (offense side / defense side wording where they differ):

| Engine metric | Label | One-line explanation |
|---|---|---|
| INT rate | Interceptions | How often a pass gets picked off |
| EPA/dropback | Points added per pass | How much each pass play helps the offense score |
| Success rate | Successful passes | Passes that keep the offense on schedule |
| Sack rate | Sacks | How often the QB goes down (offense: allowed; defense: made) |
| Passing-down sack rate | Sacks on 3rd-and-long | Sacks when everyone knows a pass is coming |
| Passing-down EPA | Passing on 3rd-and-long | How well the offense passes in those spots |
| Front-seven havoc | Front-seven disruption | Tackles for loss, sacks and batted passes by the front seven |

## Highlights before and after Slice 2

- **R1 (this build):** the stat with the largest percentile gap in each passing block gets a **"Biggest gap"** badge in the accent color; the home-page chip names the game's single biggest gap ("Gap: interceptions"). The edge card's per-side line uses the **average percentile gap across that side's passing rows**, mapped to the same Even / slight / big bands. *(My call: the original spec's overall edge is weighted by the swing-factor model, which doesn't exist yet. This is an honest stand-in, and the page never claims more than "who ranks better on these stats".)*
- **After Slice 2:** "Biggest gap" is replaced by **KEY** badges on the stats the swing-factor model ranks highest; the edge card gains the overall weighted edge from the original spec; the "What could swing this game" card appears in Preview; the home-page chip shows the top swing factor ("Key: turnovers").

## Weather (new)

- **Source:** Open-Meteo forecast API (no key; free for non-commercial use with credit; attribution in the footer). Tested 2026-11-10: hourly forecasts out to 16 days.
- **Where:** stadium latitude/longitude from CFBD `/venues` (verified to include coordinates, dome flag, grass flag, city, state).
- **What:** at the kickoff hour: temperature (°F), precipitation probability, wind speed and gusts (mph), and a condition from the weather code, mapped to a short label and an icon (clear, partly cloudy, cloudy, fog, drizzle, rain, snow, thunderstorm).
- **Cases:**
  - Dome → no API call; show "Indoors".
  - Kickoff more than 16 days out → "Forecast closer to kickoff".
  - Kickoff time not yet announced → the day's forecast (high temperature, max rain chance, max wind), labeled "Time TBA".
  - Completed games → no weather shown.
  - Forecast call fails → no weather strip; the rest of the page builds normally.
- Each forecast carries the time it was fetched, shown as "Forecast as of Fri 5 PM".
- **Refresh:** forecasts change daily, so add refresh runs on **Friday 22:00 UTC** and **Saturday 12:00 UTC** to the existing Sunday and Wednesday runs. Every run rebuilds everything (cheap, since CFBD pulls are cached). The workflow already has a concurrency group, so runs can't overlap.

## Availability (new)

R1 shows only what free data supports reliably:

1. **QB check from our own data**, per team:
   - "✓ [QB] started last game" when the current starter was the primary passer in the team's most recent game.
   - A warning when the primary passer of the most recent game differs from the starter the game before, or when the QB who started most of the season didn't play the last game ("[QB] did not play last game").
   - These lines describe what happened; they never say why or claim an injury.
2. **Official report link:** for each team, a link to its conference's official football availability report page, with a line on when it posts (for SEC/Big Ten/ACC/Big 12: Wednesday, updated through about 90 minutes before kickoff). Non-conference games show each team's conference link. Teams whose conference publishes no report show "No official availability report for this game."
3. **Later, only with permission:** a marked spot for the full out/questionable list, hidden in R1. If HD Intelligence grants permission, that becomes its own design. Without permission, nothing is scraped.

## Data and pipeline additions

- CFBD `/teams` (colors, logos, abbreviation, conference) and `/venues`: once per season, cached.
- CFBD `/rankings` for the season: once per run (one call).
- Logos: a prebuild step on Vercel downloads each FBS team's light and dark logo from the URLs in the team data into the site's static files (git-ignored), so the live site doesn't load images from another site. See Owner decisions.
- Open-Meteo: one forecast call per venue with an upcoming game inside 16 days (a few dozen calls a week; it accepts several locations per call).
- The JSON the site reads gains team info (colors, logos, abbreviation), AP rank per team per game, venue details, the weather block, the biggest-gap stat and per-side edge, and the availability block. Exact field names and file layout are the builder's call, as in the original spec.

## Constraints

- Static site, as today (Next.js static export on Vercel); the API key never reaches the browser. Open-Meteo is called by the build, not by the browser.
- Free data and free hosting only.
- Fonts are self-hosted through the build (no runtime font requests).
- No horizontal page scroll at 375px in either theme.
- Tests keep running in CI; new engine logic (weather mapping, rank lookup, QB availability flags, contrast rule, biggest gap) is test-first, as in Slice 1.

## Left to the builder

- Exact spacing, sizes and the dark-theme token values beyond those listed.
- The icon set (any clean line icon set; Lucide matches the mockups).
- How the logo is drawn (inline SVG or styled text), and the favicon.
- Weather-code-to-label mapping details and icon choices.
- The conference-to-report-URL list (verify each page exists; skip conferences without one).
- JSON field names and file layout.
- How the "More" panels open (no animation either way).

## Next feature (R2): Availability watch, a what-if tab

Owner idea, approved 2026-11-10. Built right after R1, with its own plan. It turns the missing injury feed into a feature: the user reads the official report (linked in the tab) and sets players In or Out.

- **Who is listed, per team:** starting QB, backup QB, the top three receivers by targets, and the lead running back (needs CFBD player box scores for receiving and rushing, plus the backup QB's career splits).
- **Defaults:** everyone starts **In**, except a listed player who missed the team's most recent game while the team played. They start **Out**, labeled "Missed last game". This is the only automatic guess, and it never claims an injury. Nobody maintains a researched list.
- **Research link:** the official conference availability report link sits at the top of the tab: "Check the official report, then set players In or Out."
- **What a switch changes:**
  - **QB:** setting the starter Out swaps in the backup's real numbers and splits; the passing-game rows, ranks and edge lines recompute in the browser. A thin backup sample is labeled small sample.
  - **Receivers and running back:** shows their share of team production (for example "31% of receiving yards"). Edges do **not** change, because free data can't honestly measure one player's effect on a unit.
- **Wording:** edges stay in words (Even / Slight edge / Big edge). Never odds, percentages or "50/50".
- **Memory:** choices are saved on the device per game (local storage, wrapped so it fails safely); "Reset to defaults" restores them; a banner shows whenever the page differs from the defaults ("What-if: Tommy Carr set Out").

## Added after preview review (owner, 2026-11-10)

- **"Gap" chip renamed** to "Edge: <stat> · <team abbreviation>" (owner). Matchup badge reads "Biggest edge", Preview card "Biggest edges".
- **Game of the Week ships in this update** (owner), moved up from Slice 3, using the original spec's rule minus swing factors (which don't exist until Slice 2). *My calls:* score = 0.6 x strength (mean percentile of the four passing units) + 0.4 x closeness (100 minus the mean absolute gap); only games with an AP Top 25 team are eligible when the week has any, so a Group of 5 game with schedule-inflated numbers can't headline; the card (v3 mockup design) shows on every filter the game passes; "Why watch" states unit strength and the edge picture, never a prediction. Swing factors join the score after Slice 2.
- **QB splits rework (owner, approved from mockup qb-splits-v2, layout A).** Per starting QB: an opponent box ("This week: <team> pass D · <rank> of <N>"), two record boxes (pass defenses ranked as good or better than this week's opponent, inclusive, outlined "This game"; and worse), a one-line summary (record above the line; "All N losses came against pass defenses ranked Xth or better" when 2+ losses; special wording for one game or none), and the career game log vs. FBS opponents sorted by opponent pass-defense rank with a "▲ <team> <rank> · tougher D above" line. Shown: every game above the line plus two below; the rest and the QB's old tier table sit behind "More". The three team-unit split tables stay, each in its own visible card (owner). *My calls:* points per pass weighted by dropbacks; "Small sample" under 3 games; postseason rows labeled "CFP" (from CFBD game notes) or "Bowl".
- **Collapsible QB split groups (owner).** Each offense's QB card and its three unit tables sit in one block, closed by default, with a team-colored header (team, QB, record vs. pass D as good as this week's) and a full-width "Show all N splits" / "Hide splits" button. Native details element, no animation.
