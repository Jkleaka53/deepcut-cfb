import type { Cell, Edge, Matchup, UnitRow } from "./types";

/** Same bands as engine/cfbm/config.py EDGE_SLIGHT / EDGE_CLEAR. */
const SLIGHT = 15;
const CLEAR = 35;

/** Port of units.py edge(). */
export function edge(offPct: number | null | undefined, defPct: number | null | undefined): Edge {
  if (offPct == null || defPct == null) return null;
  const gap = offPct - defPct;
  if (Math.abs(gap) < SLIGHT) return "even";
  const side = gap > 0 ? "offense" : "defense";
  return `${Math.abs(gap) < CLEAR ? "slight" : "clear"}-${side}` as Edge;
}

function gaps(rows: UnitRow[]): [number, UnitRow][] {
  return rows.flatMap((r) => (r.offense.pct == null || r.defense.pct == null ? [] : [[r.offense.pct - r.defense.pct, r] as [number, UnitRow]]));
}

/** Port of units.py side_edge(). */
export function sideEdge(rows: UnitRow[]): Edge {
  const g = gaps(rows);
  if (!g.length) return null;
  const mean = g.reduce((a, [x]) => a + x, 0) / g.length;
  return edge(50 + mean / 2, 50 - mean / 2);
}

/** Port of units.py biggest_gap(): first row wins ties. */
export function biggestGap(rows: UnitRow[]): string | null {
  const g = gaps(rows);
  if (!g.length) return null;
  return g.reduce((best, item) => (Math.abs(item[0]) > Math.abs(best[0]) ? item : best))[1].key;
}

const EMPTY: Cell = { value: null, rank: null, pct: null };

/** The matchup as it reads with the given players Out. Only a starting QB set Out changes numbers. */
export function applyWhatIf(m: Matchup, out: Set<number>): Matchup {
  const swaps = new Map<string, NonNullable<NonNullable<Matchup["availability"]>[string]["backup"]>>();
  for (const [team, a] of Object.entries(m.availability ?? {})) {
    const starter = a.players?.find((p) => p.role === "QB");
    if (starter && out.has(starter.athleteId) && a.backup) swaps.set(team, a.backup);
  }
  if (!swaps.size) return m;
  const quarterbacks = { ...m.quarterbacks };
  const sections = m.sections.map((s) => {
    const b = swaps.get(s.offenseTeam);
    if (!b) return s;
    quarterbacks[s.offenseTeam] = { athleteId: b.athleteId, name: b.name };
    const units = s.units.map((u) => ({
      ...u,
      rows: u.rows.map((r) => {
        if (r.offense.value === null && r.offense.rank === null && !(r.key in b.cells)) return r;
        const offense = { ...(b.cells[r.key] ?? EMPTY) };
        return { ...r, offense, edge: edge(offense.pct, r.defense.pct) };
      }),
    }));
    const rows = units.flatMap((u) => u.rows);
    return { ...s, units, edge: sideEdge(rows), biggestGap: biggestGap(rows), qbVs: b.qbVs };
  });
  return { ...m, quarterbacks, sections };
}

/** Players who start Out: anyone with no stats in the team's last game, except the backup QB. */
export function defaultsOut(m: Matchup): Set<number> {
  const ids = Object.values(m.availability ?? {}).flatMap((a) => (a.players ?? [])
    .filter((p) => p.noStatsLastGame && p.role !== "QB2" && (p.role !== "QB" || a.backup))
    .map((p) => p.athleteId));
  return new Set(ids);
}

/** Banner text: every change from the defaults, plus any starting QB Out by default (so the backup's
 *  numbers never show silently). Null when there is nothing to say. */
export function whatIfText(m: Matchup, out: Set<number>, defaults: Set<number>): string | null {
  const parts: string[] = [];
  for (const a of Object.values(m.availability ?? {})) {
    for (const p of a.players ?? []) {
      if (p.role === "QB2") continue;
      const isOut = out.has(p.athleteId);
      if (isOut !== defaults.has(p.athleteId)) parts.push(`${p.name} set ${isOut ? "Out" : "In"}`);
      else if (isOut && p.role === "QB") parts.push(`${p.name} Out (no stats last game)`);
    }
  }
  return parts.length ? `What-if: ${parts.join(", ")}` : null;
}
