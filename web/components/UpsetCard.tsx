import PickCard from "./PickCard";
import type { GameSummary, TeamInfo, UpsetOdds } from "@/lib/types";

const INK = "#0b1220";

/** Upset Watch: the slim striped card plus DraftKings' own win odds as a two-color bar (away left, home right). */
export default function UpsetCard({ game: g, odds, teams }:
  { game: GameSummary; odds: UpsetOdds; teams: Record<string, TeamInfo> }) {
  const away = teams[g.away], home = teams[g.home];
  return (
    <PickCard tag="Upset Watch" game={g} teams={teams}>
      <div className="odds-bar" role="img" aria-label={`${odds.source} odds: ${g.away} ${odds.away}%, ${g.home} ${odds.home}%`}>
        <span className="odds-seg" style={{ width: `${odds.away}%`, background: away?.fill ?? INK }}>
          {away?.abbr ?? g.away} {odds.away}%
        </span>
        <span className="odds-seg home" style={{ width: `${odds.home}%`, background: home?.fill ?? INK }}>
          {home?.abbr ?? g.home} {odds.home}%
        </span>
      </div>
      <div className="odds-cap">{odds.source} odds</div>
    </PickCard>
  );
}
