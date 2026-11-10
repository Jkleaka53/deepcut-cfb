import { edgeText, fmt, rankText } from "@/lib/format";
import type { UnitTable as UnitTableT } from "@/lib/types";

export default function UnitTable({ table }: { table: UnitTableT }) {
  return (
    <div>
      <h3>{table.title}</h3>
      <div className="table-scroll">
        <table className="stats">
          <thead>
            <tr>
              <th></th>
              <th>{table.offenseTeam} offense</th>
              <th>{table.defenseTeam} defense</th>
              <th>Edge</th>
            </tr>
          </thead>
          <tbody>
            {table.rows.map((r) => (
              <tr key={r.key}>
                <td>{r.label}</td>
                <td>
                  {fmt(r.offense.value, r.format)} <span className="muted">{rankText(r.offense.rank)}</span>
                </td>
                <td>
                  {fmt(r.defense.value, r.format)} <span className="muted">{rankText(r.defense.rank)}</span>
                </td>
                <td className={r.edge?.startsWith("clear") ? "edge-clear" : undefined}>
                  {edgeText(r.edge, table.offenseTeam, table.defenseTeam)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted" style={{ fontSize: "0.8rem", margin: "2px 0 0" }}>
        Ranks are among FBS teams (#1 = best for that side).
      </p>
    </div>
  );
}
