import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import PickCard from "@/components/PickCard";
import ScoreRow from "@/components/ScoreRow";
import { pickFor } from "./gotw";
import type { GameSummary } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");
const g = (o: Partial<GameSummary>): GameSummary => ({ id: 401856856, season: 2026, week: 10, seasonType: "regular",
  start: "2026-10-31T23:00:00.000Z", home: "Texas Tech", away: "West Virginia", homeConf: "Big 12", awayConf: "Big 12",
  neutral: false, venue: null, completed: false, homePoints: null, awayPoints: null, hasBreakdown: true, ...o });
const why = "Both offenses score efficiently and both defenses give it up: offenses rank 4th and 9th.";

describe("Shootout of the Week card", () => {
  it("shows tag, teams, why and a link to the game", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({})} why={why} teams={{}} />);
    for (const s of ["Shootout of the Week", "West Virginia", "Texas Tech", why, "/game?season=2026&amp;id=401856856"])
      expect(h).toContain(s);
  });
  it("is the small card, not the Game of the Week card", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({})} why={why} teams={{}} />);
    expect(h).toContain("pick-card");
    expect(h).not.toMatch(/class="gotw[ "]/);
  });
  it("shows the final score once played", () => {
    const h = html(<PickCard tag="Shootout of the Week" game={g({ completed: true, awayPoints: 48, homePoints: 53 })}
      why={why} teams={{}} />);
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
