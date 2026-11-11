import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import PickCard from "@/components/PickCard";
import PickNote from "@/components/matchup/PickNote";
import ScoreRow from "@/components/ScoreRow";
import { pickFor, pickWhyFor } from "./gotw";
import type { GameSummary } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");
const g = (o: Partial<GameSummary>): GameSummary => ({ id: 401856856, season: 2026, week: 10, seasonType: "regular",
  start: "2026-10-31T23:00:00.000Z", home: "Texas Tech", away: "West Virginia", homeConf: "Big 12", awayConf: "Big 12",
  neutral: false, venue: null, completed: false, homePoints: null, awayPoints: null, hasBreakdown: true, ...o });
const why = "Both offenses score efficiently and both defenses give it up: offenses rank 4th and 9th.";

const teams = { "West Virginia": { fill: "#002855" }, "Texas Tech": { fill: "#cc0000" } } as never;

describe("Shootout of the Week card", () => {
  it("shows tag, teams and a link to the game", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({})} teams={{}} />);
    for (const s of ["Shootout of the Week", "West Virginia", "Texas Tech", "/game?season=2026&amp;id=401856856"])
      expect(h).toContain(s);
  });
  it("keeps the reason off the home page", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({})} teams={{}} />);
    expect(h).not.toContain("Why watch");
  });
  it("uses the team-color split like Game of the Week, as the small card", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({})} teams={teams} />);
    expect(h).toContain("pick-card");
    expect(h).not.toMatch(/class="gotw[ "]/);
    expect(h).toMatch(/linear-gradient\(115deg, #002855 0 49\.6%, #cc0000 50\.4% 100%\)/);
  });
  it("shows the final score once played", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({ completed: true, awayPoints: 48, homePoints: 53 })}
      teams={{}} />);
    expect(h).toContain("48 – 53");
    expect(h).toContain("Final");
  });
  it("card hidden without a pick", () => expect(pickFor({}, "10", [g({})], "all", [])).toBeNull());
  it("card respects the filter", () => {
    const picks = { "10": { id: 401856856, why } };
    expect(pickFor(picks, "10", [g({})], "Big 12", [])?.game.id).toBe(401856856);
    expect(pickFor(picks, "10", [g({})], "SEC", [])).toBeNull();
  });
});

describe("Shootout watch chip", () => {
  const row = (o: Partial<GameSummary>) =>
    html(<ScoreRow game={g(o)} teams={{}} favorites={[]} onToggle={() => {}} />);
  it("shows when flagged", () => expect(row({ shootoutWatch: true })).toContain("Shootout watch"));
  it("absent otherwise", () => {
    expect(row({ shootoutWatch: false })).not.toContain("Shootout watch");
    expect(row({})).not.toContain("Shootout watch");
  });
});

describe("Shootout reason on the game page", () => {
  const picks = { "10": { id: 401856856, why }, "11": { id: 5, why: "Other." } };
  it("finds the reason for the picked game", () => expect(pickWhyFor(picks, 401856856)).toBe(why));
  it("nothing for other games or a missing file", () => {
    expect(pickWhyFor(picks, 7)).toBeNull();
    expect(pickWhyFor({}, 401856856)).toBeNull();
  });
  it("note shows the tag and the reason", () => {
    const h = html(<PickNote tag="Shootout of the Week" why={why} />);
    expect(h).toContain("Shootout of the Week");
    expect(h).toContain(why);
  });
});
