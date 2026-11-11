import { describe, expect, it } from "vitest";
import { myTeamGames } from "./filters";
import type { GameSummary } from "./types";

const g = (o: Partial<GameSummary>): GameSummary => ({ id: 1, season: 2026, week: 11, seasonType: "regular",
  start: "2026-11-14T20:30:00.000Z", home: "Texas Tech", away: "West Virginia", homeConf: "Big 12", awayConf: "Big 12",
  neutral: false, venue: null, completed: false, homePoints: null, awayPoints: null, hasBreakdown: true, ...o });

const games = [g({ id: 10, week: 10 }), g({ id: 11, week: 11, home: "Utah" }), g({ id: 12, week: 12, home: "Houston", away: "Baylor" })];

describe("My Teams follows the selected week", () => {
  it("shows the favorite's game in the week you picked", () =>
    expect(myTeamGames(games, "10", ["West Virginia"]).map((x) => x.id)).toEqual([10]));
  it("changes when you switch weeks", () =>
    expect(myTeamGames(games, "11", ["West Virginia"]).map((x) => x.id)).toEqual([11]));
  it("empty when your teams don't play that week", () =>
    expect(myTeamGames(games, "12", ["West Virginia"])).toEqual([]));
  it("empty with no week or no favorites", () => {
    expect(myTeamGames(games, "", ["West Virginia"])).toEqual([]);
    expect(myTeamGames(games, "10", [])).toEqual([]);
  });
});
