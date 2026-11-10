import QbCard from "./QbCard";
import SplitTable from "../SplitTable";
import type { Section, TeamInfo } from "@/lib/types";

/** QB card (record and game log vs. pass defenses) plus the unit split tables, each in its own card. */
export default function QbTiers({ section, qb, teams }: { section: Section; qb: string | null; teams: Record<string, TeamInfo> }) {
  const qbTable = qb ? section.splits.find((t) => t.subject === qb) : undefined;
  const others = section.splits.filter((t) => t !== qbTable);
  return (
    <>
      {section.qbVs ? (
        <QbCard qb={section.qbVs} offense={section.offenseTeam} teams={teams} detail={qbTable} />
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
    </>
  );
}
