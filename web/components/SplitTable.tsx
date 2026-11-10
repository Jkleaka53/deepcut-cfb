import { fmt, tierLabel } from "@/lib/format";
import type { SplitTable as SplitTableT } from "@/lib/types";

export default function SplitTable({ table }: { table: SplitTableT }) {
  const keys = Object.keys(table.metricLabels);
  return (
    <div>
      <h3>{table.title}</h3>
      <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
        Seasons: {table.seasons.length ? table.seasons.join(", ") : "none yet"}. Garbage time removed.
      </p>
      <div className="table-scroll">
        <table className="stats">
          <thead>
            <tr>
              <th>Opponent strength</th>
              <th>Games</th>
              <th>Plays</th>
              {keys.map((k) => <th key={k}>{table.metricLabels[k]}</th>)}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((r) => {
              const hl = r.tier === table.highlightTier;
              return (
                <tr key={r.tier} className={hl ? "highlight" : undefined}>
                  <td>
                    {tierLabel(r.tier)}
                    {hl && " ← this game"}
                    {r.games > 0 && r.smallSample && <span className="tag">Small sample</span>}
                  </td>
                  <td>{r.games}</td>
                  <td>{r.plays}</td>
                  {r.games === 0 ? (
                    <td colSpan={keys.length} className="muted">No games</td>
                  ) : (
                    keys.map((k) => <td key={k}>{fmt(r.metrics[k], table.metricFormats[k])}</td>)
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
