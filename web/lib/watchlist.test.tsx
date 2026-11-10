// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { getWatch, toggleWatch } from "./watchlist";
import { FILTERS, passes } from "./filters";
import ScoreRow from "@/components/ScoreRow";
import BackButton from "@/components/BackButton";
import type { GameSummary } from "./types";

const back = vi.fn(), push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ back, push }) }));

const game = { id: 7, season: 2026, week: 11, seasonType: "regular", start: "2026-11-14T20:00:00.000Z", startTimeTBD: false,
  home: "Georgia", away: "Texas", homeRank: null, awayRank: null, homePoints: null, awayPoints: null, completed: false,
  neutral: false, hasBreakdown: true, homeConf: "SEC", awayConf: "SEC" } as unknown as GameSummary;

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
function mount(el: React.ReactElement) {
  const box = document.createElement("div");
  document.body.appendChild(box);
  act(() => createRoot(box).render(el));
  return box;
}
const button = (box: HTMLElement, name: string) => box.querySelector<HTMLButtonElement>(`button[aria-label="${name}"]`)!;
const click = (b: HTMLElement) => act(() => { b.click(); });

describe("watch list", () => {
  beforeEach(() => { localStorage.clear(); back.mockReset(); push.mockReset(); });
  afterEach(() => vi.restoreAllMocks());

  it("toggles and persists game ids", () => {
    expect(toggleWatch(7)).toEqual([7]);
    expect(JSON.parse(localStorage.getItem("cfbm:watch")!)).toEqual([7]);
    expect(getWatch()).toEqual([7]);
    expect(toggleWatch(7)).toEqual([]);
  });

  it("survives blocked storage", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(getWatch()).toEqual([]);
    expect(() => toggleWatch(1)).not.toThrow();
  });

  it("Watch filter shows only watched games and sits after My Teams", () => {
    const labels = FILTERS.map((f) => f.label);
    expect(labels.indexOf("Watch")).toBe(labels.indexOf("My Teams") + 1);
    expect(passes(game, "watch", [], [7])).toBe(true);
    expect(passes(game, "watch", [], [8])).toBe(false);
  });

  it("score row bell toggles without opening the game", () => {
    const onWatch = vi.fn();
    const box = mount(<ScoreRow game={game} teams={{}} favorites={[]} onToggle={() => {}} watched={false} onWatch={onWatch} />);
    const bell = button(box, "Add Texas at Georgia to Watch");
    expect(bell.getAttribute("aria-pressed")).toBe("false");
    click(bell);
    expect(onWatch).toHaveBeenCalledWith(7);
  });

  it("back button goes back in history, or home when opened directly", () => {
    Object.defineProperty(window.history, "length", { value: 3, configurable: true });
    const box = mount(<BackButton />);
    click(button(box, "Back"));
    expect(back).toHaveBeenCalled();
    Object.defineProperty(window.history, "length", { value: 1, configurable: true });
    click(button(box, "Back"));
    expect(push).toHaveBeenCalledWith("/");
  });
});

describe("home view memory", () => {
  beforeEach(() => sessionStorage.clear());
  it("remembers week and filter for this tab so Back returns to them", async () => {
    const { loadView, saveView } = await import("./filters");
    expect(loadView()).toBeNull();
    saveView({ season: 2025, week: "9", filter: "watch" });
    expect(loadView()).toEqual({ season: 2025, week: "9", filter: "watch" });
    sessionStorage.setItem("cfbm:view", "{bad");
    expect(loadView()).toBeNull();
  });
});
