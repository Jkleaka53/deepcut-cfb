import type { GameSummary } from "./types";

export type Filter = "all" | "top25" | "mine" | "SEC" | "Big Ten" | "Big 12" | "ACC" | "g5" | "ind";
export const P4 = ["SEC", "Big Ten", "Big 12", "ACC"];
export const IND = "FBS Independents";
export const POST = "post";

export const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" }, { value: "top25", label: "Top 25" }, { value: "mine", label: "My Teams" },
  { value: "SEC", label: "SEC" }, { value: "Big Ten", label: "Big Ten" }, { value: "Big 12", label: "Big 12" },
  { value: "ACC", label: "ACC" }, { value: "g5", label: "Group of 5" }, { value: "ind", label: "Independents" },
];

const confs = (g: GameSummary) => [g.homeConf, g.awayConf];

export function passes(g: GameSummary, f: Filter, favorites: string[]): boolean {
  switch (f) {
    case "all": return true;
    case "top25": return (g.homeRank ?? null) !== null || (g.awayRank ?? null) !== null;
    case "mine": return favorites.includes(g.home) || favorites.includes(g.away);
    case "g5": return confs(g).some((c) => !!c && !P4.includes(c) && c !== IND);
    case "ind": return confs(g).includes(IND);
    default: return confs(g).includes(f);
  }
}

export function weekValue(g: GameSummary): string {
  return g.seasonType === "postseason" ? POST : String(g.week);
}

const byKickoff = (a: GameSummary, b: GameSummary) => a.start.localeCompare(b.start) || a.id - b.id;

export function groupByDay(games: GameSummary[]): { day: string; games: GameSummary[] }[] {
  const out: { day: string; games: GameSummary[] }[] = [];
  for (const g of [...games].sort(byKickoff)) {
    const d = new Date(g.start);
    // A TBA kickoff's clock time is a placeholder (05:00Z); its UTC date is the real game day.
    const day = Number.isNaN(d.getTime()) ? "Date TBA"
      : d.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric", ...(g.startTimeTBD ? { timeZone: "UTC" } : {}) });
    const last = out[out.length - 1];
    if (last && last.day === day) last.games.push(g);
    else out.push({ day, games: [g] });
  }
  return out;
}

export function weekChips(games: GameSummary[]): { value: string; label: string }[] {
  const regular = [...new Set(games.filter((g) => g.seasonType === "regular").map((g) => g.week))].sort((a, b) => a - b);
  const chips = regular.map((w) => ({ value: String(w), label: `Wk ${w}` }));
  if (games.some((g) => g.seasonType === "postseason")) chips.push({ value: POST, label: "Bowls" });
  return chips;
}
