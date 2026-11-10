import type { Cell, Matchup } from "./types";

const cell = (c: Cell): Cell => ({ value: c.value ?? null, rank: c.rank ?? null, pct: c.pct ?? null });

/** Fill every optional (newer) field so components never deal with undefined. Old data renders cleanly. */
export function normalizeMatchup(m: Matchup): Matchup {
  return {
    ...m,
    game: {
      ...m.game,
      homeRank: m.game.homeRank ?? null,
      awayRank: m.game.awayRank ?? null,
      weather: m.game.weather ?? null,
      gap: m.game.gap ?? null,
    },
    venue: m.venue ?? null,
    availability: m.availability ?? {},
    sections: m.sections.map((s) => ({
      ...s,
      edge: s.edge ?? null,
      biggestGap: s.biggestGap ?? null,
      qbVs: s.qbVs ?? null,
      units: s.units.map((u) => ({
        ...u,
        rows: u.rows.map((r) => ({ ...r, offense: cell(r.offense), defense: cell(r.defense), explain: r.explain ?? "", hint: r.hint ?? null })),
      })),
    })),
  };
}
