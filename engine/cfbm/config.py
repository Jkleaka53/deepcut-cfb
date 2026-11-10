"""Project-wide constants. Values come from the design spec and the slice 1 plan."""

CFBD_BASE_URL = "https://api.collegefootballdata.com"

# Garbage time: pre-play absolute margin strictly greater than this, by period.
GARBAGE_MARGIN = {2: 38, 3: 28, 4: 22}

CAREER_START_SEASON = 2021
DISPLAY_SEASONS = (2025, 2026)

PRIMARY_QB_SHARE = 0.75
MIN_SAMPLE_GAMES = 3
MIN_SAMPLE_PLAYS = 60

# Regular-season weeks below 5 blend last season with this season.
EARLY_SEASON_LAST_WEEK = 4

# Edge bands, in percentile points.
EDGE_SLIGHT = 15
EDGE_CLEAR = 35

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
}
