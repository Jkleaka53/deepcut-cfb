import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import AvailabilityCard from "../components/matchup/AvailabilityCard";
import HeadToHead from "../components/matchup/HeadToHead";
import { groupByDay } from "./filters";
import { localKickoff } from "./format";
import { visibleTabs } from "./matchup";
import type { GameSummary, Matchup, TeamInfo, UnitRow } from "./types";

const g = (o: Partial<GameSummary>): GameSummary => ({
  id: 1, season: 2026, week: 11, seasonType: "regular", start: "2026-11-14T17:00:00.000Z", home: "A", away: "B",
  homeConf: "SEC", awayConf: "SEC", neutral: false, venue: null, completed: false, homePoints: null, awayPoints: null,
  hasBreakdown: true, ...o,
});

describe("TBA kickoffs", () => {
  it("groups a TBA game by its UTC date, not the placeholder hour in local time", () => {
    const tba = g({ id: 2, start: "2026-11-14T05:00:00.000Z", startTimeTBD: true });
    const want = new Date(Date.UTC(2026, 10, 14, 12)).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
    expect(groupByDay([tba])[0].day).toBe(want);
  });
  it("TBA label uses the UTC weekday", () => expect(localKickoff("2026-11-14T05:00:00.000Z", true)).toBe("Sat · TBA"));
});

const T = (fill: string, dark: string): TeamInfo => ({ school: "x", id: null, abbr: "X", conference: null, fill, barDark: dark,
  textLight: fill, textDark: "#fee11a", logo: null, logoDark: null });

describe("dark-mode bars", () => {
  it("bar carries each team's own dark-theme colour (barDark), not textDark", () => {
    const row: UnitRow = { key: "k", label: "L", format: "pct", edge: "clear-defense", explain: "",
      offense: { value: 0.03, rank: 130, pct: 5 }, defense: { value: 0.02, rank: 49, pct: 60 } };
    const html = renderToString(<HeadToHead row={row} offense="M" defense="O" teams={{ M: T("#00274c", "#ffcb05"), O: T("#007030", "#4fd18a") }} />);
    expect(html).toContain("--bd:#ffcb05");
    expect(html).toContain("--bd:#4fd18a");
  });
});

describe("availability wording", () => {
  it("known conference without a link is not told no report exists", () => {
    const html = renderToString(<AvailabilityCard team="Michigan" data={{ flags: [], report: { conference: "Big Ten", url: null, when: "Posts Wednesday", publishes: true } }} />);
    expect(html).not.toContain("No official availability report");
    expect(html.replace(/<!-- -->/g, "")).toContain("Check the Big Ten");
  });
});

describe("old-format data hides new sections", () => {
  const base = { game: g({}), earlySeason: false, notes: [], quarterbacks: {}, venue: null } as unknown as Matchup;
  const row: UnitRow = { key: "k", label: "L", format: "pct", edge: null, offense: { value: 1, rank: 1, pct: null }, defense: { value: 1, rank: 1, pct: null } };
  const sec = { offenseTeam: "B", defenseTeam: "A", splits: [], units: [{ title: "t", offenseTeam: "B", defenseTeam: "A", rows: [row] }] };
  it("no availability, no pct -> no Availability tab and no gaps", () => {
    expect(visibleTabs({ ...base, sections: [sec], availability: {} })).toEqual(["preview", "passing", "qb"]);
  });
  it("with availability -> all tabs", () => {
    expect(visibleTabs({ ...base, sections: [sec], availability: { A: { flags: [], report: { conference: null, url: null, when: null } } } }))
      .toEqual(["preview", "passing", "qb", "availability"]);
  });
});
