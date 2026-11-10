// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { differs, loadOut, saveOut } from "./choices";

const KEY = "cfbm:whatif:2026:7";
const listed = new Set([10, 11, 20, 21]);
afterEach(() => { localStorage.clear(); vi.restoreAllMocks(); });

describe("saved what-if choices", () => {
  it("round trip: only differences are stored, and they come back", () => {
    const defaults = new Set([20]);
    saveOut(2026, 7, new Set([10]), defaults);
    expect(JSON.parse(localStorage.getItem(KEY)!)).toEqual({ in: [20], out: [10] });
    expect([...loadOut(2026, 7, defaults, listed)].sort()).toEqual([10]);
  });
  it("nothing stored → defaults", () => {
    expect([...loadOut(2026, 7, new Set([20]), listed)]).toEqual([20]);
  });
  it("junk JSON → defaults", () => {
    localStorage.setItem(KEY, "{not json");
    expect([...loadOut(2026, 7, new Set([20]), listed)]).toEqual([20]);
    localStorage.setItem(KEY, JSON.stringify({ in: "x", out: [10, "y"] }));
    expect([...loadOut(2026, 7, new Set([20]), listed)].sort()).toEqual([10, 20]);
  });
  it("ids no longer listed are ignored", () => {
    localStorage.setItem(KEY, JSON.stringify({ in: [], out: [999] }));
    expect([...loadOut(2026, 7, new Set(), listed)]).toEqual([]);
  });
  it("storage that throws → defaults, and saving does not crash", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect([...loadOut(2026, 7, new Set([20]), listed)]).toEqual([20]);
    expect(() => saveOut(2026, 7, new Set([10]), new Set())).not.toThrow();
  });
  it("saving the defaults (reset) removes the key", () => {
    localStorage.setItem(KEY, JSON.stringify({ in: [], out: [10] }));
    saveOut(2026, 7, new Set([20]), new Set([20]));
    expect(localStorage.getItem(KEY)).toBeNull();
  });
  it("differs", () => {
    expect(differs(new Set([1]), new Set([1]))).toBe(false);
    expect(differs(new Set([1, 2]), new Set([1]))).toBe(true);
    expect(differs(new Set(), new Set([1]))).toBe(true);
  });
});
