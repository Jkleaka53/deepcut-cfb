import type { Edge, Tier } from "./types";

export function fmt(v: number | null | undefined, format: "pct" | "epa"): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  if (format === "pct") return `${(v * 100).toFixed(1)}%`;
  const s = Math.abs(v).toFixed(2);
  return v < 0 ? `−${s}` : `+${s}`;
}

export function rankText(rank: number | null): string {
  return rank === null ? "" : `#${rank}`;
}

export function edgeText(edge: Edge, offenseTeam: string, defenseTeam: string): string {
  switch (edge) {
    case "even": return "Even";
    case "slight-offense": return `Slight edge: ${offenseTeam}`;
    case "clear-offense": return `Clear edge: ${offenseTeam}`;
    case "slight-defense": return `Slight edge: ${defenseTeam}`;
    case "clear-defense": return `Clear edge: ${defenseTeam}`;
    default: return "–";
  }
}

export function tierLabel(t: Tier): string {
  return t === 1 ? "Top third" : t === 2 ? "Middle third" : "Bottom third";
}
