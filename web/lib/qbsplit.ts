import { ordinal } from "./format";
import type { QbGame, QbVs } from "./types";

const SUFFIX = new Set(["jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"]);

export function lastName(name: string): string {
  const parts = name.trim().split(/\s+/);
  while (parts.length > 1 && SUFFIX.has(parts[parts.length - 1].toLowerCase())) parts.pop();
  return parts[parts.length - 1];
}

export function rowLabel(g: QbGame): string {
  return `'${String(g.season).slice(-2)}${g.stage ? ` ${g.stage}` : ""}`;
}

export interface Bucket { w: number; l: number; games: number; epa: number | null }

function bucket(games: QbGame[]): Bucket {
  let w = 0, l = 0, num = 0, den = 0;
  for (const g of games) {
    if (g.result === "W") w++;
    if (g.result === "L") l++;
    if (g.epaPerDb !== null && g.dropbacks > 0) { num += g.epaPerDb * g.dropbacks; den += g.dropbacks; }
  }
  return { w, l, games: games.length, epa: den > 0 ? num / den : null };
}

/** "As good or better" includes the line rank itself. */
export function splitAt(games: QbGame[], cut: number): { above: Bucket; below: Bucket } {
  return { above: bucket(games.filter((g) => g.oppRank <= cut)), below: bucket(games.filter((g) => g.oppRank > cut)) };
}

export function visibleRows(games: QbGame[], cut: number, extra = 2): { above: QbGame[]; below: QbGame[]; hidden: QbGame[] } {
  const above = games.filter((g) => g.oppRank <= cut);
  const rest = games.filter((g) => g.oppRank > cut);
  return { above, below: rest.slice(0, extra), hidden: rest.slice(extra) };
}

export function summary(q: QbVs): string {
  if (q.oppRank === null) return "";
  const who = lastName(q.name);
  const above = q.games.filter((g) => g.oppRank <= q.oppRank!);
  if (above.length === 0) return `${who} hasn't faced a pass defense as good as ${q.opponent}'s yet.`;
  if (above.length === 1) {
    const g = above[0];
    const what = g.result === "W" ? `a ${g.pf}-${g.pa} win over` : g.result === "L" ? `a ${g.pf}-${g.pa} loss to` : "a game against";
    return `${who} has faced one pass defense as good as ${q.opponent}'s: ${what} ${g.opponent} (${ordinal(g.oppRank)}).`;
  }
  const b = splitAt(q.games, q.oppRank).above;
  let s = `Against pass defenses as good as ${q.opponent}'s or better, ${who} is ${b.w}-${b.l}.`;
  const losses = above.filter((g) => g.result === "L");
  if (losses.length >= 2) {
    const worst = Math.max(...losses.map((g) => g.oppRank));
    s += ` All ${losses.length} losses came against pass defenses ranked ${ordinal(worst)} or better.`;
  }
  return s;
}
