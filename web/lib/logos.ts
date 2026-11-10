import type { Theme } from "./theme";
import type { TeamInfo } from "./types";

/** Site path of a team logo downloaded at build time (scripts/fetch-logos.mjs). */
export function logoPath(team: TeamInfo | undefined, theme: Theme): string | null {
  if (!team || team.id === null || team.id === undefined) return null;
  if (theme === "dark" && team.logoDark) return `/logos/dark/${team.id}.png`;
  return team.logo ? `/logos/${team.id}.png` : null;
}
