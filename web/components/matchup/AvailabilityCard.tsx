import { AlertTriangle, Check, ExternalLink } from "lucide-react";
import type { TeamAvailability } from "@/lib/types";

export default function AvailabilityCard({ team, data }: { team: string; data?: TeamAvailability }) {
  const flags = data?.flags ?? [];
  const r = data?.report;
  return (
    <div className="card">
      <h4>{team}</h4>
      {flags.length === 0 && <p className="muted">No quarterback games on record yet this season.</p>}
      {flags.map((f) => (
        <div key={f.text} className={`flag ${f.kind}`}>
          {f.kind === "ok" ? <Check className="icon sm" aria-hidden /> : <AlertTriangle className="icon sm" aria-hidden />}
          <span>{f.text}</span>
        </div>
      ))}
      {r?.url ? (
        <p className="report">
          <a href={r.url} target="_blank" rel="noopener noreferrer">
            {r.conference} availability report <ExternalLink className="icon sm" aria-hidden />
          </a>
          {r.when && <span className="muted"> {r.when}</span>}
        </p>
      ) : r?.publishes ? (
        <p className="report">Check the {r.conference}&apos;s official availability report.{r.when && <span className="muted"> {r.when}</span>}</p>
      ) : (
        <p className="muted report">No official availability report for this game.</p>
      )}
    </div>
  );
}
