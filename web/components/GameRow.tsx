"use client";

import Link from "next/link";
import type { GameSummary } from "@/lib/types";

interface Props {
  game: GameSummary;
  favorites: string[];
  onToggle: (team: string) => void;
}

function kickoff(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function Star({ team, favorites, onToggle }: { team: string; favorites: string[]; onToggle: (t: string) => void }) {
  const on = favorites.includes(team);
  return (
    <button
      className="star"
      aria-label={on ? `Remove ${team} from My Teams` : `Add ${team} to My Teams`}
      aria-pressed={on}
      onClick={() => onToggle(team)}
    >
      {on ? "★" : "☆"}
    </button>
  );
}

export default function GameRow({ game: g, favorites, onToggle }: Props) {
  const joiner = g.neutral ? "vs" : "@";
  const score = g.completed && g.awayPoints !== null && g.homePoints !== null
    ? `Final: ${g.away} ${g.awayPoints}, ${g.home} ${g.homePoints}`
    : kickoff(g.start);
  return (
    <div className="game-row">
      <div>
        <div className="teams">
          <Star team={g.away} favorites={favorites} onToggle={onToggle} />
          {g.away} {joiner} {g.home}
          <Star team={g.home} favorites={favorites} onToggle={onToggle} />
        </div>
        <div className="meta">
          {score}
          {g.neutral ? " · Neutral site" : ""}
          {g.venue ? ` · ${g.venue}` : ""}
        </div>
      </div>
      <div className="go">
        {g.hasBreakdown ? (
          <Link href={`/game?season=${g.season}&id=${g.id}`}>Breakdown →</Link>
        ) : (
          <span className="muted">No breakdown (FCS opponent)</span>
        )}
      </div>
    </div>
  );
}
