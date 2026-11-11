import Link from "next/link";
import { Clock } from "lucide-react";
import TeamLogo from "./TeamLogo";
import { localKickoff } from "@/lib/format";
import type { GameSummary, TeamInfo } from "@/lib/types";

/** A smaller featured card that sits under Game of the Week (Shootout of the Week, later Upset Watch). */
export default function PickCard({ tag, game: g, why, teams }:
  { tag: string; game: GameSummary; why: string; teams: Record<string, TeamInfo> }) {
  const final = g.completed && g.awayPoints !== null && g.homePoints !== null;
  const body = (
    <>
      <div className="pick-tag">{tag}</div>
      <div className="pick-teams">
        <span className="pick-team"><TeamLogo team={teams[g.away]} name={g.away} size={24} />
          {g.awayRank ? <span className="sr-rank num">{g.awayRank}</span> : null}<span className="pick-name">{g.away}</span></span>
        <span className="pick-at">{final ? `${g.awayPoints} – ${g.homePoints}` : g.neutral ? "vs" : "at"}</span>
        <span className="pick-team"><TeamLogo team={teams[g.home]} name={g.home} size={24} />
          {g.homeRank ? <span className="sr-rank num">{g.homeRank}</span> : null}<span className="pick-name">{g.home}</span></span>
      </div>
      <div className="pick-meta"><Clock className="icon sm" aria-hidden />{final ? "Final" : localKickoff(g.start, g.startTimeTBD)}</div>
      <div className="pick-why"><b>Why watch:</b> {why}</div>
    </>
  );
  return g.hasBreakdown
    ? <Link href={`/game?season=${g.season}&id=${g.id}`} className="pick-card">{body}</Link>
    : <div className="pick-card">{body}</div>;
}
