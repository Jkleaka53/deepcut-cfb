"use client";
import { chipText, edgeChipText } from "@/lib/swing";

import Link from "next/link";
import { Bell, Star } from "lucide-react";
import TeamLogo from "./TeamLogo";
import WeatherIcon from "./WeatherIcon";
import { localKickoff } from "@/lib/format";
import { weatherMini } from "@/lib/weather";
import type { GameSummary, TeamInfo } from "@/lib/types";

interface Props {
  game: GameSummary;
  teams: Record<string, TeamInfo>;
  favorites: string[];
  onToggle: (team: string) => void;
  watched?: boolean;
  onWatch?: (id: number) => void;
}

function Line({ name, rank, points, won, team, fav, onToggle }:
  { name: string; rank: number | null | undefined; points: number | null; won: boolean; team?: TeamInfo; fav: boolean; onToggle: () => void }) {
  return (
    <div className={`sr-line ${won ? "won" : ""}`}>
      <TeamLogo team={team} name={name} size={24} />
      {rank ? <span className="sr-rank num">{rank}</span> : null}
      <span className="sr-name">{name}</span>
      <button className={`sr-star ${fav ? "on" : ""}`} aria-pressed={fav}
        aria-label={fav ? `Remove ${name} from My Teams` : `Add ${name} to My Teams`}
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onToggle(); }}>
        <Star className="icon sm" aria-hidden fill={fav ? "currentColor" : "none"} />
      </button>
      {points !== null && <span className="sr-pts num">{points}</span>}
    </div>
  );
}

export default function ScoreRow({ game: g, teams, favorites, onToggle, watched = false, onWatch }: Props) {
  const final = g.completed && g.awayPoints !== null && g.homePoints !== null;
  const mini = weatherMini(g.weather);
  const body = (
    <>
      <div className="sr-teams">
        <Line name={g.away} rank={g.awayRank} points={final ? g.awayPoints : null} won={final && g.awayPoints! > g.homePoints!}
          team={teams[g.away]} fav={favorites.includes(g.away)} onToggle={() => onToggle(g.away)} />
        <Line name={g.home} rank={g.homeRank} points={final ? g.homePoints : null} won={final && g.homePoints! > g.awayPoints!}
          team={teams[g.home]} fav={favorites.includes(g.home)} onToggle={() => onToggle(g.home)} />
      </div>
      <div className="sr-side">
        <span className="sr-timerow">
          <span className="sr-time">{final ? "Final" : localKickoff(g.start, g.startTimeTBD)}</span>
          {onWatch && (
            <button className={`sr-watch ${watched ? "on" : ""}`} aria-pressed={watched}
              aria-label={watched ? `Remove ${g.away} at ${g.home} from Watch` : `Add ${g.away} at ${g.home} to Watch`}
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); onWatch(g.id); }}>
              <Bell className="icon sm" aria-hidden fill={watched ? "currentColor" : "none"} />
            </button>
          )}
        </span>
        {!final && mini && (
          <span className="sr-wx"><WeatherIcon kind={g.weather?.icon} indoors={g.weather?.status === "indoors"} />{mini}</span>
        )}
        {g.neutral && <span className="sr-note">Neutral site</span>}
        {!g.hasBreakdown && <span className="sr-note">FCS opponent</span>}
        {(() => {
          const fav = g.keyFactor?.favors ?? g.gap?.favors;
          const text = fav ? chipText(g, teams[fav]?.abbr ?? fav) : null;
          return text && <span className="badge-accent">{text}</span>;
        })()}
        {(() => {
          const t = g.edge?.team;
          const text = t ? edgeChipText(g.edge, teams[t]?.abbr ?? t) : null;
          return text && <span className="badge-plain">{text}</span>;
        })()}
        {g.shootoutWatch && <span className="badge-plain">Shootout watch</span>}
      </div>
    </>
  );
  return g.hasBreakdown
    ? <Link href={`/game?season=${g.season}&id=${g.id}`} className="scorerow">{body}</Link>
    : <div className="scorerow">{body}</div>;
}
