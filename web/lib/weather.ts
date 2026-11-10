import type { Weather, WeatherIcon } from "./types";

export function weatherMini(w: Weather | null | undefined): string | null {
  if (!w) return null;
  if (w.status === "indoors") return "Indoors";
  if (w.status === "far" || w.tempF === null || w.tempF === undefined) return null;
  const parts = [`${w.tempF}°`];
  if ((w.precipPct ?? 0) >= 30) parts.push(`${w.precipPct}%`);
  if ((w.windMph ?? 0) >= 15) parts.push(`${w.windMph} mph`);
  return parts.join(" · ");
}

export function weatherStrip(w: Weather | null | undefined): { icon: WeatherIcon | null; parts: string[]; asOf: string | null } | null {
  if (!w) return null;
  if (w.status === "indoors") return { icon: null, parts: ["Indoors"], asOf: null };
  if (w.status === "far") return { icon: null, parts: ["Forecast closer to kickoff"], asOf: null };
  const parts: string[] = [];
  if (w.tempF !== null && w.tempF !== undefined) parts.push(`${w.tempF}°F${w.label && w.label !== "—" ? ` ${w.label}` : ""}`);
  if (w.precipPct !== null && w.precipPct !== undefined) parts.push(`${w.precipPct}% rain`);
  if (w.windMph !== null && w.windMph !== undefined) parts.push(`${w.windMph} mph wind`);
  if (w.status === "tba") parts.push("Time TBA");
  let asOf: string | null = null;
  if (w.asOf) {
    const d = new Date(w.asOf);
    if (!Number.isNaN(d.getTime())) asOf = `Forecast as of ${d.toLocaleString(undefined, { weekday: "short", hour: "numeric" })}`;
  }
  return { icon: w.icon ?? null, parts, asOf };
}
