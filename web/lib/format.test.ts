import { describe, expect, it } from "vitest";
import { edgeText, fmt, rankText, tierLabel } from "./format";

describe("fmt", () => {
  it("formats pct with one decimal", () => expect(fmt(0.081, "pct")).toBe("8.1%"));
  it("formats positive epa with plus", () => expect(fmt(0.14, "epa")).toBe("+0.14"));
  it("formats negative epa with a real minus sign", () => expect(fmt(-0.08, "epa")).toBe("−0.08"));
  it("formats null as a dash", () => expect(fmt(null, "pct")).toBe("–"));
});

describe("rankText", () => {
  it("prefixes #", () => expect(rankText(98)).toBe("#98"));
  it("null is empty", () => expect(rankText(null)).toBe(""));
});

describe("edgeText", () => {
  it("even", () => expect(edgeText("even", "WVU", "Tech")).toBe("Even"));
  it("slight offense", () => expect(edgeText("slight-offense", "WVU", "Tech")).toBe("Slight edge: WVU"));
  it("clear defense", () => expect(edgeText("clear-defense", "WVU", "Tech")).toBe("Clear edge: Tech"));
  it("null", () => expect(edgeText(null, "WVU", "Tech")).toBe("–"));
});

describe("tierLabel", () => {
  it("labels thirds", () => {
    expect(tierLabel(1)).toBe("Top third");
    expect(tierLabel(2)).toBe("Middle third");
    expect(tierLabel(3)).toBe("Bottom third");
  });
});
