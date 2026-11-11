import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import EdgeMeter from "@/components/matchup/EdgeMeter";
import EdgeCard from "@/components/matchup/EdgeCard";
import ScoreRow from "@/components/ScoreRow";
import { edgeChipText } from "./swing";
import type { GameSummary, TeamInfo } from "./types";

const text = (html: string) => html.replace(/<!-- -->/g, "");
const om: TeamInfo = { school: "Ole Miss", id: 145, abbr: "MISS", conference: "SEC", fill: "#14213d", textLight: "#14213d",
  textDark: "#9fb3ff", logo: null, logoDark: null };

describe("edge meter", () => {
  it("shows team, band and score, filling toward the favored side", () => {
    const html = text(renderToString(
      <EdgeMeter overall={{ edge: "slight", team: "Ole Miss", score: 3.4 }} home="Ole Miss" away="Missouri" />));
    expect(html).toContain("Ole Miss");
    expect(html).toContain("Slight edge");
    expect(html).toContain("3.4");
    expect(html).toMatch(/class="em-fill"[^>]*style="left:50%;width:17%"/);
  });
  it("fills toward the away side from the center", () => {
    const html = text(renderToString(
      <EdgeMeter overall={{ edge: "clear", team: "Missouri", score: 9 }} home="Ole Miss" away="Missouri" />));
    expect(html).toMatch(/class="em-fill"[^>]*style="left:5%;width:45%"/);
    expect(html).toContain("Big edge");
  });
  it("says Even with no fill for an even game", () => {
    const html = text(renderToString(
      <EdgeMeter overall={{ edge: "even", team: null, score: 0.6 }} home="Ole Miss" away="Missouri" />));
    expect(html).toContain("Even");
    expect(html).toContain("0.6");
    expect(html).not.toContain("em-fill");
  });
  it("fills with the accent token, not a team color (team navies vanish in dark mode)", () => {
    const html = text(renderToString(
      <EdgeMeter overall={{ edge: "slight", team: "Ole Miss", score: 3.4 }} home="Ole Miss" away="Missouri" />));
    expect(html).not.toContain("#14213d");
  });
  it("is hidden when overall is null", () => {
    expect(renderToString(<EdgeMeter overall={null} home="A" away="B" />)).toBe("");
  });
  it("lists the cutoffs in the legend", () => {
    const html = text(renderToString(
      <EdgeMeter overall={{ edge: "slight", team: "Ole Miss", score: 3.4 }} home="Ole Miss" away="Missouri" />));
    expect(html).toContain("Under 2 Even · 2 to 8 Slight · 8+ Big");
  });
});

describe("edge card", () => {
  it("falls back to text when score missing", () => {
    const html = text(renderToString(
      <EdgeCard sections={[]} teams={{}} overall={{ edge: "slight", team: "X" }} home="X" away="Y" />));
    expect(html).toContain("Overall: Slight edge X");
  });
  it("uses the meter when score is present", () => {
    const html = text(renderToString(
      <EdgeCard sections={[]} teams={{ "Ole Miss": om }} overall={{ edge: "slight", team: "Ole Miss", score: 3.4 }}
        home="Ole Miss" away="Missouri" />));
    expect(html).toContain("em-fill");
    expect(html).not.toContain("Overall: Slight edge");
  });
});

describe("home edge-score chip", () => {
  it("formats band, team and score", () => {
    expect(edgeChipText({ band: "slight", team: "Ole Miss", score: 3.4 }, "MISS")).toBe("Slight edge · MISS 3.4");
    expect(edgeChipText({ band: "clear", team: "LSU", score: 8.2 }, "LSU")).toBe("Big edge · LSU 8.2");
  });
  it("is null for even or missing", () => {
    expect(edgeChipText({ band: "even", team: null, score: 1 }, "X")).toBeNull();
    expect(edgeChipText(null, "X")).toBeNull();
    expect(edgeChipText(undefined, "X")).toBeNull();
  });
  it("shows on the score row", () => {
    const game: GameSummary = { id: 1, season: 2026, week: 7, seasonType: "regular", start: "2026-10-11T20:00:00.000Z",
      home: "Ole Miss", away: "Missouri", homeConf: "SEC", awayConf: "SEC", neutral: false, venue: null, completed: false,
      homePoints: null, awayPoints: null, hasBreakdown: true, edge: { band: "slight", team: "Ole Miss", score: 3.7 } };
    const html = text(renderToString(<ScoreRow game={game} teams={{ "Ole Miss": om }} favorites={[]} onToggle={() => {}} />));
    expect(html).toContain("Slight edge · MISS 3.7");
  });
});
