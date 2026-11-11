# Edge score, swing detail, Shootout of the Week, Upset Watch: design

Date: 2026-11-10. Status: brainstormed with the owner, awaiting his approval.

Four features, built and shipped as four separate slices in this order:

1. **Edge score** (0 to 10 meter behind the Even / Slight / Big labels)
2. **Swing detail** (tap a "What could swing this game" reason to open it)
3. **Shootout of the Week**
4. **Upset Watch** (his "unexpected edge of the week")

Slice 1 comes first because slices 3 and 4 use the edge score. Each slice gets its own plan, ledger and review, the same process as today's slices (see project memory: plan in `docs/superpowers/plans`, opus review on a code-only diff, ledger copied to `docs/superpowers/plans/<plan>-ledger.md`). Each goes live only when the owner says "done".

## Why

The owner wants the reasoning behind a game, not just who is favored. Three gaps showed up in use:

- The edge labels feel too generous: games show "Even" while the rows underneath clearly lean one way.
- Swing reasons are one line. "Watch X on first and second down. If it stays on schedule, this edge is playing out" is confusing and has no number behind it.
- There is no way to spot the week's likely shootout or likely upset.

## Ground rules that still hold (owner, earlier sessions)

- Not for gambling. No predicted scores, margins, totals, spreads or over/under, and none of our own win percentages.
- **One exception (owner, this session):** the Upset Watch card shows the pros' pregame win odds, labeled as theirs, as the thing we argue against. This is the only place a win % appears, and it is never our number.
- Stats strictly before kickoff; garbage time and FCS games excluded (existing pipeline rules).
- Design: light default plus dark switch, no animations, square corners, electric blue accent. Must work at 375px.

---

## Slice 1: Edge score

### The problem, measured (recon this session, 2026 data, 537 games with a swing section)

- Overall edge labels: 287 Even, 210 Slight, 40 Clear.
- In the average "Even" game, 70% of the individual unit rows are Slight or Clear, and 236 of 287 have a Slight or Clear passing or running side edge.
- Of 182 finished "Even" games, 46 were decided by 21+ points (e.g. Missouri at Ole Miss wk 7, 3-31; Florida at Missouri wk 5, 17-45; Texas A&M at LSU wk 4, 6-35).
- When a label does fire it holds up: favored team won 17 of 19 Clear and 95 of 137 Slight.

Cause: `swing.py` builds the overall edge by averaging signed percentile gaps across every model feature for both sides of the ball (`weighted / weight`), so a home passing edge and an away passing edge cancel. `units.side_edge` does the same per section. The Even band is `|gap| < 15` percentile points (`config.EDGE_SLIGHT`), applied after the averaging has already shrunk the gap.

### What he sees (owner chose mockup A)

On the game page Preview edge card: `Ole Miss · Slight edge · 3.4`, with a horizontal meter centered on "Even" that fills toward the team with the edge, ends labeled with the two team names. The home page Edge chip shows the same label with the number.

### How it is built

- One number per game, 0 to 10, plus which team it favors. 0 means even.
- Built from the passing matchup, the running matchup and the swing factors, weighted by how much each actually decided games 2015-2025 (minus 2020), the same data and approach as the swing model. Each team's offense vs the other's defense is scored on its own side first, then the two sides are netted, so a big one-sided edge is not erased by averaging across every stat.
- Labels come from the number with new cutoffs, chosen by checking against past seasons and this season's finished games. Target: "Even" only for games near a coin flip, "Big" should almost always hold up.
- Before shipping, show the owner a before/after: label counts, and how often the favored team won in each band, old vs new. The new labels must match real results better than the old ones.
- Label words become Even / Slight / Big everywhere this slice touches (the overall label currently uses "clear"). My call.

### Left to the builder

- Exact formula, scaling to 0 to 10, and the band cutoffs (backtest decides).
- Whether per-row unit labels on the passing/running tables change. My call: they stay as they are; only overall and section (passing game / running game) edges move to the new score.
- Whether Game of the Week weighting uses the new score. My call: leave GOTW alone in this slice.

---

## Slice 2: Swing detail

### What he sees (owner approved mockup)

Each reason in "What could swing this game" becomes a pulldown, closed by default, one open at a time, opening in place on the game page (no new page). Opened, it shows:

1. **What it means:** the stat in plain words, including exactly which plays count. For "early-down success" (`sd_sr`, CFBD standard downs): every 1st down, 2nd-and-7 or shorter, 3rd or 4th-and-4 or shorter, on any series; success = half the yards needed on 1st, 70% on 2nd, all of it on 3rd/4th. The owner asked whether "first and second down" meant the first two downs of a drive; the text must make clear it does not.
2. **Why <team> has the edge:** a small table: offense's rate, what the defense allows, FBS average, and each unit's national rank ("8th of 134").
3. **Why it matters:** one line on why the stat made the list, including a historical line like "Since 2015, teams that won this matchup won the game 64% of the time." Owner approved this line explicitly. It is about past seasons in general, never this game.
4. **What to watch:** the existing cue (`CUES` in `swing.py`), rewritten with a concrete, checkable marker (e.g. "if they keep gaining 4+ yards on 1st down").

### Left to the builder

- The historical "won the game X% of the time" figure per feature comes from the 2015-2025 swing training data; compute it at build time into `model.json`.
- Rewrite all nine CUES and EXPLAIN texts for clarity; plain English, no jargon like "standard downs" without the definition.

---

## Slice 3: Shootout of the Week

### What it is (owner)

The week's game most likely to be pure offense: both teams scoring a lot, defenses playing little part. His reference game: West Virginia 48 at Texas Tech 53, 2026 week 10.

### Recon finding

A naive score (good offense vs weak defense on both sides, from the unit rows) ranked WVU-Texas Tech 35th of 62 in week 10. It has no pace and was never tested against real totals. The real version must be a model trained on 2015-2025 results (combined points as the target), the same way the swing model was built.

### How it is picked (my calls, owner agreed to the playback)

- Both offenses good and both defenses weak; a one-sided mismatch is a blowout, not a shootout. Use the weaker side's score so both must qualify.
- Pace (plays per game) and big-play rate count heavily. Pace is new data; derive it from cached play-by-play or CFBD season stats.
- Backtest: how often the weekly pick was among that week's top 3 combined-points games, and whether 2026 week 10 WVU-Texas Tech ranks near the top. Report this to the owner before shipping.
- No predicted total, no over/under. A pick and a reason in words, e.g. "Both offenses top 20 in pace and big plays; both defenses bottom 30."

### What he sees

- Home page: Game of the Week stays the big star card at the top. Shootout of the Week and Upset Watch sit under it as two **smaller** cards (owner).
- My call: a small "Shootout watch" tag on other games that score high on the same model.

---

## Slice 4: Upset Watch

### What it is (owner)

A game each week where the pros could be wrong: the underdog has a real edge somewhere, or a heavy favorite is weaker than the line says. The site picks it automatically on each refresh.

### What he sees (owner chose mockup B, "much better visual representation")

Small card under Game of the Week:

- Title "Upset Watch" (my call; owner called it "unexpected edge of the week", could be different wording).
- The matchup, then a two-color win odds bar ("ISU 28% | K-State 72%"), labeled with its real source.
- "Why that could be wrong:" our reason in words, citing the strongest underdog edge (stat and both ranks) and the edge score.

### How it is picked

- Pros' view: the owner wants ESPN's win odds. CFBD's free tier carries betting lines (providers include ESPN Bet) and a pregame win probability derived from the spread. Builder confirms which exists on the free tier. If ESPN's own per-game win % is not available, use CFBD's pregame win probability and label it honestly (e.g. "Pregame win odds, from the betting line"), never "ESPN" unless it is.
- Pick: the game where our edge score disagrees most with the pros (underdog has the edge, or heavy favorite has only a slight one). Skip games with no line.
- Backtest on past seasons: how often picks ended in an upset or a much closer game than the line expected. Report to the owner before shipping.

### Owner decisions (2026-11-10, after checking the data)

- CFBD's free tier has no ESPN win odds for 2026 (providers: DraftKings, Bovada). Owner chose **DraftKings win %**, from DraftKings' moneylines with the bookmaker's margin removed, labeled "DraftKings odds". Only the two percentages are shown, never the spread or moneyline.
- History: moneylines exist only for recent seasons, but spreads go back to 2015, so the backtest turns each spread into the pros' win chance (a curve fitted on the history itself).

---

## Decisions from the builder check (all my calls)

Mockups referenced above are in `docs/superpowers/specs/2026-11-10-mockups/` (`edge-score.html` = mockup A, `upset-card.html` = mockup B, `swing-detail.html`).

1. **Edge score inputs.** Use the nine swing-model stats (`swing_data.FEATURES`), which have 2015-2025 history from `/stats/game/advanced`. No play-by-play backfill for 2015-2020 (it would cost 100+ CFBD calls on the free tier and grow a cache already at ~1 GB). The passing game section edge uses the passing features (`pass_ppa`, `pass_sr`, `pd_sr`, plus `sd_sr` and `explosive` split by play type only if CFBD provides it; otherwise those two count toward the overall only). The running game section edge uses `rush_ppa`, `rush_sr`, `stuff`, `line_yards`. To avoid "Even over a lopsided table", the section label must not contradict the direction of the majority of rows shown under it; if it would, the plan adds a test and the builder reports the cases.
2. **Nothing gambling-shaped in published JSON.** Our internal win probability (edge score fit) and the Shootout model's predicted total stay inside the engine. Exported data carries only the 0 to 10 score, the favored team, labels, picks and reasons in words. A test asserts no exported matchup/home JSON contains those fields. The pros' odds for the Upset Watch game are the only win % exported.
3. **Home field.** The edge score includes home field (neutral sites get none), because it is real and the pros' odds include it; otherwise Upset Watch would lean toward road underdogs every week. The swing model's home coefficient supplies the size.
4. **Backtest gate.** Each of slices 1, 3 and 4 ends its engine work with a hard stop: the backtest numbers go to the owner before any web work. Better than chance means: Shootout weekly pick lands in that week's top 3 combined points more often than 3 / games-that-week on average, and WVU-Texas Tech 2026 wk 10 ranks in its week's top 5; Upset Watch picks lose outright or finish closer than the line expected more often than the line's own implied rate for those games. If a slice fails the gate, report and let the owner choose: iterate, drop the card, or ship without it.
5. **Pick overlaps.** If Shootout or Upset Watch picks the Game of the Week, take the next-best game. If nothing qualifies (early season, no lines), hide that card.

## Non-goals

- No notifications, accounts or server; still a static site refreshed by the workflow.
- No redesign of the existing sections beyond what each slice names.
- No change to Game of the Week's selection rules. (Superseded 2026-11-10 by the owner: Game of the Week now counts the running game, uses the edge score for closeness, and prefers games with two ranked teams, then one, then any.)

## Anti-goals (would be a failure even if it works)

- Any of our own predicted score, total, margin, spread or win %.
- Labels that still say "Even" over a clearly lopsided matchup.
- A shootout or upset pick that a backtest shows is no better than chance, shipped anyway.
