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
}

export interface UnitRow {
  key: string;
  label: string;
  format: "pct" | "epa";
  offense: { value: number | null; rank: number | null };
  defense: { value: number | null; rank: number | null };
  edge: Edge;
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
}

export interface Matchup {
  game: GameSummary;
  earlySeason: boolean;
  notes: string[];
  quarterbacks: Record<string, { athleteId: number; name: string } | null>;
  sections: Section[];
}

export interface PlayerEntry {
  athleteId: number;
  name: string;
  team: string;
  position: "QB";
  season: number;
}
