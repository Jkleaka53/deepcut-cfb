import { type Filter, passes } from "./filters";
import type { GameSummary } from "./types";

export type GotwPicks = Record<string, { id: number; why: string }>;

/** The week's pick (Game of the Week, Shootout of the Week), if there is one and it fits the active filter. */
export function pickFor<P extends { id: number; why: string }>(picks: Record<string, P>, week: string,
  games: GameSummary[], filter: Filter, favorites: string[]): { game: GameSummary; why: string; pick: P } | null {
  const p = picks[week];
  if (!p) return null;
  const game = games.find((x) => x.id === p.id);
  if (!game || !passes(game, filter, favorites)) return null;
  return { game, why: p.why, pick: p };
}

export const gotwFor = pickFor;

/** The reason for a game that is some week's pick, or null. */
export function pickWhyFor(picks: Record<string, { id: number; why: string }>, id: number): string | null {
  return Object.values(picks).find((p) => p.id === id)?.why ?? null;
}
