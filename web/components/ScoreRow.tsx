"use client";

import Link from "next/link";
import { Star } from "lucide-react";
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

export default function ScoreRow({ game: g, teams, favorites, onToggle }: Props) {
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
        <span className="sr-time">{final ? "Final" : localKickoff(g.start, g.startTimeTBD)}</span>
        {!final && mini && (
          <span className="sr-wx"><WeatherIcon kind={g.weather?.icon} indoors={g.weather?.status === "indoors"} />{mini}</span>
        )}
        {g.neutral && <span className="sr-note">Neutral site</span>}
        {!g.hasBreakdown && <span className="sr-note">FCS opponent</span>}
        {g.gap && <span className="badge-accent">Gap: {g.gap.label}</span>}
      </div>
    </>
  );
  return g.hasBreakdown
    ? <Link href={`/game?season=${g.season}&id=${g.id}`} className="scorerow">{body}</Link>
    : <div className="scorerow">{body}</div>;
}
