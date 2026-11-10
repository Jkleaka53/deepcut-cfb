import type { GameSummary, Index, Matchup, PlayerEntry } from "./types";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export const loadIndex = () => getJson<Index>("/data/index.json");
export const loadGames = (season: number) => getJson<GameSummary[]>(`/data/${season}/games.json`);
export const loadMatchup = (season: number, id: number) =>
  getJson<Matchup>(`/data/${season}/matchups/${id}.json`);
export const loadPlayers = () => getJson<PlayerEntry[]>("/data/players.json");
