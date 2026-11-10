import type { Cell, Matchup, UnitTable } from "./types";

const cell = (c: Cell): Cell => ({ value: c.value ?? null, rank: c.rank ?? null, pct: c.pct ?? null });

/** Fill every optional (newer) field so components never deal with undefined. Old data renders cleanly. */
const table = (u: UnitTable): UnitTable => ({
  ...u,
  rows: u.rows.map((r) => ({ ...r, offense: cell(r.offense), defense: cell(r.defense), explain: r.explain ?? "", hint: r.hint ?? null, isKey: r.isKey ?? false })),
});

export function normalizeMatchup(m: Matchup): Matchup {
  return {
    ...m,
    game: {
      ...m.game,
      homeRank: m.game.homeRank ?? null,
      awayRank: m.game.awayRank ?? null,
      weather: m.game.weather ?? null,
      gap: m.game.gap ?? null,
      keyFactor: m.game.keyFactor ?? null,
    },
    venue: m.venue ?? null,
    availability: m.availability ?? {},
    swing: m.swing ?? null,
    sections: m.sections.map((s) => ({
      ...s,
      edge: s.edge ?? null,
      biggestGap: s.biggestGap ?? null,
      qbVs: s.qbVs ?? null,
      units: s.units.map(table),
      runUnits: s.runUnits ? s.runUnits.map(table) : null,
      runEdge: s.runEdge ?? null,
      runBiggestGap: s.runBiggestGap ?? null,
    })),
  };
}
