import type { GameSummary, PlayerEntry } from "./types";

export function normalize(s: string): string {
  return s
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .replace(/['’ʻ`]/g, "")
    .replace(/&/g, "and")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

export function matchGame(g: GameSummary, q: string, players: PlayerEntry[]): boolean {
  const query = normalize(q);
  if (!query) return true;
  const fields = [g.home, g.away, g.homeConf ?? "", g.awayConf ?? ""];
  if (fields.some((f) => normalize(f).includes(query))) return true;
  return players.some(
    (p) =>
      p.season === g.season &&
      (p.team === g.home || p.team === g.away) &&
      normalize(p.name).includes(query),
  );
}
