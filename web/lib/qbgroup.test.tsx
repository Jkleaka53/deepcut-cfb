import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import QbTiers from "@/components/matchup/QbTiers";
import type { QbVs, Section, SplitTable } from "./types";

const t = (title: string, subject: string): SplitTable => ({ title, subject, tierSkill: "pass_defense", seasons: [2026],
  highlightTier: 1, metricLabels: {}, metricFormats: {}, rows: [] });
const qbVs: QbVs = { name: "Austin Simmons", opponent: "Georgia", oppRank: 28, of: 138, games: [
  { gameId: 1, season: 2026, opponent: "Texas", oppRank: 23, stage: null, result: "L", pf: 20, pa: 34, epaPerDb: 0.1, dropbacks: 44 }] };
const sec: Section = { offenseTeam: "Missouri", defenseTeam: "Georgia", units: [], qbVs,
  splits: [t("Austin Simmons vs. pass defenses by strength", "Austin Simmons"), t("Missouri pass protection", "Missouri"),
    t("Georgia pass defense", "Georgia"), t("Georgia pass rush", "Georgia")] };
const html = (s: Section) => renderToString(<QbTiers section={s} qb="Austin Simmons" teams={{}} />).replace(/<!-- -->/g, "");

describe("QB split group", () => {
  it("is one collapsed block per team with an obvious expand control", () => {
    const h = html(sec);
    expect(h).toMatch(/<details class="qb-group"(?![^>]*open)/);
    expect(h).toContain("Missouri passing game");
    expect(h).toContain("QB Austin Simmons");
    expect(h).toContain("0-1 vs. pass D as good as Georgia&#x27;s");
    expect(h).toContain("Show all 4 splits");
  });
  it("holds the QB card and all three unit tables inside", () => {
    const h = html(sec);
    const inside = h.slice(h.indexOf("</summary>"));
    for (const s of ["Austin Simmons vs. pass defenses", "Missouri pass protection", "Georgia pass defense", "Georgia pass rush"])
      expect(inside).toContain(s);
  });
  it("no QB: still a block, without a record line", () => {
    const h = html({ ...sec, qbVs: null, splits: sec.splits.slice(1) });
    expect(h).toContain("Show all 3 splits");
    expect(h).not.toContain("vs. pass D as good as");
  });
});
