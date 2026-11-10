import Link from "next/link";
import { Clock, MapPin } from "lucide-react";
import TeamLogo from "./TeamLogo";
import WeatherIcon from "./WeatherIcon";
import { localKickoff } from "@/lib/format";
import { weatherMini } from "@/lib/weather";
import type { GameSummary, TeamInfo } from "@/lib/types";

const INK = "#0b1220";

function Team({ name, rank, team }: { name: string; rank: number | null | undefined; team?: TeamInfo }) {
  return (
    <div className="gotw-team">
      <TeamLogo team={team} name={name} size={40} tile />
      <div className="gotw-name">{rank ? <span className="hero-rank">{rank}</span> : null}{name}</div>
    </div>
  );
}

export default function GotwCard({ game: g, why, teams }: { game: GameSummary; why: string; teams: Record<string, TeamInfo> }) {
  const away = teams[g.away], home = teams[g.home];
  const final = g.completed && g.awayPoints !== null && g.homePoints !== null;
  const mini = final ? null : weatherMini(g.weather);
  const body = (
    <>
      <div className="gotw-tag">Game of the Week</div>
      <div className="gotw-teams">
        <Team name={g.away} rank={g.awayRank} team={away} />
        <div className="gotw-at">{final ? `${g.awayPoints} – ${g.homePoints}` : g.neutral ? "vs" : "at"}</div>
        <Team name={g.home} rank={g.homeRank} team={home} />
      </div>
      <div className="gotw-meta">
        <span><Clock className="icon sm" aria-hidden />{final ? "Final" : localKickoff(g.start, g.startTimeTBD)}</span>
        {g.venue && <span><MapPin className="icon sm" aria-hidden />{g.venue}</span>}
        {mini && <span><WeatherIcon kind={g.weather?.icon} indoors={g.weather?.status === "indoors"} />{mini}</span>}
      </div>
      <div className="gotw-why"><b>Why watch:</b> {why}</div>
    </>
  );
  const style = { background: `linear-gradient(115deg, ${away?.fill ?? INK} 0 49.6%, ${home?.fill ?? INK} 50.4% 100%)` };
  return g.hasBreakdown
    ? <Link href={`/game?season=${g.season}&id=${g.id}`} className="gotw" style={style}>{body}</Link>
    : <div className="gotw" style={style}>{body}</div>;
}
