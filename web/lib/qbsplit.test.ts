import { describe, expect, it } from "vitest";
import { lastName, rowLabel, splitAt, summary, visibleRows } from "./qbsplit";
import type { QbGame, QbVs } from "./types";

const G = (opponent: string, oppRank: number, result: "W" | "L", pf: number, pa: number, epaPerDb: number, dropbacks = 30,
  season = 2025, stage: QbGame["stage"] = null): QbGame =>
  ({ gameId: oppRank * 10 + season, season, opponent, oppRank, stage, result, pf, pa, epaPerDb, dropbacks });

const STOCKTON: QbVs = { name: "Gunner Stockton", opponent: "Missouri", oppRank: 54, of: 138, games: [
  G("Notre Dame", 1, "L", 10, 23, -0.04, 32, 2024), G("Oklahoma", 11, "W", 41, 13, -0.18, 21, 2026),
  G("Ole Miss", 24, "L", 34, 39, 0.28, 35, 2025, "CFP"), G("Alabama", 37, "L", 21, 24, 0.13, 21),
  G("Texas", 40, "W", 35, 10, 0.36, 31), G("Auburn", 67, "L", 24, 27, 0.18, 39, 2026),
  G("Tennessee", 69, "W", 44, 41, 0.26, 36), G("Kentucky", 77, "W", 35, 14, 0.26, 25), G("Marshall", 107, "W", 45, 7, 0.41, 20),
] };

describe("splitAt", () => {
  it("counts the line rank as 'as good or better'", () => {
    const s = splitAt(STOCKTON.games, 40);
    expect(s.above).toMatchObject({ w: 2, l: 3, games: 5 });
    expect(s.below).toMatchObject({ w: 3, l: 1, games: 4 });
  });
  it("points per pass weighted by dropbacks", () => {
    const s = splitAt([G("A", 1, "W", 1, 0, 0.5, 10), G("B", 2, "W", 1, 0, -0.1, 30)], 5);
    expect(s.above.epa).toBeCloseTo(0.05, 5);
    expect(s.below).toMatchObject({ games: 0, epa: null });
  });
});

describe("summary", () => {
  it("record plus where the losses came", () =>
    expect(summary({ ...STOCKTON, oppRank: 40 })).toBe(
      "Against pass defenses as good as Missouri's or better, Stockton is 2-3. All 3 losses came against pass defenses ranked 37th or better."));
  it("single game", () =>
    expect(summary({ ...STOCKTON, oppRank: 5 })).toBe("Stockton has faced one pass defense as good as Missouri's: a 10-23 loss to Notre Dame (1st)."));
  it("single win", () =>
    expect(summary({ ...STOCKTON, games: STOCKTON.games.slice(1), oppRank: 11 })).toBe(
      "Stockton has faced one pass defense as good as Missouri's: a 41-13 win over Oklahoma (11th)."));
  it("none yet", () => expect(summary({ ...STOCKTON, games: STOCKTON.games.slice(4), oppRank: 20 })).toBe(
    "Stockton hasn't faced a pass defense as good as Missouri's yet."));
  it("no rank for this week's defense", () => expect(summary({ ...STOCKTON, oppRank: null })).toBe(""));
  it("never predicts", () => expect(summary(STOCKTON).toLowerCase()).not.toMatch(/will|should|likely|50\/50|injur/));
});

describe("visibleRows", () => {
  it("all above the line plus two below", () => {
    const v = visibleRows(STOCKTON.games, 40);
    expect(v.above.map((g) => g.oppRank)).toEqual([1, 11, 24, 37, 40]);
    expect(v.below.map((g) => g.oppRank)).toEqual([67, 69]);
    expect(v.hidden.map((g) => g.oppRank)).toEqual([77, 107]);
  });
});

describe("names and labels", () => {
  it.each([["Gunner Stockton", "Stockton"], ["Michael Hawkins Jr.", "Hawkins"], ["Joe Smith III", "Smith"], ["Cher", "Cher"]])(
    "%s", (n, want) => expect(lastName(n)).toBe(want));
  it("season and stage", () => {
    expect(rowLabel(STOCKTON.games[2])).toBe("'25 CFP");
    expect(rowLabel(STOCKTON.games[0])).toBe("'24");
  });
});
