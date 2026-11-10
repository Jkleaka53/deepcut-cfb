import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import ScoreRow from "@/components/ScoreRow";
import type { GameSummary, TeamInfo } from "./types";

const game: GameSummary = { id: 7, season: 2026, week: 11, seasonType: "regular", start: "2026-11-14T20:30:00.000Z",
  home: "Oregon", away: "Michigan", homeConf: "Big Ten", awayConf: "Big Ten", neutral: false, venue: null, completed: false,
  homePoints: null, awayPoints: null, hasBreakdown: true, gap: { key: "int_rate", label: "Interceptions", favors: "Oregon" } };
const ore: TeamInfo = { school: "Oregon", id: 2483, abbr: "ORE", conference: "Big Ten", fill: "#007030", textLight: "#007030",
  textDark: "#4fd18a", logo: null, logoDark: null };

const text = (html: string) => html.replace(/<!-- -->/g, "");

describe("home edge chip", () => {
  it("names the stat and the team it favors", () => {
    const html = text(renderToString(<ScoreRow game={game} teams={{ Oregon: ore }} favorites={[]} onToggle={() => {}} />));
    expect(html).toContain("Edge: Interceptions · ORE");
    expect(html).not.toContain("Gap:");
  });
  it("falls back to the school name without team info", () => {
    const html = text(renderToString(<ScoreRow game={game} teams={{}} favorites={[]} onToggle={() => {}} />));
    expect(html).toContain("Edge: Interceptions · Oregon");
  });
});
