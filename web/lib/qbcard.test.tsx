import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import QbCard from "@/components/matchup/QbCard";
import type { QbGame, QbVs } from "./types";

const G = (opponent: string, oppRank: number, result: "W" | "L"): QbGame =>
  ({ gameId: oppRank, season: 2025, opponent, oppRank, stage: null, result, pf: 30, pa: 20, epaPerDb: 0.2, dropbacks: 30 });
const qb: QbVs = { name: "Gunner Stockton", opponent: "Missouri", oppRank: 54, of: 138,
  games: [G("Notre Dame", 1, "L"), G("Texas", 40, "W"), G("Auburn", 67, "L"), G("Kentucky", 77, "W"), G("Marshall", 107, "W")] };
const html = (q: QbVs) => renderToString(<QbCard qb={q} offense="Georgia" teams={{}} />).replace(/<!-- -->/g, "");

describe("QbCard", () => {
  it("shows the opponent rank, both records and the line", () => {
    const h = html(qb);
    expect(h).toContain("Missouri pass D");
    expect(h).toContain("of 138");
    expect(h).toContain("1-1");
    expect(h).toContain("2-1");
    expect(h).toContain("▲ Missouri 54th");
  });
  it("puts games past the first two below the line behind More", () => {
    expect(html(qb)).toContain("More: 1 more game");
  });
  it("no games yet", () => expect(html({ ...qb, games: [] })).toContain("No starts against FBS pass defenses on record yet."));
});
