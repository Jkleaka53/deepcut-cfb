import { describe, expect, it } from "vitest";
import { localKickoff, ordinal, splitShare, verdict } from "./format";

describe("ordinal", () => {
  it.each([[130, "130th"], [1, "1st"], [2, "2nd"], [3, "3rd"], [22, "22nd"], [113, "113th"], [11, "11th"], [101, "101st"]])(
    "%i -> %s", (n, s) => expect(ordinal(n)).toBe(s));
  it("null is empty", () => expect(ordinal(null)).toBe(""));
});

describe("verdict", () => {
  it("clear defense = big edge", () =>
    expect(verdict("clear-defense", "Michigan", "Oregon")).toEqual({ text: "Oregon big edge", team: "Oregon" }));
  it("slight offense", () =>
    expect(verdict("slight-offense", "Michigan", "Oregon")).toEqual({ text: "Michigan slight edge", team: "Michigan" }));
  it("even", () => expect(verdict("even", "A", "B")).toEqual({ text: "Even", team: null }));
  it("null", () => expect(verdict(null, "A", "B")).toEqual({ text: "", team: null }));
});

describe("splitShare", () => {
  it("offense share of the bar", () => expect(splitShare(6, 65)).toBe(8));
  it("even split", () => expect(splitShare(50, 50)).toBe(50));
  it("missing side", () => expect(splitShare(null, 40)).toBeNull());
  it("both zero", () => expect(splitShare(0, 0)).toBeNull());
});

describe("localKickoff", () => {
  it("TBA", () => expect(localKickoff("2026-11-14T05:00:00.000Z", true)).toMatch(/TBA/));
  it("bad date", () => expect(localKickoff("nope")).toBe(""));
  it("formats in the viewer's zone", () => {
    const iso = "2026-11-14T20:30:00.000Z";
    const want = new Date(iso).toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" });
    expect(localKickoff(iso)).toBe(want);
  });
});
