import { describe, expect, it } from "vitest";
import { groupByDay, passes, weekChips } from "./filters";
import type { GameSummary } from "./types";

const g = (o: Partial<GameSummary>): GameSummary => ({
  id: 1, season: 2026, week: 11, seasonType: "regular", start: "2026-11-14T17:00:00.000Z", home: "Oregon", away: "Michigan",
  homeConf: "Big Ten", awayConf: "Big Ten", neutral: false, venue: "Autzen", completed: false, homePoints: null,
  awayPoints: null, hasBreakdown: true, homeRank: null, awayRank: null, ...o,
});

describe("passes", () => {
  it("all", () => expect(passes(g({}), "all", [])).toBe(true));
  it("top25 needs a ranked team", () => {
    expect(passes(g({}), "top25", [])).toBe(false);
    expect(passes(g({ awayRank: 18 }), "top25", [])).toBe(true);
  });
  it("mine", () => {
    expect(passes(g({}), "mine", ["Oregon"])).toBe(true);
    expect(passes(g({}), "mine", ["Texas"])).toBe(false);
  });
  it("conference", () => {
    expect(passes(g({}), "Big Ten", [])).toBe(true);
    expect(passes(g({}), "SEC", [])).toBe(false);
  });
  it("Pac-12 counts as Group of 5", () => expect(passes(g({ homeConf: "Pac-12", awayConf: "SEC" }), "g5", [])).toBe(true));
  it("P4 only is not g5", () => expect(passes(g({}), "g5", [])).toBe(false));
  it("independents", () => {
    expect(passes(g({ homeConf: "FBS Independents" }), "ind", [])).toBe(true);
    expect(passes(g({ homeConf: "FBS Independents", awayConf: "Big Ten" }), "g5", [])).toBe(false);
  });
  it("FCS opponent (null conf) is not g5", () => expect(passes(g({ homeConf: null as unknown as string }), "g5", [])).toBe(false));
});

describe("groupByDay", () => {
  const label = (iso: string) => new Date(iso).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
  it("groups by local day in kickoff order", () => {
    const a = g({ id: 1, start: "2026-11-14T20:00:00.000Z" });
    const b = g({ id: 2, start: "2026-11-14T16:00:00.000Z" });
    const c = g({ id: 3, start: "2026-11-13T17:00:00.000Z" });
    const out = groupByDay([a, b, c]);
    expect(out.map((d) => d.day)).toEqual([label(c.start), label(a.start)]);
    expect(out[1].games.map((x) => x.id)).toEqual([2, 1]);
  });
});

describe("weekChips", () => {
  it("regular weeks then bowls", () => {
    const out = weekChips([g({ week: 2 }), g({ week: 1 }), g({ week: 2 }), g({ week: 1, seasonType: "postseason" })]);
    expect(out).toEqual([{ value: "1", label: "Wk 1" }, { value: "2", label: "Wk 2" }, { value: "post", label: "Bowls" }]);
  });
});
