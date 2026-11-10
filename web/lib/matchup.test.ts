import { describe, expect, it } from "vitest";
import { edgeLine, passingRows, topGaps } from "./matchup";
import type { Section, UnitRow } from "./types";

const row = (key: string, off: number | null, def: number | null): UnitRow => ({
  key, label: key, format: "pct", edge: null, explain: "", hint: null,
  offense: { value: 1, rank: 1, pct: off }, defense: { value: 1, rank: 1, pct: def },
});

const sec = (off: string, def: string, rows: UnitRow[], edge: Section["edge"] = null): Section => ({
  offenseTeam: off, defenseTeam: def, splits: [], edge, biggestGap: null,
  units: [{ title: "a", offenseTeam: off, defenseTeam: def, rows: rows.slice(0, 1) },
          { title: "b", offenseTeam: off, defenseTeam: def, rows: rows.slice(1) }],
});

describe("passingRows", () => {
  it("flattens both tables, widest gap first, missing pct last", () => {
    const s = sec("M", "O", [row("a", 50, 55), row("b", null, 90), row("c", 10, 80), row("d", 70, 40)]);
    expect(passingRows(s).map((r) => r.key)).toEqual(["c", "d", "a", "b"]);
  });
});

describe("topGaps", () => {
  it("takes the n widest across both sections", () => {
    const a = sec("M", "O", [row("a1", 50, 55), row("a2", 10, 90)]);
    const b = sec("O", "M", [row("b1", 80, 20), row("b2", 40, 50), row("b3", null, 1)]);
    const out = topGaps([a, b], 3);
    expect(out.map((x) => x.row.key)).toEqual(["a2", "b1", "b2"]);
    expect(out[1].section.offenseTeam).toBe("O");
    expect(topGaps([a, b]).length).toBe(3);
    expect(topGaps([a, b], 10).length).toBe(4);
  });
});

describe("edgeLine", () => {
  it("defense big", () =>
    expect(edgeLine(sec("Michigan", "Oregon", [], "clear-defense"))).toEqual({ text: "When Michigan passes: Oregon defense has a big edge", team: "Oregon" }));
  it("offense slight", () =>
    expect(edgeLine(sec("Michigan", "Oregon", [], "slight-offense"))).toEqual({ text: "When Michigan passes: Michigan offense has a slight edge", team: "Michigan" }));
  it("even", () => expect(edgeLine(sec("Michigan", "Oregon", [], "even"))).toEqual({ text: "When Michigan passes: even matchup", team: null }));
  it("null", () => expect(edgeLine(sec("Michigan", "Oregon", [], null))).toBeNull());
});
