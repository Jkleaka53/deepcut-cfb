import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import Hero from "@/components/matchup/Hero";
import { recordText } from "./format";
import type { Matchup } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");

describe("team records", () => {
  it("formats overall then conference", () => {
    expect(recordText({ wins: 8, losses: 2, confWins: 5, confLosses: 1, conference: "SEC" })).toBe("8-2 · 5-1 SEC");
    expect(recordText({ wins: 7, losses: 3, confWins: 0, confLosses: 0, conference: null })).toBe("7-3");
    expect(recordText(undefined)).toBeNull();
  });

  it("hero shows each team's record under its name", () => {
    const m = { game: { away: "Missouri", home: "Georgia", completed: false, awayPoints: null, homePoints: null, neutral: false,
      start: "2026-11-14T20:30:00.000Z", startTimeTBD: false }, venue: null, quarterbacks: {},
      records: { Missouri: { wins: 6, losses: 3, confWins: 3, confLosses: 3, conference: "SEC" },
                 Georgia: { wins: 8, losses: 1, confWins: 6, confLosses: 1, conference: "SEC" } } } as unknown as Matchup;
    const h = html(<Hero m={m} teams={{}} />);
    expect(h).toContain("6-3 · 3-3 SEC");
    expect(h).toContain("8-1 · 6-1 SEC");
  });
});
