import { MapPin } from "lucide-react";
import TeamLogo from "../TeamLogo";
import WeatherIcon from "../WeatherIcon";
import { localKickoff } from "@/lib/format";
import { weatherStrip } from "@/lib/weather";
import type { Matchup, TeamInfo } from "@/lib/types";

const INK = "#0b1220";

function Side({ name, rank, qb, team, points, align }:
  { name: string; rank: number | null | undefined; qb: string | null; team?: TeamInfo; points: number | null; align: "l" | "r" }) {
  return (
    <div className={`hero-side ${align}`}>
      <TeamLogo team={team} name={name} size={40} tile />
      <div className="hero-name">{rank ? <span className="hero-rank">{rank}</span> : null}{name}</div>
      {qb && <div className="hero-qb">QB {qb}</div>}
      {points !== null && <div className="hero-pts num">{points}</div>}
    </div>
  );
}

export default function Hero({ m, teams }: { m: Matchup; teams: Record<string, TeamInfo> }) {
  const g = m.game;
  const away = teams[g.away], home = teams[g.home];
  const final = g.completed && g.awayPoints !== null && g.homePoints !== null;
  const wx = final ? null : weatherStrip(g.weather);
  const v = m.venue;
  const place = [v?.name ?? g.venue, [v?.city, v?.state].filter(Boolean).join(", "), v?.dome ? "Indoors" : v?.grass === true ? "Grass" : v?.grass === false ? "Turf" : null]
    .filter(Boolean).join(" · ");
  return (
    <header className="hero">
      <div className="hero-split" style={{ background: `linear-gradient(115deg, ${away?.fill ?? INK} 0 49.6%, ${home?.fill ?? INK} 50.4% 100%)` }}>
        <Side name={g.away} rank={g.awayRank} qb={m.quarterbacks[g.away]?.name ?? null} team={away} points={final ? g.awayPoints : null} align="l" />
        <div className="hero-mid">
          <span className="hero-at">{g.neutral ? "vs" : "at"}</span>
          <span className="hero-when">{final ? "Final" : localKickoff(g.start)}</span>
        </div>
        <Side name={g.home} rank={g.homeRank} qb={m.quarterbacks[g.home]?.name ?? null} team={home} points={final ? g.homePoints : null} align="r" />
      </div>
      {place && <div className="hero-venue"><MapPin className="icon sm" aria-hidden />{place}</div>}
      {wx && (
        <div className="hero-wx">
          <WeatherIcon kind={wx.icon} indoors={g.weather?.status === "indoors"} />
          <span>{wx.parts.join(" · ")}</span>
          {wx.asOf && <span className="muted hero-asof">{wx.asOf}</span>}
        </div>
      )}
    </header>
  );
}
