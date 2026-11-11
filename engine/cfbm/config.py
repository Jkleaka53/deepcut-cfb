"""Project-wide constants. Values come from the design spec and the slice 1 plan."""

CFBD_BASE_URL = "https://api.collegefootballdata.com"

# Garbage time: pre-play absolute margin strictly greater than this, by period.
GARBAGE_MARGIN = {2: 38, 3: 28, 4: 22}

CAREER_START_SEASON = 2021
DISPLAY_SEASONS = (2025, 2026)
# Swing-factor model training seasons: about ten, skipping 2020's COVID schedules.
TRAIN_SEASONS = tuple(y for y in range(2015, 2026) if y != 2020)
MIN_TRAIN_GAMES = 500

PRIMARY_QB_SHARE = 0.75
MIN_SAMPLE_GAMES = 3
MIN_SAMPLE_PLAYS = 60

# Regular-season weeks below 5 blend last season with this season.
EARLY_SEASON_LAST_WEEK = 4

# Edge bands, in percentile points.
EDGE_SLIGHT = 15
EDGE_CLEAR = 35

# Edge score (0-10) cutoffs: below SLIGHT is Even, at or above BIG is Big. Set 2026-11-10 by
# `cfbm.cli edge-cutoffs` (leave-one-season-out, 5613 games 2015-2025 minus 2020):
# Even 1099 games, favored team won 53.5%; Slight 3088, 69.1%; Big (>=7.5) 1426, 85.3%.
# Owner raised Big to 8.0 the same day: at 7.5 only 81% of 2026's 88 Big games held; at 8.0, 85% of 65.
EDGE_SCORE_SLIGHT = 2.0
EDGE_SCORE_BIG = 8.0

# Set by the Task 2 spike (see docs/spike-notes.md).
# Scrambles/throwaways are not labeled in free play-by-play, so pass rush uses front-seven havoc.
PRESSURE_PROXY = "front_seven_havoc"
# No completion-probability fields on the free tier.
CPOE_AVAILABLE = False

PLAY_TYPES = {
    "pass": {"Pass Reception", "Pass Incompletion", "Passing Touchdown"},
    "sack": {"Sack"},
    "interception": {"Pass Interception Return", "Interception Return Touchdown", "Interception"},
    "rush": {"Rush", "Rushing Touchdown"},
}

DISCLAIMER = "Not for gambling or betting. DeepCut CFB is a personal statistics project."
BOWL_NOTE = "Bowl rosters can differ from season numbers because of opt-outs and transfers."
EARLY_NOTE = "Early-season data: numbers blend last season with this season."

# Official conference availability report pages (verified 2026-11-10). Big Ten's page could not be
# confirmed (bigten.org blocks automated requests), so it is left out until a URL is checked by hand.
_P4_WHEN = "Posts Wednesday, updated until about 90 minutes before kickoff."
AVAILABILITY_REPORTS = {
    "SEC": {"url": "https://www.secsports.com/fbreports", "when": _P4_WHEN},
    "ACC": {"url": "https://theacc.com/sports/2025/8/28/availability-reporting.aspx", "when": _P4_WHEN},
    "Big 12": {"url": "https://big12sports.com/sports/2025/8/21/availability-reporting.aspx", "when": _P4_WHEN},
    "Big Ten": {"url": None, "when": _P4_WHEN},  # publishes reports; page URL not yet confirmed
}

# Opponent adjustment for the edge/swing model's pregame stats (owner 2026-11-10). Each team's stat is
# corrected by this share of how far its opponents' averages sit from the league's, using only games
# before kickoff. 0.8 had the best held-out log loss (0.5626 vs 0.5764 raw) over 2015-2025; see
# docs/superpowers/plans/2026-11-10-upset-report.md.
OPP_ADJUST = 0.8
# Re-checked on the adjusted model 2026-11-10: owner kept EDGE_SCORE_SLIGHT 2.0 / EDGE_SCORE_BIG 8.0 (Big 85% on 2026).

# Edge model (2026-11-10): scoring margin per game is capped at this many points either way, and a team's
# season-to-date numbers are pulled toward the league average by n / (n + EDGE_SHRINK_K) (n = its games so far).
EDGE_MARGIN_CAP = 28
# Shrink strength set 2026-11-10 by `cfbm.cli edge-audit` (leave-one-season-out, 7791 games 2015-2025 minus 2020),
# all-games log loss: k=0 0.5404, k=1 0.5405, k=2 0.5407, k=3 0.5410, k=5 0.5412. No shrinking was best by a hair,
# so a team's numbers are only centered on the league average; a team with no games sits at the average.
EDGE_SHRINK_K = 0.0
