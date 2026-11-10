import { describe, expect, it } from "vitest";
import { normalizeMatchup } from "./normalize";
import type { Matchup } from "./types";

const OLD = {
  game: { id: 1, season: 2026, week: 11, seasonType: "regular", start: "2026-11-14T20:30:00.000Z", home: "Oregon",
    away: "Michigan", homeConf: "Big Ten", awayConf: "Big Ten", neutral: false, venue: "Autzen", completed: false,
    homePoints: null, awayPoints: null, hasBreakdown: true },
  earlySeason: false, notes: [], quarterbacks: { Michigan: null, Oregon: null },
  sections: [{ offenseTeam: "Michigan", defenseTeam: "Oregon", splits: [],
    units: [{ title: "t", offenseTeam: "Michigan", defenseTeam: "Oregon",
      rows: [{ key: "int_rate", label: "INT rate", format: "pct", offense: { value: 0.03, rank: 130 },
        defense: { value: 0.02, rank: 49 }, edge: "clear-defense" }] }] }],
} as unknown as Matchup;

describe("normalizeMatchup", () => {
  it("fills new optional fields on old data", () => {
    const m = normalizeMatchup(OLD);
    expect(m.venue).toBeNull();
    expect(m.availability).toEqual({});
    expect(m.game.weather).toBeNull();
    expect(m.game.homeRank).toBeNull();
    expect(m.sections[0].edge).toBeNull();
    expect(m.sections[0].biggestGap).toBeNull();
    const row = m.sections[0].units[0].rows[0];
    expect(row.offense.pct).toBeNull();
    expect(row.explain).toBe("");
    expect(row.hint).toBeNull();
  });
  it("keeps values that exist", () => {
    const m = normalizeMatchup({ ...OLD, venue: { name: "Autzen", city: "Eugene", state: "OR", grass: true, dome: false } });
    expect(m.venue?.city).toBe("Eugene");
  });
});
