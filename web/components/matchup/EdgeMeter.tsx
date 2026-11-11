import { BAND, EDGE_BIG, EDGE_SLIGHT } from "@/lib/swing";
import type { OverallEdge, TeamInfo } from "@/lib/types";

/** Overall edge as a 0-10 meter: centered on Even, filling toward the favored team (away left, home right). */
export default function EdgeMeter({ overall, home, away, teams }: {
  overall: OverallEdge | null | undefined; home: string; away: string; teams: Record<string, TeamInfo>;
}) {
  if (!overall || overall.score == null) return null;
  const { edge, team, score } = overall;
  const even = edge === "even" || !team;
  const width = Math.min(score, 10) * 5;
  const left = team === home ? 50 : 50 - width;
  const color = team ? teams[team]?.fill : undefined;
  return (
    <div className="edge-meter">
      <p className="em-title">
        {even ? <span>Even</span> : <><span className="em-team">{team}</span> · {BAND[edge]}</>}
        {" · "}{score.toFixed(1)}
      </p>
      <div className="em-bar" role="img"
        aria-label={even ? `Even matchup, edge score ${score.toFixed(1)} of 10` : `${BAND[edge]} ${team}, edge score ${score.toFixed(1)} of 10`}>
        <span className="em-mid" />
        {!even && <span className="em-fill" style={{ left: `${left}%`, width: `${width}%`, ...(color ? { background: color } : {}) }} />}
      </div>
      <div className="em-ends"><span>{away}</span><span>Even</span><span>{home}</span></div>
      <p className="muted small">Edge score 0 to 10: Under {EDGE_SLIGHT} Even · {EDGE_SLIGHT} to {EDGE_BIG} Slight · {EDGE_BIG}+ Big</p>
    </div>
  );
}
