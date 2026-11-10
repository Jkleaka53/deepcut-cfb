const KEY = "cfbm:favorites";

export function getFavorites(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((t): t is string => typeof t === "string") : [];
  } catch {
    return [];
  }
}

export function isFavorite(team: string): boolean {
  return getFavorites().includes(team);
}

export function toggleFavorite(team: string): string[] {
  const current = getFavorites();
  const next = current.includes(team) ? current.filter((t) => t !== team) : [...current, team];
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Storage blocked: favorites just won't persist.
  }
  return next;
}
