import Link from "next/link";
import { Clock } from "lucide-react";
import TeamLogo from "./TeamLogo";
import { localKickoff } from "@/lib/format";
import type { GameSummary, TeamInfo } from "@/lib/types";

const INK = "#0b1220";

/** A slim featured card under Game of the Week, in the same team-color split. The reason lives on the game page. */
export default function PickCard({ tag, game: g, teams, children }:
  { tag: string; game: GameSummary; teams: Record<string, TeamInfo>; children?: React.ReactNode }) {
  const away = teams[g.away], home = teams[g.home];
  const final = g.completed && g.awayPoints !== null && g.homePoints !== null;
  const body = (
    <>
      <div className="pick-tag">{tag}</div>
      <div className="pick-teams">
        <span className="pick-team"><TeamLogo team={away} name={g.away} size={24} tile />
          <span className="pick-name">{g.awayRank ? <span className="hero-rank">{g.awayRank}</span> : null}{g.away}</span></span>
        <span className="pick-at">{final ? `${g.awayPoints} – ${g.homePoints}` : g.neutral ? "vs" : "at"}</span>
        <span className="pick-team home"><span className="pick-name">{g.homeRank ? <span className="hero-rank">{g.homeRank}</span> : null}{g.home}</span>
          <TeamLogo team={home} name={g.home} size={24} tile /></span>
      </div>
      <div className="pick-meta"><Clock className="icon sm" aria-hidden />{final ? "Final" : localKickoff(g.start, g.startTimeTBD)}</div>
      {children}
    </>
  );
  const style = { background: `linear-gradient(115deg, ${away?.fill ?? INK} 0 49.6%, ${home?.fill ?? INK} 50.4% 100%)` };
  return g.hasBreakdown
    ? <Link href={`/game?season=${g.season}&id=${g.id}`} className="pick-card" style={style}>{body}</Link>
    : <div className="pick-card" style={style}>{body}</div>;
}
