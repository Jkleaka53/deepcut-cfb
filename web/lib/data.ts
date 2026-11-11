import type { GameSummary, Index, Matchup, PlayerEntry, TeamInfo } from "./types";
import type { GotwPicks } from "./gotw";

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

export async function loadTeams(season: number): Promise<Record<string, TeamInfo>> {
  try {
    const list = await getJson<TeamInfo[]>(`/data/${season}/teams.json`);
    return Object.fromEntries(list.map((t) => [t.school, t]));
  } catch {
    return {};
  }
}

export async function loadGotw(season: number): Promise<GotwPicks> {
  try {
    return await getJson<GotwPicks>(`/data/${season}/gotw.json`);
  } catch {
    return {};
  }
}

export async function loadShootout(season: number): Promise<GotwPicks> {
  try {
    return await getJson<GotwPicks>(`/data/${season}/shootout.json`);
  } catch {
    return {};
  }
}
