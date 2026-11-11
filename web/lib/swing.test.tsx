import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import SwingCard from "@/components/matchup/SwingCard";
import EdgeCard from "@/components/matchup/EdgeCard";
import { badgeFor, chipText, overallText } from "./swing";
import type { Section, Swing, UnitRow } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");
const sw: Swing = {
  overallEdge: { edge: "slight", team: "Georgia" }, note: null,
  drivers: [
    { key: "sd_sr", label: "Early-down success", offense: "Missouri", defense: "Georgia", edge: "clear", favors: "Georgia",
      offRank: 100, defRank: 27, of: 136, cue: "Watch Missouri on first and second down.", score: 0.98 },
    { key: "explosive", label: "Big plays", offense: "Missouri", defense: "Georgia", edge: "clear", favors: "Missouri",
      offRank: 17, defRank: 77, of: 136, cue: "One or two big plays by Missouri could decide it.", score: 0.3 }],
  storylines: [{ text: "Gunner Stockton is 7-2 at home as a starter.", sample: "9 games", kind: "storyline" },
    { text: "Michigan travels about 1,970 miles for this one.", sample: "schedule", kind: "storyline" }],
};

describe("SwingCard", () => {
  it("lists drivers in order with matchup, ranks, edge and cue, then labeled storylines", () => {
    const h = html(<SwingCard swing={sw} teams={{}} />);
    expect(h).toContain("What could swing this game");
    expect(h.indexOf("Early-down success")).toBeLessThan(h.indexOf("Big plays"));
    expect(h).toContain("Missouri offense vs. Georgia defense · 100th vs. 27th of 136");
    expect(h).toContain("Big edge Georgia");
    expect(h).toContain("Watch Missouri on first and second down.");
    expect(h).toContain("Storylines to watch");
    expect(h).toContain("Storyline · 9 games");
    expect(h).toContain("Storyline · Schedule");
    expect(h.indexOf("Big plays")).toBeLessThan(h.indexOf("Gunner Stockton"));
    expect(h).toContain("Not a prediction.");
    expect(h).not.toMatch(/%|odds|50\/50/);
  });
  it("shows the note when there are no drivers", () => {
    const h = html(<SwingCard swing={{ ...sw, drivers: [], note: "Too early in the season: Oregon has fewer than 3 games against FBS teams." }} teams={{}} />);
    expect(h).toContain("Too early in the season");
  });
  it("renders nothing for old data", () => {
    expect(html(<SwingCard swing={null} teams={{}} />)).toBe("");
  });
});

describe("badges, chip, overall edge", () => {
  const row = (key: string, isKey?: boolean) => ({ key, label: key, format: "pct", offense: { value: 1, rank: 1 },
    defense: { value: 1, rank: 1 }, edge: null, isKey } as UnitRow);
  const sec = (rows: UnitRow[], biggestGap: string | null) =>
    ({ offenseTeam: "A", defenseTeam: "B", splits: [], biggestGap, units: [{ title: "t", offenseTeam: "A", defenseTeam: "B", rows }] } as Section);
  it("KEY replaces Biggest edge; Biggest edge stays when the block has no key row", () => {
    const s1 = sec([row("epa_per_db", true), row("int_rate", false)], "int_rate");
    expect(badgeFor(s1.units[0].rows[0], s1)).toBe("Key");
    expect(badgeFor(s1.units[0].rows[1], s1)).toBeNull();
    const s2 = sec([row("epa_per_db", false), row("int_rate", false)], "int_rate");
    expect(badgeFor(s2.units[0].rows[1], s2)).toBe("Biggest edge");
  });
  it("home chip: Key when a key factor exists, else Edge", () => {
    expect(chipText({ keyFactor: { label: "Big plays", favors: "Oregon" }, gap: { key: "x", label: "Sacks", favors: "Oregon" } } as never, "ORE"))
      .toBe("Key: Big plays · ORE");
    expect(chipText({ keyFactor: null, gap: { key: "x", label: "Sacks", favors: "Oregon" } } as never, "ORE")).toBe("Edge: Sacks · ORE");
    expect(chipText({ keyFactor: null, gap: null } as never, "ORE")).toBeNull();
  });
  it("overall edge in words", () => {
    expect(overallText({ edge: "slight", team: "Georgia" })).toBe("Overall: Slight edge Georgia");
    expect(overallText({ edge: "clear", team: "Georgia" })).toBe("Overall: Big edge Georgia");
    expect(overallText({ edge: "even", team: null })).toBe("Overall: Even");
    expect(overallText(null)).toBeNull();
    expect(html(<EdgeCard sections={[]} teams={{}} overall={{ edge: "slight", team: "Georgia" }} home="Georgia" away="Missouri" />)).toContain("Overall: Slight edge Georgia");
  });
});
