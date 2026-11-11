import { ChevronDown } from "lucide-react";
import { ordinal } from "@/lib/format";
import { bandText, formatStat, matchupLine } from "@/lib/swing";
import type { Driver, DriverDetail, Swing, TeamInfo } from "@/lib/types";

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function Head({ d, fill }: { d: Driver; fill?: string }) {
  return (
    <>
      <span className="swing-head">
        <span className="swing-label">{d.label}</span>
        <span className="swing-edge" style={d.edge !== "even" ? { background: fill ?? "var(--ink)", color: "#ffffff" } : undefined}>
          {bandText(d.edge, d.favors)}
        </span>
      </span>
      <span className="swing-match">{matchupLine(d)}</span>
    </>
  );
}

function Detail({ d, detail }: { d: Driver; detail: DriverDetail }) {
  const rows: [string, number | null, number | null][] = [
    [`${d.offense} offense`, detail.offValue, d.offRank],
    [`${d.defense} defense allows`, detail.defAllows, d.defRank],
    ["FBS average", detail.fbsAvg, null],
  ];
  return (
    <div className="swing-detail">
      <h5 className="swing-dl">What it means</h5>
      <p>{detail.meaning}</p>
      <h5 className="swing-dl">Why {d.favors} has the edge</h5>
      <table className="swing-table">
        <tbody>
          {rows.map(([label, v, rank]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td>{formatStat(v, detail.format)}</td>
              <td>{rank == null ? "" : `${ordinal(rank)} of ${d.of}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h5 className="swing-dl">Why it matters</h5>
      <p>{detail.why}</p>
      <h5 className="swing-dl">What to watch</h5>
      <p>{d.cue}</p>
    </div>
  );
}

export default function SwingCard({ swing, teams }: { swing: Swing | null | undefined; teams: Record<string, TeamInfo> }) {
  if (!swing) return null;
  return (
    <div className="card swing">
      <h4>What could swing this game</h4>
      {swing.drivers.length === 0 && swing.note && <p className="muted">{swing.note}</p>}
      <ol className="swing-list">
        {swing.drivers.map((d, i) => {
          const fav = teams[d.favors];
          return (
            <li key={`${d.offense}-${d.key}`}>
              <span className="swing-n">{i + 1}</span>
              {d.detail ? (
                <details name="swing" className="swing-item">
                  <summary className="swing-body">
                    <Head d={d} fill={fav?.fill} />
                    <span className="swing-more">Show the stats <ChevronDown className="icon sm" aria-hidden /></span>
                  </summary>
                  <Detail d={d} detail={d.detail} />
                </details>
              ) : (
                <div className="swing-body">
                  <Head d={d} fill={fav?.fill} />
                  <div className="swing-cue">{d.cue}</div>
                </div>
              )}
            </li>
          );
        })}
      </ol>
      {swing.storylines.length > 0 && <>
        <h5 className="swing-sub">Storylines to watch</h5>
        <ul className="story-list">
          {swing.storylines.map((s) => (
            <li key={s.text}>
              <span>{s.text}</span>
              <span className="tag">Storyline · {cap(s.sample)}</span>
            </li>
          ))}
        </ul>
      </>}
      <p className="muted small">Ranked by how much each stat has decided games since 2015, how far apart these teams are on it, and how much it swings week to week. Storylines are small samples. Not a prediction.</p>
    </div>
  );
}
