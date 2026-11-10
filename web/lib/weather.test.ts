import { describe, expect, it } from "vitest";
import { weatherMini, weatherStrip } from "./weather";

describe("weatherMini", () => {
  it("temp only when calm and dry", () =>
    expect(weatherMini({ status: "forecast", tempF: 44, precipPct: 5, windMph: 4, icon: "cloudy" })).toBe("44°"));
  it("adds rain at 30%+", () =>
    expect(weatherMini({ status: "forecast", tempF: 58, precipPct: 70, windMph: 5, icon: "rain" })).toBe("58° · 70%"));
  it("adds wind at 15+ mph", () =>
    expect(weatherMini({ status: "forecast", tempF: 47, precipPct: 0, windMph: 18, icon: "clear" })).toBe("47° · 18 mph"));
  it("indoors", () => expect(weatherMini({ status: "indoors" })).toBe("Indoors"));
  it("far or missing is null", () => {
    expect(weatherMini({ status: "far" })).toBeNull();
    expect(weatherMini(null)).toBeNull();
    expect(weatherMini(undefined)).toBeNull();
  });
});

describe("weatherStrip", () => {
  it("forecast parts", () => {
    const s = weatherStrip({ status: "forecast", label: "Cloudy", icon: "cloudy", tempF: 53, precipPct: 24, windMph: 7, gustMph: 15, asOf: "2026-11-13T22:00:00+00:00" })!;
    expect(s.icon).toBe("cloudy");
    expect(s.parts).toEqual(["53°F Cloudy", "24% rain", "7 mph wind"]);
    expect(s.asOf).toMatch(/^Forecast as of /);
  });
  it("far", () => expect(weatherStrip({ status: "far" })!.parts).toEqual(["Forecast closer to kickoff"]));
  it("indoors", () => expect(weatherStrip({ status: "indoors" })!.parts).toEqual(["Indoors"]));
  it("tba suffix", () =>
    expect(weatherStrip({ status: "tba", label: "Rain", icon: "rain", tempF: 61, precipPct: 70, windMph: 18 })!.parts.at(-1)).toBe("Time TBA"));
  it("missing", () => expect(weatherStrip(null)).toBeNull());
});
