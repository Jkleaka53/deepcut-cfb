import { describe, expect, it } from "vitest";
import { logoPath } from "./logos";
import type { TeamInfo } from "./types";

const T: TeamInfo = { school: "Oregon", id: 2483, abbr: "ORE", conference: "Big Ten", fill: "#007030",
  textLight: "#007030", textDark: "#4fd18a", logo: "https://x/2483.png", logoDark: "https://x/d/2483.png" };

describe("logoPath", () => {
  it("light", () => expect(logoPath(T, "light")).toBe("/logos/2483.png"));
  it("dark", () => expect(logoPath(T, "dark")).toBe("/logos/dark/2483.png"));
  it("missing team", () => expect(logoPath(undefined, "light")).toBeNull());
  it("no dark source falls back to light", () => expect(logoPath({ ...T, logoDark: null }, "dark")).toBe("/logos/2483.png"));
  it("no source at all", () => expect(logoPath({ ...T, logo: null, logoDark: null }, "light")).toBeNull());
  it("no id", () => expect(logoPath({ ...T, id: null }, "light")).toBeNull());
});
