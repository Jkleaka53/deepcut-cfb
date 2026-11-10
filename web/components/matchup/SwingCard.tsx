import { bandText, matchupLine } from "@/lib/swing";
import type { Swing, TeamInfo } from "@/lib/types";

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

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
              <div className="swing-body">
                <div className="swing-head">
                  <span className="swing-label">{d.label}</span>
                  <span className="swing-edge" style={d.edge !== "even" ? { background: fav?.fill ?? "var(--ink)", color: "#ffffff" } : undefined}>
                    {bandText(d.edge, d.favors)}
                  </span>
                </div>
                <div className="swing-match">{matchupLine(d)}</div>
                <div className="swing-cue">{d.cue}</div>
              </div>
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
