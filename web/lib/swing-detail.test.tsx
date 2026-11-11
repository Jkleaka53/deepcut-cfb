import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import SwingCard from "@/components/matchup/SwingCard";
import { formatStat } from "./swing";
import type { Driver, Swing } from "./types";

const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");
const cue = "Watch Ole Miss on 1st down: gaining 4 or more yards keeps them out of 3rd-and-long.";
const base: Driver = {
  key: "sd_sr", label: "Early-down success", offense: "Ole Miss", defense: "Missouri", edge: "clear", favors: "Ole Miss",
  offRank: 8, defRank: 96, of: 134, cue, score: 0.9,
  detail: { meaning: "M", format: "pct", offValue: 0.521, defAllows: 0.47, fbsAvg: 0.44, why: "W" },
};
const card = (d: Driver) => {
  const sw: Swing = { overallEdge: null, note: null, drivers: [d], storylines: [] };
  return html(<SwingCard swing={sw} teams={{}} />);
};

describe("formatStat", () => {
  it("formats by kind and says n/a when missing", () => {
    expect(formatStat(0.521, "pct")).toBe("52.1%");
    expect(formatStat(0.214, "epa")).toBe("+0.21");
    expect(formatStat(-0.05, "epa")).toBe("-0.05");
    expect(formatStat(1.274, "num")).toBe("1.27");
    expect(formatStat(null, "pct")).toBe("n/a");
    expect(formatStat(NaN, "num")).toBe("n/a");
  });
});

describe("swing reason pulldown", () => {
  it("driver with detail is a closed details in the swing group", () => {
    const h = card(base);
    expect(h).toContain("<details");
    expect(h).toContain('name="swing"');
    expect(h).not.toMatch(/<details[^>]* open/);
  });
  it("opened content shows meaning, table, why and cue", () => {
    const h = card(base);
    for (const s of ["M", "Ole Miss offense", "52.1%", "8th of 134", "Missouri defense allows", "47.0%",
      "96th of 134", "FBS average", "44.0%", "W", cue]) expect(h).toContain(s);
  });
  it("heading names the favored team", () => {
    expect(card(base)).toContain("Why Ole Miss has the edge");
    expect(card({ ...base, favors: "Missouri" })).toContain("Why Missouri has the edge");
  });
  it("missing value shows n/a", () => {
    const h = card({ ...base, detail: { ...base.detail!, defAllows: null } });
    expect(h).toContain("n/a");
    expect(h).not.toContain("NaN");
  });
  it("old driver without detail renders flat", () => {
    const h = card({ ...base, detail: undefined });
    expect(h).not.toContain("<details");
    expect(h).toContain("Early-down success");
    expect(h).toContain(cue);
  });
});
