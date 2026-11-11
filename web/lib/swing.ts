import { ordinal } from "./format";
import type { Driver, GameSummary, OverallEdge, Section, UnitRow } from "./types";

export const BAND = { even: "Even", slight: "Slight edge", clear: "Big edge" } as const;

/** Edge-score cutoffs; mirror engine config.EDGE_SCORE_SLIGHT / EDGE_SCORE_BIG. */
export const EDGE_SLIGHT = 2;
export const EDGE_BIG = 8;

export function bandText(edge: Driver["edge"], team: string | null): string {
  return edge === "even" || !team ? "Even" : `${BAND[edge]} ${team}`;
}

export function overallText(o: OverallEdge | null | undefined): string | null {
  return o ? `Overall: ${bandText(o.edge, o.team)}` : null;
}

export function matchupLine(d: Driver): string {
  return `${d.offense} offense vs. ${d.defense} defense · ${ordinal(d.offRank)} vs. ${ordinal(d.defRank)} of ${d.of}`;
}

/** KEY replaces "Biggest edge" once the model marks rows; a block with no key row keeps Biggest edge. */
export function badgeFor(row: UnitRow, section: Section): string | null {
  if (row.isKey) return "Key";
  const anyKey = section.units.some((u) => u.rows.some((r) => r.isKey));
  return !anyKey && row.key === section.biggestGap ? "Biggest edge" : null;
}

export function chipText(g: Pick<GameSummary, "keyFactor" | "gap">, abbr: string): string | null {
  if (g.keyFactor) return `Key: ${g.keyFactor.label} · ${abbr}`;
  if (g.gap) return `Edge: ${g.gap.label} · ${abbr}`;
  return null;
}

export function edgeChipText(e: GameSummary["edge"], abbr: string): string | null {
  if (!e || e.band === "even" || !e.team) return null;
  return `${BAND[e.band]} · ${abbr} ${e.score.toFixed(1)}`;
}
