import { describe, expect, it } from "vitest";
import { applyWhatIf, biggestGap, defaultsOut, edge, sideEdge } from "./whatif";
import type { Matchup, UnitRow } from "./types";

const row = (key: string, op: number | null, dp: number | null): UnitRow => ({
  key, label: key, format: "pct", offense: { value: op === null ? null : 0.1, rank: op === null ? null : 10, pct: op },
  defense: { value: 0.1, rank: 20, pct: dp }, edge: edge(op, dp), explain: "", hint: null });

const m = (): Matchup => ({
  game: { id: 1, season: 2026, week: 11, seasonType: "regular", homeTeam: "Oregon", awayTeam: "Michigan" } as unknown as Matchup["game"],
  earlySeason: false, notes: [],
  quarterbacks: { Michigan: { athleteId: 10, name: "Tommy Carr" }, Oregon: { athleteId: 30, name: "Dylan Raiola" } },
  sections: [
    { offenseTeam: "Michigan", defenseTeam: "Oregon", splits: [], edge: "even", biggestGap: "epa_per_db",
      qbVs: { name: "Tommy Carr", opponent: "Oregon", oppRank: 2, of: 136, games: [] },
      units: [{ title: "t", offenseTeam: "Michigan", defenseTeam: "Oregon", rows: [row("epa_per_db", 60, 50), row("sack_rate", 50, 50)] }] },
    { offenseTeam: "Oregon", defenseTeam: "Michigan", splits: [], edge: "even", biggestGap: null, qbVs: null,
      units: [{ title: "t", offenseTeam: "Oregon", defenseTeam: "Michigan", rows: [row("epa_per_db", 50, 50)] }] },
  ],
  availability: {
    Michigan: { flags: [], report: { conference: "Big Ten", url: null, when: null }, players: [
      { athleteId: 10, name: "Tommy Carr", role: "QB", share: null, shareOf: null, noStatsLastGame: false },
      { athleteId: 11, name: "Back Up", role: "QB2", share: null, shareOf: null, noStatsLastGame: true },
      { athleteId: 20, name: "Wr One", role: "WR", share: 0.31, shareOf: "receiving yards", noStatsLastGame: true }],
      backup: { athleteId: 11, name: "Back Up", games: 2, smallSample: true,
        cells: { epa_per_db: { value: -0.1, rank: 120, pct: 5 }, sack_rate: { value: 0.1, rank: 100, pct: 20 } },
        qbVs: { name: "Back Up", opponent: "Oregon", oppRank: 2, of: 136, games: [] } } },
    Oregon: { flags: [], report: { conference: "Big Ten", url: null, when: null }, players: [
      { athleteId: 30, name: "Dylan Raiola", role: "QB", share: null, shareOf: null, noStatsLastGame: false }], backup: null },
  },
});

describe("edge bands (port of units.py)", () => {
  it.each([[50, 50, "even"], [64.9, 50, "even"], [65, 50, "slight-offense"], [50, 84.9, "slight-defense"],
    [85, 50, "clear-offense"], [10, 90, "clear-defense"]] as const)("%s vs %s → %s", (o, d, e) => {
    expect(edge(o, d)).toBe(e);
  });
  it("null side → null", () => expect(edge(null, 50)).toBeNull());
  it("sideEdge maps the mean gap through edge(50+g/2, 50-g/2)", () => {
    // gaps -40 and -40 → mean -40 → edge(30, 70) → gap -40 → clear-defense
    expect(sideEdge([row("a", 10, 50), row("b", 30, 70)])).toBe("clear-defense");
    // mean gap 20 → edge(60, 40) → gap 20 → slight-offense
    expect(sideEdge([row("a", 70, 50)])).toBe("slight-offense");
    expect(sideEdge([row("a", null, 50)])).toBeNull();
  });
  it("biggestGap is the row with the largest absolute gap", () => {
    expect(biggestGap([row("a", 60, 50), row("b", 20, 50), row("c", 90, 70)])).toBe("b");
  });
});

describe("applyWhatIf", () => {
  it("starter Out swaps in the backup's cells and recomputes edges", () => {
    const out = applyWhatIf(m(), new Set([10]));
    const sec = out.sections[0];
    const [epa, sack] = sec.units[0].rows;
    expect(epa.offense).toEqual({ value: -0.1, rank: 120, pct: 5 });
    expect(epa.edge).toBe("clear-defense");
    expect(sack.offense.rank).toBe(100);
    expect(sack.edge).toBe("slight-defense");
    expect(sec.edge).toBe("clear-defense");
    expect(sec.biggestGap).toBe("epa_per_db");
    expect(sec.qbVs?.name).toBe("Back Up");
    expect(out.quarterbacks.Michigan).toEqual({ athleteId: 11, name: "Back Up" });
    expect(out.sections[1]).toEqual(m().sections[1]);
  });
  it("never mutates its input", () => {
    const input = m();
    const before = JSON.stringify(input);
    applyWhatIf(input, new Set([10]));
    expect(JSON.stringify(input)).toBe(before);
  });
  it("backup with no numbers: offense cells null, no verdicts, no side edge", () => {
    const input = m();
    input.availability!.Michigan.backup!.cells = { epa_per_db: { value: null, rank: null, pct: null } };
    const sec = applyWhatIf(input, new Set([10])).sections[0];
    expect(sec.units[0].rows.map((r) => r.offense)).toEqual([{ value: null, rank: null, pct: null }, { value: null, rank: null, pct: null }]);
    expect(sec.units[0].rows.map((r) => r.edge)).toEqual([null, null]);
    expect(sec.edge).toBeNull();
    expect(sec.biggestGap).toBeNull();
  });
  it("no backup or receivers Out → unchanged", () => {
    expect(applyWhatIf(m(), new Set([30, 20]))).toEqual(m());
    expect(applyWhatIf(m(), new Set())).toEqual(m());
  });
  it("defaultsOut is everyone flagged, never the backup", () => {
    expect([...defaultsOut(m())]).toEqual([20]);
  });
});
