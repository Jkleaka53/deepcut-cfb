// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getFavorites, isFavorite, toggleFavorite } from "./favorites";

describe("favorites", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.restoreAllMocks());

  it("starts empty", () => expect(getFavorites()).toEqual([]));

  it("toggle adds then removes", () => {
    expect(toggleFavorite("West Virginia")).toEqual(["West Virginia"]);
    expect(isFavorite("West Virginia")).toBe(true);
    expect(toggleFavorite("West Virginia")).toEqual([]);
    expect(isFavorite("West Virginia")).toBe(false);
  });

  it("persists under cfbm:favorites", () => {
    toggleFavorite("Hawai'i");
    expect(JSON.parse(localStorage.getItem("cfbm:favorites")!)).toEqual(["Hawai'i"]);
  });

  it("survives blocked storage", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(getFavorites()).toEqual([]);
    expect(() => toggleFavorite("Ohio State")).not.toThrow();
    expect(isFavorite("Ohio State")).toBe(false);
  });

  it("ignores corrupt stored data", () => {
    localStorage.setItem("cfbm:favorites", "{not json");
    expect(getFavorites()).toEqual([]);
  });
});
