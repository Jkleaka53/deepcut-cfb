import { AlertTriangle, Check, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import TeamLogo from "../TeamLogo";
import AvailabilityCard from "./AvailabilityCard";
import type { TeamAvailability, TeamInfo, WatchPlayer } from "@/lib/types";

type Props = { team: string; data?: TeamAvailability; completed: boolean; out: Set<number>; onToggle: (id: number, out: boolean) => void; info?: TeamInfo };

function roleLine(p: WatchPlayer, starter: string | null): string {
  if (p.role === "QB") return "Starting QB";
  if (p.role === "QB2") return `Backup QB · takes over if ${starter ?? "the starter"} is Out`;
  if (p.share === null) return `No ${p.shareOf ?? "yards"} yet`;
  return `${Math.round(p.share * 100)}% of ${p.shareOf}`;
}

/** One collapsible block per team, closed to start. Completed games and older data hold the plain card. */
export default function AvailabilityWatch(props: Props) {
  const { team, data, completed, out, info } = props;
  const live = !completed && !!data?.players;
  const players = data?.players ?? [];
  const switchable = players.filter((p) => p.role !== "QB2");
  const sub = live
    ? `${switchable.length} players to set · ${switchable.filter((p) => out.has(p.athleteId)).length} Out`
    : data?.flags[0]?.text ?? "No quarterback games on record yet this season.";
  return (
    <details className="qb-group aw-group">
      <summary style={{ borderTopColor: info?.fill ?? "var(--ink)" }}>
        <TeamLogo team={info} name={team} size={30} tile />
        <span className="qbg-text">
          <span className="qbg-team">{team} availability</span>
          <span className="qbg-sub">{sub}</span>
        </span>
        <span className="qbg-btn">
          <span className="when-closed">{live ? `Show all ${players.length} players` : "Show details"} <ChevronDown className="icon sm" aria-hidden /></span>
          <span className="when-open">Hide <ChevronUp className="icon sm" aria-hidden /></span>
        </span>
      </summary>
      <div className="qbg-body">
        {live ? <WatchList {...props} /> : <AvailabilityCard team={team} data={data} />}
      </div>
    </details>
  );
}

function WatchList({ data, out, onToggle }: Props) {
  if (!data?.players) return null;
  const r = data.report;
  const starter = data.players.find((p) => p.role === "QB")?.name ?? null;
  const b = data.backup;
  return (
    <div className="card aw">
      {data.flags.map((f) => (
        <div key={f.text} className={`flag ${f.kind}`}>
          {f.kind === "ok" ? <Check className="icon sm" aria-hidden /> : <AlertTriangle className="icon sm" aria-hidden />}
          <span>{f.text}</span>
        </div>
      ))}
      <p className="aw-research">
        Check the official report, then set players In or Out.{" "}
        {r.url ? (
          <a href={r.url} target="_blank" rel="noopener noreferrer">
            {r.conference} availability report <ExternalLink className="icon sm" aria-hidden />
          </a>
        ) : r.publishes ? (
          <span className="muted">Find it on the {r.conference}&apos;s website.</span>
        ) : (
          <span className="muted">No official report for this game.</span>
        )}
      </p>
      <ul className="aw-list">
        {data.players.map((p) => {
          const isOut = out.has(p.athleteId);
          const locked = p.role === "QB" && !b;
          return (
            <li key={p.athleteId} className={`aw-row${isOut ? " is-out" : ""}`} data-player={p.athleteId}>
              <div className="aw-who">
                <span className="aw-name">{p.name}</span>
                <span className="aw-role">{roleLine(p, starter)}</span>
                <span className="aw-tags">
                  {p.noStatsLastGame && <span className="tag">No stats last game</span>}
                  {p.role === "QB2" && b?.smallSample && <span className="tag">Small sample</span>}
                </span>
                {p.role === "QB2" && b && b.games === 0 && (
                  <span className="aw-note">No starts yet, so his numbers show as dashes.</span>
                )}
                {locked && <span className="aw-note">No other QB has thrown a pass this season</span>}
              </div>
              {p.role !== "QB2" && (
                <div className="aw-switch" role="group" aria-label={`${p.name} availability`}>
                  <button type="button" aria-pressed={!isOut} disabled={locked} onClick={() => onToggle(p.athleteId, false)}>In</button>
                  <button type="button" aria-pressed={isOut} disabled={locked} onClick={() => onToggle(p.athleteId, true)}>Out</button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
      <p className="muted small">Setting the starting QB Out swaps in the backup&apos;s numbers from his own starts. Receivers and backs show their share only; switching them doesn&apos;t change any numbers.</p>
    </div>
  );
}
