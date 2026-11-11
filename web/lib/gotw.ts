import { type Filter, passes } from "./filters";
import type { GameSummary } from "./types";

export type GotwPicks = Record<string, { id: number; why: string }>;

/** The week's pick (Game of the Week, Shootout of the Week), if there is one and it fits the active filter. */
export function pickFor(picks: GotwPicks, week: string, games: GameSummary[], filter: Filter, favorites: string[]):
  { game: GameSummary; why: string } | null {
  const p = picks[week];
  if (!p) return null;
  const game = games.find((x) => x.id === p.id);
  if (!game || !passes(game, filter, favorites)) return null;
  return { game, why: p.why };
}

export const gotwFor = pickFor;
