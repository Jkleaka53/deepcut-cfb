import { describe, expect, it } from "vitest";
import { gotwFor } from "./gotw";
import type { GameSummary } from "./types";

const g = (o: Partial<GameSummary>): GameSummary => ({ id: 1, season: 2026, week: 11, seasonType: "regular",
  start: "2026-11-14T20:30:00.000Z", home: "Georgia", away: "Missouri", homeConf: "SEC", awayConf: "SEC", neutral: false,
  venue: null, completed: false, homePoints: null, awayPoints: null, hasBreakdown: true, homeRank: 1, ...o });

const games = [g({ id: 1 }), g({ id: 2, week: 12 })];
const picks = { "11": { id: 1, why: "Why." }, "12": { id: 2, why: "Other." } };

describe("gotwFor", () => {
  it("returns the selected week's pick", () => expect(gotwFor(picks, "11", games, "all", [])?.game.id).toBe(1));
  it("shows under a filter the game passes", () => expect(gotwFor(picks, "11", games, "SEC", [])?.why).toBe("Why."));
  it("hidden under a filter it fails", () => expect(gotwFor(picks, "11", games, "Big Ten", [])).toBeNull());
  it("no pick for the week", () => expect(gotwFor(picks, "5", games, "all", [])).toBeNull());
  it("missing file", () => expect(gotwFor({}, "11", games, "all", [])).toBeNull());
  it("pick not in games list", () => expect(gotwFor({ "11": { id: 99, why: "x" } }, "11", games, "all", [])).toBeNull());
});
