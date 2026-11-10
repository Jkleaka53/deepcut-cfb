import { describe, expect, it } from "vitest";
import { matchGame, normalize } from "./search";
import type { GameSummary, PlayerEntry } from "./types";

const game = (over: Partial<GameSummary> = {}): GameSummary => ({
  id: 1, season: 2025, week: 9, seasonType: "regular", start: "2025-10-25T23:30:00Z",
  home: "Texas Tech", away: "West Virginia", homeConf: "Big 12", awayConf: "Big 12",
  neutral: false, venue: null, completed: true, homePoints: 35, awayPoints: 17, hasBreakdown: true,
  ...over,
});

const players: PlayerEntry[] = [
  { athleteId: 7, name: "Michael Hawkins Jr.", team: "West Virginia", position: "QB", season: 2025 },
  { athleteId: 8, name: "Old Guy", team: "Texas Tech", position: "QB", season: 2023 },
];

describe("normalize", () => {
  it("strips accents", () => expect(normalize("San José State")).toBe("san jose state"));
  it("strips apostrophes", () => expect(normalize("Hawai'i")).toBe("hawaii"));
  it("turns & into and", () => expect(normalize("Texas A&M")).toBe("texas aandm"));
  it("collapses spaces and trims", () => expect(normalize("  Ole   Miss ")).toBe("ole miss"));
});

describe("matchGame", () => {
  it("matches a team name", () => expect(matchGame(game(), "texas tech", players)).toBe(true));
  it("matches an accented team without the accent", () =>
    expect(matchGame(game({ home: "San José State" }), "san jose", players)).toBe(true));
  it("matches hawaii", () => expect(matchGame(game({ away: "Hawai'i" }), "hawaii", players)).toBe(true));
  it("matches a conference", () => expect(matchGame(game(), "big 12", players)).toBe(true));
  it("matches a player on either team in that season", () =>
    expect(matchGame(game(), "hawkins", players)).toBe(true));
  it("does not match a player from another season", () =>
    expect(matchGame(game(), "old guy", players)).toBe(false));
  it("empty query matches everything", () => expect(matchGame(game(), "  ", players)).toBe(true));
  it("non-match returns false", () => expect(matchGame(game(), "oregon", players)).toBe(false));
});
