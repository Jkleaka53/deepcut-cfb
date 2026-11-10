import type { Matchup, Section, UnitRow } from "./types";

const gap = (r: UnitRow): number | null => {
  const a = r.offense.pct, b = r.defense.pct;
  return a === null || a === undefined || b === null || b === undefined ? null : a - b;
};

export function passingRows(section: Section): UnitRow[] {
  const rows = section.units.flatMap((u) => u.rows);
  return rows
    .map((r, i) => ({ r, i, g: gap(r) }))
    .sort((x, y) => (x.g === null ? 1 : 0) - (y.g === null ? 1 : 0) || (y.g === null || x.g === null ? 0 : Math.abs(y.g) - Math.abs(x.g)) || x.i - y.i)
    .map((x) => x.r);
}

/** The same section seen through its run tables (null when the data has none), so every passing
 *  helper (rows, edge line, badges) works on the run phase unchanged. */
export function runView(section: Section): Section | null {
  if (!section.runUnits) return null;
  return { ...section, units: section.runUnits, edge: section.runEdge ?? null, biggestGap: section.runBiggestGap ?? null };
}

export type Phase = "pass" | "run";

export function topGaps(sections: Section[], n = 3): { section: Section; row: UnitRow; phase: Phase }[] {
  const views = sections.flatMap((s) => {
    const r = runView(s);
    return [{ section: s, phase: "pass" as Phase }, ...(r ? [{ section: r, phase: "run" as Phase }] : [])];
  });
  return views
    .flatMap(({ section, phase }) => section.units.flatMap((u) => u.rows).map((row) => ({ section, row, phase, g: gap(row) })))
    .filter((x) => x.g !== null)
    .sort((a, b) => Math.abs(b.g!) - Math.abs(a.g!))
    .slice(0, n)
    .map(({ section, row, phase }) => ({ section, row, phase }));
}

export function edgeLine(section: Section, verb: "passes" | "runs" = "passes"): { text: string; team: string | null } | null {
  const off = section.offenseTeam, def = section.defenseTeam;
  const size = (e: string) => (e.startsWith("clear") ? "Big edge" : "Slight edge");
  const e = section.edge;
  if (!e) return null;
  if (e === "even") return { text: `${off} ${verb} → Even`, team: null };
  if (e.endsWith("defense")) return { text: `${off} ${verb} → ${def} D · ${size(e)}`, team: def };
  return { text: `${off} ${verb} → ${off} offense · ${size(e)}`, team: off };
}

/** Tabs to show: Availability only when the data carries it (old-format JSON doesn't). */
export function visibleTabs(m: Matchup): string[] {
  const tabs = ["preview", "passing"];
  if (m.sections.some((s) => s.runUnits)) tabs.push("running");
  tabs.push("qb");
  if (m.availability && Object.keys(m.availability).length > 0) tabs.push("availability");
  return tabs;
}
