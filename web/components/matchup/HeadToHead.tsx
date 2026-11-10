import { fmt, ordinal, splitShare, verdict } from "@/lib/format";
import type { TeamInfo, UnitRow } from "@/lib/types";

interface Props { row: UnitRow; offense: string; defense: string; teams: Record<string, TeamInfo>; badge?: string | null }

const colorVars = (t?: TeamInfo) => ({ "--tl": t?.textLight ?? "var(--ink)", "--td": t?.textDark ?? "var(--ink)" }) as React.CSSProperties;

/** Light theme uses the team fill; dark theme uses barDark (the team hue lightened to show on the dark card). */
const barVars = (t: TeamInfo | undefined, width: number) =>
  ({ width: `${width}%`, "--bl": t?.fill ?? "var(--muted)", "--bd": t?.barDark ?? t?.fill ?? "var(--muted)" }) as React.CSSProperties;

export default function HeadToHead({ row, offense, defense, teams, badge }: Props) {
  const o = row.offense, d = row.defense;
  const op = o.pct ?? null, dp = d.pct ?? null;
  const both = o.value !== null && d.value !== null && op !== null && dp !== null;
  const offWins = both && op! > dp!, defWins = both && dp! > op!;
  const v = both ? verdict(row.edge, offense, defense) : { text: "", team: null };
  const share = both ? splitShare(op, dp) : null;
  return (
    <div className="h2h">
      <div className={`h2h-val l ${offWins ? "win" : both ? "lose" : ""}`}>
        <span className="num">{o.value === null ? "—" : fmt(o.value, row.format)}</span>
        <span className="h2h-rank">{o.value === null ? "" : ordinal(o.rank)}</span>
      </div>
      <div className="h2h-mid">
        <div className="h2h-label">{row.label}{badge && <span className="badge-accent">{badge}</span>}</div>
        {row.explain && <div className="h2h-explain">{row.explain}</div>}
        {v.text && <div className="h2h-verdict" style={colorVars(v.team ? teams[v.team] : undefined)}>{v.text}</div>}
      </div>
      <div className={`h2h-val r ${defWins ? "win" : both ? "lose" : ""}`}>
        <span className="num">{d.value === null ? "—" : fmt(d.value, row.format)}</span>
        <span className="h2h-rank">{d.value === null ? "" : ordinal(d.rank)}</span>
      </div>
      {share !== null && (
        <div className="h2h-bar" aria-hidden>
          <span style={barVars(teams[offense], share)} />
          <span style={barVars(teams[defense], 100 - share)} />
        </div>
      )}
    </div>
  );
}
