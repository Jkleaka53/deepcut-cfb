import SplitTable from "../SplitTable";
import TeamLogo from "../TeamLogo";
import { fmt, ordinal } from "@/lib/format";
import { rowLabel, splitAt, summary, visibleRows } from "@/lib/qbsplit";
import type { QbGame, QbVs, SplitTable as SplitTableT, TeamInfo } from "@/lib/types";

const SMALL = 3;

function Box({ head, b, on }: { head: string; b: ReturnType<typeof splitAt>["above"]; on: boolean }) {
  return (
    <div className={`qb-box ${on ? "on" : ""}`}>
      <div className="qb-box-h">{head}</div>
      <div className="qb-rec num">{b.games === 0 ? "—" : `${b.w}-${b.l}`}</div>
      <div className="qb-box-m">
        {b.epa === null ? "" : `${fmt(b.epa, "epa")} pts per pass · `}{b.games} {b.games === 1 ? "game" : "games"}
      </div>
      {on && <span className="qb-flag">◆ This game</span>}
      {b.games > 0 && b.games < SMALL && <span className="tag">Small sample</span>}
    </div>
  );
}

function Row({ g, dim }: { g: QbGame; dim?: boolean }) {
  return (
    <tr className={dim ? "below" : undefined}>
      <td className="o">{g.opponent} <span className="yr">{rowLabel(g)}</span></td>
      <td className="r num">{ordinal(g.oppRank)}</td>
      <td className="r">{g.result && <span className={`res ${g.result}`}>{g.result}</span>} {g.pf !== null ? `${g.pf}-${g.pa}` : ""}</td>
      <td className="r num">{fmt(g.epaPerDb, "epa")}</td>
    </tr>
  );
}

interface Props { qb: QbVs; offense: string; teams: Record<string, TeamInfo>; detail?: SplitTableT }

export default function QbCard({ qb, offense, teams, detail }: Props) {
  const opp = teams[qb.opponent];
  const cut = qb.oppRank;
  const rows = cut === null ? { above: [], below: qb.games, hidden: [] } : visibleRows(qb.games, cut);
  const shown = cut === null ? qb.games.slice(0, 8) : [...rows.above, ...rows.below];
  const hidden = cut === null ? qb.games.slice(8) : rows.hidden;
  const s = cut === null ? null : splitAt(qb.games, cut);
  const text = summary(qb);
  const line = (
    <tr className="cut"><td colSpan={4}>▲ {qb.opponent} {cut !== null ? ordinal(cut) : ""} · tougher D above</td></tr>
  );
  return (
    <div className="card">
      <h4 className="qb-ttl"><TeamLogo team={teams[offense]} name={offense} size={22} />{qb.name} vs. pass defenses</h4>
      {cut !== null && (
        <div className="qb-vs" style={{ background: opp?.fill ?? "var(--ink)" }}>
          <div className="qb-vs-l">
            <TeamLogo team={opp} name={qb.opponent} size={26} tile />
            <div>This week<br /><b>{qb.opponent} pass D</b></div>
          </div>
          <div className="qb-vs-r"><b className="num">{ordinal(cut)}</b>{qb.of ? <small>of {qb.of}</small> : null}</div>
        </div>
      )}
      {s && (
        <div className="qb-cmp">
          <Box head={`vs. pass defenses ranked ${ordinal(cut)} or better`} b={s.above} on />
          <Box head={`vs. pass defenses ranked worse than ${ordinal(cut)}`} b={s.below} on={false} />
        </div>
      )}
      {text && <div className="qb-say">{text}</div>}
      {qb.games.length === 0 ? (
        <p className="muted">No starts against FBS pass defenses on record yet.</p>
      ) : (
        <table className="qb-log">
          <thead><tr><th>Opponent</th><th className="r">Pass D</th><th className="r">Result</th><th className="r">Pts/ pass</th></tr></thead>
          <tbody>
            {cut === null ? shown.map((g) => <Row key={g.gameId} g={g} />) : (
              <>
                {rows.above.map((g) => <Row key={g.gameId} g={g} />)}
                {line}
                {rows.below.map((g) => <Row key={g.gameId} g={g} dim />)}
              </>
            )}
          </tbody>
        </table>
      )}
      <p className="muted small qb-note">
        Pass D = the opponent&apos;s rank in points allowed per pass that season (this season: up to kickoff). Pts/pass = {offense}&apos;s
        points added per pass that game. Games he started against FBS teams, at every school.
      </p>
      {(hidden.length > 0 || detail) && (
        <details className="more">
          <summary>{hidden.length > 0 ? `More: ${hidden.length} more ${hidden.length === 1 ? "game" : "games"}` : "More"}{detail ? " and the full split table" : ""}</summary>
          {hidden.length > 0 && (
            <table className="qb-log"><tbody>{hidden.map((g) => <Row key={g.gameId} g={g} dim />)}</tbody></table>
          )}
          {detail && <SplitTable table={detail} />}
        </details>
      )}
    </div>
  );
}
