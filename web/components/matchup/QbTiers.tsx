import SplitTable from "../SplitTable";
import { fmt, tierLabel } from "@/lib/format";
import type { Section } from "@/lib/types";

export default function QbTiers({ section, qb }: { section: Section; qb: string | null }) {
  const qbTable = qb ? section.splits.find((t) => t.subject === qb) : undefined;
  const others = section.splits.filter((t) => t !== qbTable);
  return (
    <div className="card">
      <h4>{qb ? `${qb} vs. pass defenses` : `${section.offenseTeam} passing`}</h4>
      {qbTable ? (
        <div className="tiers">
          {qbTable.rows.map((r) => {
            const on = r.tier === qbTable.highlightTier;
            return (
              <div key={r.tier} className={`tier ${on ? "on" : ""}`}>
                <div className="tier-name">{tierLabel(r.tier)}</div>
                <div className="tier-val num">{r.games === 0 ? "—" : fmt(r.metrics.epa_per_db ?? null, "epa")}</div>
                <div className="tier-sub">{r.games} {r.games === 1 ? "game" : "games"}</div>
                {on && <div className="tier-flag">this game</div>}
                {r.games > 0 && r.smallSample && <span className="tag">Small sample</span>}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="muted">No starting quarterback identified yet, so there&apos;s no QB split.</p>
      )}
      {qbTable && <p className="muted small">Points added per pass against defenses in each third of FBS.</p>}
      <details className="more">
        <summary>More</summary>
        {qbTable && <SplitTable table={qbTable} />}
        {others.map((t) => <SplitTable key={t.title} table={t} />)}
      </details>
    </div>
  );
}
