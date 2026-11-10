// Games picked to watch, kept in this browser only (like My Teams). CFBD game ids are unique across seasons.
const KEY = "cfbm:watch";

export function getWatch(): number[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((n): n is number => typeof n === "number") : [];
  } catch {
    return [];
  }
}

export function toggleWatch(id: number): number[] {
  const current = getWatch();
  const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Storage blocked: the watch list just won't persist.
  }
  return next;
}
