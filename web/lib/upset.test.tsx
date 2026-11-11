import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import UpsetCard from "@/components/UpsetCard";
import PickNote from "@/components/matchup/PickNote";
import { pickFor, pickWhyFor } from "./gotw";
import type { GameSummary } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "").replace(/&#x27;/g, "'");
const g = (o: Partial<GameSummary>): GameSummary => ({ id: 401, season: 2026, week: 11, seasonType: "regular",
  start: "2026-11-14T20:30:00.000Z", home: "Oregon", away: "Michigan", homeConf: "Big Ten", awayConf: "Big Ten",
  neutral: false, venue: null, completed: false, homePoints: null, awayPoints: null, hasBreakdown: true, ...o });
const teams = { Michigan: { fill: "#00274c", abbr: "MICH" }, Oregon: { fill: "#154733", abbr: "ORE" } } as never;
const odds = { source: "DraftKings", home: 78, away: 22 };
const why = "Michigan has the edge in Big plays: Michigan's offense ranks 9th against an Oregon defense that ranks 80th of 136.";

describe("Upset Watch card", () => {
  const h = html(<UpsetCard game={g({})} odds={odds} teams={teams} />);
  it("shows the tag, the source and both whole-number odds, away first", () => {
    expect(h).toContain("Upset Watch");
    expect(h).toContain("DraftKings odds");
    expect(h.indexOf("22%")).toBeGreaterThan(-1);
    expect(h.indexOf("22%")).toBeLessThan(h.indexOf("78%"));
    expect(h).toContain("MICH");
  });
  it("bar widths follow the odds", () => {
    expect(h).toMatch(/width:22%/);
    expect(h).toMatch(/width:78%/);
  });
  it("no reason on the home card", () => expect(h).not.toContain("Why that could be wrong"));
  it("is the slim striped card", () => expect(h).toContain("pick-card"));
});

describe("Upset Watch on the game page", () => {
  it("note shows the tag, the heading and the reason", () => {
    const h = html(<PickNote tag="Upset Watch" heading="Why that could be wrong" why={why} />);
    for (const s of ["Upset Watch", "Why that could be wrong", why]) expect(h).toContain(s);
  });
  it("shootout note still works without a heading", () => {
    const h = html(<PickNote tag="Shootout of the Week" why="Lots of expected scoring." />);
    expect(h).toContain("Shootout of the Week");
    expect(h).not.toContain("Why that could be wrong");
  });
  it("finds the reason and hides without a pick or under a failing filter", () => {
    const picks = { "11": { id: 401, why, odds } };
    expect(pickWhyFor(picks, 401)).toBe(why);
    expect(pickFor(picks, "11", [g({})], "Big Ten", [])?.game.id).toBe(401);
    expect(pickFor(picks, "11", [g({})], "SEC", [])).toBeNull();
    expect(pickFor({}, "11", [g({})], "all", [])).toBeNull();
  });
});
