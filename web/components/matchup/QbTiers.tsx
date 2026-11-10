import { ChevronDown, ChevronUp } from "lucide-react";
import QbCard from "./QbCard";
import SplitTable from "../SplitTable";
import TeamLogo from "../TeamLogo";
import { splitAt } from "@/lib/qbsplit";
import type { Section, TeamInfo } from "@/lib/types";

/** One collapsible block per offense: the QB card plus the three unit split tables. Starts closed. */
export default function QbTiers({ section, qb, teams }: { section: Section; qb: string | null; teams: Record<string, TeamInfo> }) {
  const qbTable = qb ? section.splits.find((t) => t.subject === qb) : undefined;
  const others = section.splits.filter((t) => t !== qbTable);
  const q = section.qbVs;
  const count = (q || qbTable ? 1 : 0) + others.length;
  let record: string | null = null;
  if (q && q.oppRank !== null) {
    const a = splitAt(q.games, q.oppRank).above;
    record = a.games === 0 ? `No starts vs. pass D as good as ${q.opponent}'s` : `${a.w}-${a.l} vs. pass D as good as ${q.opponent}'s`;
  }
  const team = teams[section.offenseTeam];
  return (
    <details className="qb-group">
      <summary style={{ background: team?.fill ?? "var(--ink)" }}>
        <TeamLogo team={team} name={section.offenseTeam} size={30} tile />
        <span className="qbg-text">
          <span className="qbg-team">{section.offenseTeam} passing game</span>
          <span className="qbg-sub">{qb ? `QB ${qb}` : "No starting QB yet"}</span>
          {record && <span className="qbg-sub">{record}</span>}
        </span>
        <span className="qbg-btn">
          <span className="when-closed">Show all {count} splits <ChevronDown className="icon sm" aria-hidden /></span>
          <span className="when-open">Hide splits <ChevronUp className="icon sm" aria-hidden /></span>
        </span>
      </summary>
      <div className="qbg-body">
        {q ? (
          <QbCard qb={q} offense={section.offenseTeam} teams={teams} detail={qbTable} />
        ) : (
          <div className="card">
            <h4>{section.offenseTeam} passing</h4>
            {qbTable ? <SplitTable table={qbTable} /> : (
              <p className="muted">No starting quarterback identified yet, so there&apos;s no QB split.</p>
            )}
          </div>
        )}
        {others.map((t) => (
          <div key={t.title} className="card split-card"><SplitTable table={t} /></div>
        ))}
      </div>
    </details>
  );
}
