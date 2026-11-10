"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import SplitTable from "@/components/SplitTable";
import UnitTable from "@/components/UnitTable";
import { loadMatchup } from "@/lib/data";
import type { Matchup } from "@/lib/types";

function when(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
}

function MatchupView() {
  const params = useSearchParams();
  const season = Number(params.get("season"));
  const id = Number(params.get("id"));
  const [m, setM] = useState<Matchup | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    if (!season || !id) { setMissing(true); return; }
    setMissing(false);
    setM(null);
    loadMatchup(season, id).then(setM).catch(() => setMissing(true));
  }, [season, id]);

  if (missing) {
    return (
      <p>
        No breakdown for this game. <Link href="/">Back to all games</Link>
      </p>
    );
  }
  if (!m) return <p className="muted">Loading breakdown…</p>;

  const g = m.game;
  const final = g.completed && g.homePoints !== null && g.awayPoints !== null;

  return (
    <article>
      <p className="label">{g.seasonType === "postseason" ? `${g.season} postseason` : `${g.season} · Week ${g.week}`}</p>
      <h1>
        {g.away} {g.neutral ? "vs" : "@"} {g.home}
      </h1>
      <p className="muted" style={{ marginTop: 0 }}>
        {when(g.start)}
        {g.neutral ? " · Neutral site" : ""}
        {g.venue ? ` · ${g.venue}` : ""}
      </p>
      {final && (
        <p>
          <strong>Final:</strong> {g.away} {g.awayPoints}, {g.home} {g.homePoints}
        </p>
      )}
      {m.notes.map((n) => <div key={n} className="callout">{n}</div>)}

      {m.sections.map((s) => (
        <section key={s.offenseTeam} className="section-head">
          <h2 style={{ marginTop: 0 }}>
            {s.offenseTeam} passing vs. {s.defenseTeam} defense
          </h2>
          {m.quarterbacks[s.offenseTeam] === null && (
            <p className="muted">No starting quarterback identified yet, so there&apos;s no QB split.</p>
          )}
          {s.units.map((u) => <UnitTable key={u.title} table={u} />)}
          {s.splits.map((t) => <SplitTable key={t.title} table={t} />)}
        </section>
      ))}
    </article>
  );
}

export default function GamePage() {
  return (
    <Suspense fallback={<p className="muted">Loading breakdown…</p>}>
      <MatchupView />
    </Suspense>
  );
}
