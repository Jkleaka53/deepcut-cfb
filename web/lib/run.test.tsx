import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import EdgeCard from "@/components/matchup/EdgeCard";
import { edgeLine, runView, topGaps, visibleTabs } from "./matchup";
import { fmt } from "./format";
import { badgeFor } from "./swing";
import { normalizeMatchup } from "./normalize";
import type { Matchup, Section, UnitRow } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");
const row = (key: string, o: number, d: number, extra: Partial<UnitRow> = {}): UnitRow => ({
  key, label: key, format: "pct", edge: "even", offense: { value: 0.1, rank: 1, pct: o }, defense: { value: 0.1, rank: 1, pct: d }, ...extra });
const sec = (runUnits: Section["runUnits"]): Section => ({
  offenseTeam: "Georgia", defenseTeam: "Missouri", splits: [], edge: "even", biggestGap: "epa_per_db",
  units: [{ title: "Passing", offenseTeam: "Georgia", defenseTeam: "Missouri", rows: [row("epa_per_db", 55, 50)] }],
  runUnits, runEdge: "slight-defense", runBiggestGap: "line_yards" });
const runs = [{ title: "Run blocking vs. run defense front", offenseTeam: "Georgia", defenseTeam: "Missouri",
  rows: [row("stuff_rate", 40, 45), row("line_yards", 10, 90, { format: "yds" })] }];

describe("run phase", () => {
  it("formats yards per carry", () => {
    expect(fmt(3.456, "yds")).toBe("3.5 yds");
  });

  it("runView swaps in the run tables and run edge", () => {
    const v = runView(sec(runs))!;
    expect(v.units[0].title).toBe("Run blocking vs. run defense front");
    expect(v.edge).toBe("slight-defense");
    expect(v.biggestGap).toBe("line_yards");
    expect(runView(sec(null))).toBeNull();
  });

  it("edge line says runs for the run view", () => {
    expect(edgeLine(runView(sec(runs))!, "runs")).toEqual({ text: "Georgia runs → Missouri D · Slight edge", team: "Missouri" });
  });

  it("biggest edges can pick a run row and know it is a run", () => {
    const top = topGaps([sec(runs)], 1);
    expect(top[0].row.key).toBe("line_yards");
    expect(top[0].phase).toBe("run");
  });

  it("Running game tab only when the data has run tables", () => {
    const base = { availability: {}, sections: [sec(runs)] } as unknown as Matchup;
    expect(visibleTabs(base)).toEqual(["preview", "passing", "running", "qb"]);
    expect(visibleTabs({ ...base, sections: [sec(null)] })).toEqual(["preview", "passing", "qb"]);
  });

  it("old JSON without runUnits normalizes to null", () => {
    const raw = { game: { id: 1 }, sections: [{ ...sec(runs), runUnits: undefined, runEdge: undefined }] } as unknown as Matchup;
    const s = normalizeMatchup(raw).sections[0];
    expect(s.runUnits).toBeNull();
    expect(s.runEdge ?? null).toBeNull();
  });

  it("a Key run row gets the Key badge inside the run view", () => {
    const keyed = [{ ...runs[0], rows: [row("stuff_rate", 40, 45, { isKey: true }), row("line_yards", 10, 90)] }];
    const v = runView(sec(keyed))!;
    expect(badgeFor(v.units[0].rows[0], v)).toBe("Key");
    expect(badgeFor(v.units[0].rows[1], v)).toBeNull();
    expect(badgeFor(runView(sec(runs))!.units[0].rows[1], runView(sec(runs))!)).toBe("Biggest edge");
  });

  it("edge card shows a run line per side", () => {
    const h = html(<EdgeCard sections={[sec(runs)]} teams={{}} />);
    expect(h).toContain("Georgia runs → Missouri D · Slight edge");
  });
});
