// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getTheme, setTheme } from "./theme";

describe("theme", () => {
  beforeEach(() => { localStorage.clear(); delete document.documentElement.dataset.theme; });
  afterEach(() => vi.restoreAllMocks());

  it("defaults to light", () => expect(getTheme()).toBe("light"));

  it("remembers dark", () => {
    setTheme("dark");
    expect(getTheme()).toBe("dark");
    expect(localStorage.getItem("cfbm:theme")).toBe("dark");
  });

  it("sets the html data attribute", () => {
    setTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    setTheme("light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("survives storage that throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(getTheme()).toBe("light");
    expect(() => setTheme("dark")).not.toThrow();
  });

  it("ignores junk values", () => {
    localStorage.setItem("cfbm:theme", "purple");
    expect(getTheme()).toBe("light");
  });
});
