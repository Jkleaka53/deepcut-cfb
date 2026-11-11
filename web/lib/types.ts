// JSON contract. engine/cfbm/export.py must emit exactly these shapes (camelCase keys).
export type Tier = 1 | 2 | 3;
export type Edge = "even" | "slight-offense" | "clear-offense" | "slight-defense" | "clear-defense" | null;
export type TierSkill = "pass_defense" | "pass_rush" | "pass_offense" | "pass_protection";

export interface Index {
  seasons: number[];
  currentSeason: number;
  currentWeek: number;
  seasonType: "regular" | "postseason";
  generatedAt: string;
}

export interface GameSummary {
  id: number;
  season: number;
  week: number;
  seasonType: "regular" | "postseason";
  start: string;
  home: string;
  away: string;
  homeConf: string | null;
  awayConf: string | null;
  neutral: boolean;
  venue: string | null;
  completed: boolean;
  homePoints: number | null;
  awayPoints: number | null;
  hasBreakdown: boolean;
  startTimeTBD?: boolean;
  homeRank?: number | null;
  awayRank?: number | null;
  weather?: Weather | null;
  gap?: { key: string; label: string; favors: string } | null;
  keyFactor?: { label: string; favors: string } | null;
  /** Overall edge score for the home chip; null when even or unscored. */
  edge?: { band: "even" | "slight" | "clear"; team: string | null; score: number } | null;
  /** Among the week\'s next-highest Shootout of the Week games. */
  shootoutWatch?: boolean;
}

export type WeatherIcon = "clear" | "partly-cloudy" | "cloudy" | "fog" | "drizzle" | "rain" | "snow" | "storm";

export interface Weather {
  status: "forecast" | "tba" | "indoors" | "far";
  label?: string;
  icon?: WeatherIcon;
  tempF?: number | null;
  precipPct?: number | null;
  windMph?: number | null;
  gustMph?: number | null;
  asOf?: string;
}

export interface TeamInfo {
  school: string;
  id: number | null;
  abbr: string;
  conference: string | null;
  fill: string;
  textLight: string;
  textDark: string;
  barDark?: string;
  logo: string | null;
  logoDark: string | null;
}

export interface Venue {
  name: string | null;
  city: string | null;
  state: string | null;
  grass: boolean | null;
  dome: boolean | null;
}

export interface AvailabilityFlag { kind: "ok" | "warn"; text: string }

export interface WatchPlayer {
  athleteId: number;
  name: string;
  role: "QB" | "QB2" | "WR" | "RB";
  share: number | null;
  shareOf: "receiving yards" | "rushing yards" | null;
  noStatsLastGame: boolean;
}

export interface Backup {
  athleteId: number;
  name: string;
  games: number;
  smallSample: boolean;
  cells: Record<string, Cell>;
  qbVs: QbVs;
}

export interface TeamAvailability {
  flags: AvailabilityFlag[];
  report: { conference: string | null; url: string | null; when: string | null; publishes?: boolean };
  players?: WatchPlayer[];
  backup?: Backup | null;
}

export interface Cell { value: number | null; rank: number | null; pct?: number | null }

export interface UnitRow {
  key: string;
  label: string;
  format: "pct" | "epa" | "yds";
  offense: Cell;
  defense: Cell;
  edge: Edge;
  explain?: string;
  hint?: string | null;
  isKey?: boolean;
}

export interface UnitTable {
  title: string;
  offenseTeam: string;
  defenseTeam: string;
  rows: UnitRow[];
}

export interface SplitRow {
  tier: Tier;
  games: number;
  plays: number;
  smallSample: boolean;
  metrics: Record<string, number | null>;
}

export interface SplitTable {
  title: string;
  subject: string;
  tierSkill: TierSkill;
  seasons: number[];
  highlightTier: Tier | null;
  metricLabels: Record<string, string>;
  metricFormats: Record<string, "pct" | "epa">;
  rows: SplitRow[];
}

export interface Section {
  offenseTeam: string;
  defenseTeam: string;
  units: UnitTable[];
  splits: SplitTable[];
  edge?: Edge;
  biggestGap?: string | null;
  qbVs?: QbVs | null;
  /** Run phase (Slice 4). Missing in older JSON. */
  runUnits?: UnitTable[] | null;
  runEdge?: Edge;
  runBiggestGap?: string | null;
}

export interface QbGame {
  gameId: number;
  season: number;
  opponent: string;
  oppRank: number;
  stage: "Bowl" | "CFP" | null;
  result: "W" | "L" | "T" | null;
  pf: number | null;
  pa: number | null;
  epaPerDb: number | null;
  dropbacks: number;
}

export interface QbVs {
  name: string;
  opponent: string;
  oppRank: number | null;
  of: number | null;
  games: QbGame[];
}

export interface Driver {
  key: string;
  label: string;
  offense: string;
  defense: string;
  edge: "even" | "slight" | "clear";
  favors: string;
  offRank: number;
  defRank: number;
  of: number;
  cue: string;
  score: number;
  /** Opened view of a swing reason; missing in old JSON (render flat). */
  detail?: DriverDetail;
}

export interface DriverDetail {
  meaning: string;
  format: "pct" | "epa" | "num";
  offValue: number | null;
  defAllows: number | null;
  fbsAvg: number | null;
  why: string;
}

export interface Storyline { text: string; sample: string; kind: "storyline" }

/** score: 0-10 edge score (percentile of how lopsided the matchup is); missing in old JSON. */
export interface OverallEdge { edge: "even" | "slight" | "clear"; team: string | null; score?: number | null }

export interface Swing {
  drivers: Driver[];
  storylines: Storyline[];
  overallEdge: OverallEdge | null;
  note: string | null;
}

export interface Matchup {
  game: GameSummary;
  earlySeason: boolean;
  notes: string[];
  quarterbacks: Record<string, { athleteId: number; name: string } | null>;
  sections: Section[];
  venue?: Venue | null;
  availability?: Record<string, TeamAvailability>;
  swing?: Swing | null;
  /** Record going into this game. Missing in older JSON. */
  records?: Record<string, TeamRecord>;
}

export interface PlayerEntry {
  athleteId: number;
  name: string;
  team: string;
  position: "QB";
  season: number;
}

export interface TeamRecord {
  wins: number;
  losses: number;
  confWins: number;
  confLosses: number;
  conference: string | null;
}
