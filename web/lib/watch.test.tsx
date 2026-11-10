// @vitest-environment jsdom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import AvailabilityWatch from "@/components/matchup/AvailabilityWatch";
import WhatIfBanner from "@/components/matchup/WhatIfBanner";
import { whatIfText } from "./whatif";
import type { Matchup, TeamAvailability } from "./types";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const data = (): TeamAvailability => ({
  flags: [{ kind: "ok", text: "Tommy Carr started last game." }],
  report: { conference: "SEC", url: "https://www.secsports.com/fbreports", when: "Posts Wednesday.", publishes: true },
  players: [
    { athleteId: 10, name: "Tommy Carr", role: "QB", share: null, shareOf: null, noStatsLastGame: false },
    { athleteId: 11, name: "Back Up", role: "QB2", share: null, shareOf: null, noStatsLastGame: false },
    { athleteId: 20, name: "Wr One", role: "WR", share: 0.312, shareOf: "receiving yards", noStatsLastGame: true },
    { athleteId: 30, name: "Rb One", role: "RB", share: 0.44, shareOf: "rushing yards", noStatsLastGame: false }],
  backup: { athleteId: 11, name: "Back Up", games: 2, smallSample: true, cells: {},
    qbVs: { name: "Back Up", opponent: "Oregon", oppRank: 2, of: 136, games: [] } },
});
const html = (el: React.ReactElement) => renderToString(el).replace(/<!-- -->/g, "");

describe("AvailabilityWatch", () => {
  it("lists roles, shares and the no-stats tag, with the research line and link", () => {
    const h = html(<AvailabilityWatch team="Michigan" data={data()} completed={false} out={new Set([20])} onToggle={() => {}} />);
    expect(h).toContain("Check the official report, then set players In or Out.");
    expect(h).toContain('href="https://www.secsports.com/fbreports"');
    expect(h).toContain("Starting QB");
    expect(h).toContain("Backup QB · takes over if Tommy Carr is Out");
    expect(h).toContain("Small sample");
    expect(h).toContain("31% of receiving yards");
    expect(h).toContain("44% of rushing yards");
    expect(h).toContain("No stats last game");
    expect((h.match(/aria-pressed="true"/g) ?? []).length).toBe(3); // QB In, WR Out, RB In; no switch on QB2
  });
  it("clicking Out calls back with the player", () => {
    const onToggle = vi.fn();
    const el = document.createElement("div");
    act(() => createRoot(el).render(<AvailabilityWatch team="Michigan" data={data()} completed={false} out={new Set()} onToggle={onToggle} />));
    const out = [...el.querySelectorAll("button")].find((b) => b.textContent === "Out" && b.closest("[data-player='10']"))!;
    act(() => out.click());
    expect(onToggle).toHaveBeenCalledWith(10, true);
  });
  it("no backup: starter switch disabled, with the reason", () => {
    const d = { ...data(), backup: null, players: data().players!.filter((p) => p.role !== "QB2") };
    const h = html(<AvailabilityWatch team="Michigan" data={d} completed={false} out={new Set()} onToggle={() => {}} />);
    expect(h).toContain("No other QB has thrown a pass this season");
    expect(h).toMatch(/data-player="10"[\s\S]*?<button[^>]*disabled/);
  });
  it("completed game or old data → the plain availability card, no switches", () => {
    for (const [d, completed] of [[data(), true], [{ flags: data().flags, report: data().report }, false]] as const) {
      const h = html(<AvailabilityWatch team="Michigan" data={d} completed={completed} out={new Set()} onToggle={() => {}} />);
      expect(h).toContain("Tommy Carr started last game.");
      expect(h).not.toContain("aria-pressed");
    }
  });
});

describe("what-if banner", () => {
  const m = { availability: { Michigan: data() } } as unknown as Matchup;
  it("names who changed from the defaults", () => {
    expect(whatIfText(m, new Set([10, 20]), new Set([20]))).toBe("What-if: Tommy Carr set Out");
    expect(whatIfText(m, new Set([10]), new Set([20]))).toBe("What-if: Tommy Carr set Out, Wr One set In");
  });
  it("a starter Out by default still shows, so the backup's numbers are never silent", () => {
    expect(whatIfText(m, new Set([10]), new Set([10]))).toBe("What-if: Tommy Carr Out (no stats last game)");
    expect(whatIfText(m, new Set([20]), new Set([20]))).toBeNull();
  });
  it("renders the text and a reset button only when choices differ", () => {
    expect(html(<WhatIfBanner text="What-if: Tommy Carr set Out" canReset onReset={() => {}} />)).toContain("Reset to defaults");
    expect(html(<WhatIfBanner text="What-if: Tommy Carr Out (no stats last game)" canReset={false} onReset={() => {}} />)).not.toContain("Reset");
  });
});
