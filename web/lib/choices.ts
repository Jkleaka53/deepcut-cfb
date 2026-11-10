/** What-if choices, saved per game on this device. Only differences from the defaults are stored. */

const key = (season: number, id: number) => `cfbm:whatif:${season}:${id}`;
const ids = (v: unknown): number[] => (Array.isArray(v) ? v.filter((x): x is number => typeof x === "number") : []);

export function loadOut(season: number, id: number, defaults: Set<number>, listed: Set<number>): Set<number> {
  const out = new Set(defaults);
  try {
    const raw = localStorage.getItem(key(season, id));
    if (!raw) return out;
    const saved = JSON.parse(raw) as { in?: unknown; out?: unknown };
    for (const x of ids(saved?.in)) out.delete(x);
    for (const x of ids(saved?.out)) if (listed.has(x)) out.add(x);
  } catch {
    return new Set(defaults);
  }
  return out;
}

export function saveOut(season: number, id: number, out: Set<number>, defaults: Set<number>): void {
  try {
    if (!differs(out, defaults)) {
      localStorage.removeItem(key(season, id));
      return;
    }
    const inIds = [...defaults].filter((x) => !out.has(x));
    const outIds = [...out].filter((x) => !defaults.has(x));
    localStorage.setItem(key(season, id), JSON.stringify({ in: inIds, out: outIds }));
  } catch {
    // Storage blocked: the switches still work for this page view.
  }
}

export function differs(a: Set<number>, b: Set<number>): boolean {
  return a.size !== b.size || [...a].some((x) => !b.has(x));
}
