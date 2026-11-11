import { edgeLine, runView } from "@/lib/matchup";
import { overallText } from "@/lib/swing";
import EdgeMeter from "./EdgeMeter";
import type { OverallEdge, Section, TeamInfo } from "@/lib/types";

function sentence(sections: Section[]): string {
  const lines = sections.map((s) => ({ s, l: edgeLine(s) })).filter((x) => x.l);
  if (lines.length === 0) return "Not enough data yet to compare these passing games.";
  const defAhead = lines.filter((x) => x.s.edge?.endsWith("defense"));
  const offAhead = lines.filter((x) => x.s.edge?.endsWith("offense"));
  const big = (x: { s: Section }) => x.s.edge?.startsWith("clear");
  if (defAhead.length === 2) {
    const [a, b] = defAhead;
    const bigger = big(a) && !big(b) ? a.s.defenseTeam : big(b) && !big(a) ? b.s.defenseTeam : null;
    return `Both defenses have the upper hand.${bigger ? ` ${bigger}'s is the bigger edge.` : ""}`;
  }
  const parts = [
    ...defAhead.map((x) => `${x.s.defenseTeam}'s defense is ahead when ${x.s.offenseTeam} passes`),
    ...offAhead.map((x) => `${x.s.offenseTeam}'s passing game is ahead of ${x.s.defenseTeam}'s defense`),
  ];
  return parts.length ? `${parts.join("; ")}.` : "These passing games are evenly matched.";
}

export default function EdgeCard({ sections, teams, overall, home, away }: {
  sections: Section[]; teams: Record<string, TeamInfo>; overall?: OverallEdge | null; home: string; away: string;
}) {
  const scored = overall?.score != null;
  const o = scored ? null : overallText(overall);
  return (
    <div className="card">
      <h4>The edge</h4>
      {scored && <EdgeMeter overall={overall} home={home} away={away} />}
      {o && <p className="edge-overall">{o}</p>}
      <p className="edge-sentence">{sentence(sections)}</p>
      {[...sections.map((s) => ({ s, verb: "passes" as const })),
        ...sections.flatMap((x) => { const r = runView(x); return r ? [{ s: r, verb: "runs" as const }] : []; })].map(({ s, verb }) => {
        const l = edgeLine(s, verb);
        if (!l) return null;
        const t = l.team ? teams[l.team] : undefined;
        return (
          <div key={`${verb}-${s.offenseTeam}`} className={`edge-line ${l.team ? "" : "even"}`}
            style={l.team ? { background: t?.fill ?? "var(--ink)", color: "#ffffff" } : undefined}>{l.text}</div>
        );
      })}
      <p className="muted small">{o || scored ? "Overall weighs every stat by how much it has decided games. The lines below are the passing and running stats. " : ""}Who ranks better on paper. Not a prediction.</p>
    </div>
  );
}
