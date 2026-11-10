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
  homeRank?: number | null;
  awayRank?: number | null;
  weather?: Weather | null;
  gap?: { key: string; label: string; favors: string } | null;
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

export interface TeamAvailability {
  flags: AvailabilityFlag[];
  report: { conference: string | null; url: string | null; when: string | null };
}

export interface Cell { value: number | null; rank: number | null; pct?: number | null }

export interface UnitRow {
  key: string;
  label: string;
  format: "pct" | "epa";
  offense: Cell;
  defense: Cell;
  edge: Edge;
  explain?: string;
  hint?: string | null;
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
}

export interface Matchup {
  game: GameSummary;
  earlySeason: boolean;
  notes: string[];
  quarterbacks: Record<string, { athleteId: number; name: string } | null>;
  sections: Section[];
  venue?: Venue | null;
  availability?: Record<string, TeamAvailability>;
}

export interface PlayerEntry {
  athleteId: number;
  name: string;
  team: string;
  position: "QB";
  season: number;
}
