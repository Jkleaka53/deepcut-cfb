import type { Edge, TeamRecord, Tier } from "./types";

export function fmt(v: number | null | undefined, format: "pct" | "epa" | "yds"): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  if (format === "pct") return `${(v * 100).toFixed(1)}%`;
  if (format === "yds") return `${v.toFixed(1)} yds`;
  const s = Math.abs(v).toFixed(2);
  return v < 0 ? `−${s}` : `+${s}`;
}

export function tierLabel(t: Tier): string {
  return t === 1 ? "Top third" : t === 2 ? "Middle third" : "Bottom third";
}

export function ordinal(n: number | null | undefined): string {
  if (n === null || n === undefined) return "";
  const t = n % 100;
  const suf = t >= 11 && t <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[n % 10] ?? "th";
  return `${n}${suf}`;
}

export function verdict(edge: Edge, offense: string, defense: string): { text: string; team: string | null } {
  switch (edge) {
    case "even": return { text: "Even", team: null };
    case "slight-offense": return { text: `${offense} slight edge`, team: offense };
    case "clear-offense": return { text: `${offense} big edge`, team: offense };
    case "slight-defense": return { text: `${defense} slight edge`, team: defense };
    case "clear-defense": return { text: `${defense} big edge`, team: defense };
    default: return { text: "", team: null };
  }
}

/** Offense's share (0-100) of a bar split between the two sides' percentiles. */
export function splitShare(offPct: number | null | undefined, defPct: number | null | undefined): number | null {
  if (offPct === null || offPct === undefined || defPct === null || defPct === undefined) return null;
  const total = offPct + defPct;
  if (total <= 0) return null;
  return Math.round((offPct / total) * 100);
}

export function localKickoff(iso: string, tbd = false): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  if (tbd) return `${d.toLocaleDateString(undefined, { weekday: "short", timeZone: "UTC" })} · TBA`;
  return d.toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" });
}

/** "8-2 · 5-1 SEC"; overall only for independents. */
export function recordText(r: TeamRecord | undefined | null): string | null {
  if (!r) return null;
  const overall = `${r.wins}-${r.losses}`;
  return r.conference ? `${overall} · ${r.confWins}-${r.confLosses} ${r.conference}` : overall;
}
