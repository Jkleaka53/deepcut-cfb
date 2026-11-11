"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import BackButton from "@/components/BackButton";
import { getWatch, toggleWatch } from "@/lib/watchlist";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import AvailabilityWatch from "@/components/matchup/AvailabilityWatch";
import WhatIfBanner from "@/components/matchup/WhatIfBanner";
import SwingCard from "@/components/matchup/SwingCard";
import { badgeFor } from "@/lib/swing";
import { loadOut, saveOut, differs } from "@/lib/choices";
import { applyWhatIf, defaultsOut, listedIds, whatIfText } from "@/lib/whatif";
import EdgeCard from "@/components/matchup/EdgeCard";
import HeadToHead from "@/components/matchup/HeadToHead";
import Hero from "@/components/matchup/Hero";
import QbTiers from "@/components/matchup/QbTiers";
import SectionTabs from "@/components/matchup/SectionTabs";
import TeamLogo from "@/components/TeamLogo";
import { loadMatchup, loadShootout, loadTeams, loadUpset } from "@/lib/data";
import { pickWhyFor } from "@/lib/gotw";
import PickNote from "@/components/matchup/PickNote";
import { passingRows, runView, topGaps, visibleTabs } from "@/lib/matchup";
import { normalizeMatchup } from "@/lib/normalize";
import type { Matchup, Section, TeamInfo } from "@/lib/types";

const LEGEND = "Rank is out of 138 FBS teams (1st = best for that side). More color in the bar = stronger.";

/** One card per offense: its passing or running rows against the other team's defense. */
function PhaseCards({ sections, verb, teams }: { sections: Section[]; verb: "passes" | "runs"; teams: Record<string, TeamInfo> }) {
  return (
    <>
      {sections.map((s) => (
        <div key={s.offenseTeam} className="card flush">
          <div className="pg-head">
            <div style={{ background: teams[s.offenseTeam]?.fill ?? "var(--ink)" }}>
              <TeamLogo team={teams[s.offenseTeam]} name={s.offenseTeam} size={18} tile />{s.offenseTeam} offense
            </div>
            <div style={{ background: teams[s.defenseTeam]?.fill ?? "var(--ink)" }}>
              {s.defenseTeam} defense<TeamLogo team={teams[s.defenseTeam]} name={s.defenseTeam} size={18} tile />
            </div>
          </div>
          <h4 className="pg-title">When {s.offenseTeam} {verb}</h4>
          {passingRows(s).map((r) => (
            <div key={r.key}>
              <HeadToHead row={r} offense={s.offenseTeam} defense={s.defenseTeam} teams={teams} badge={badgeFor(r, s)} />
              {r.hint && <div className="h2h-hint">{r.hint}</div>}
            </div>
          ))}
          <p className="muted small legend">{LEGEND}</p>
        </div>
      ))}
    </>
  );
}

function MatchupView() {
  const params = useSearchParams();
  const season = Number(params.get("season"));
  const id = Number(params.get("id"));
  const [raw, setM] = useState<Matchup | null>(null);
  const [teams, setTeams] = useState<Record<string, TeamInfo>>({});
  const [missing, setMissing] = useState(false);
  const [out, setOut] = useState<Set<number>>(new Set());
  const [watched, setWatched] = useState<number[]>([]);
  const [shootWhy, setShootWhy] = useState<string | null>(null);
  const [upsetWhy, setUpsetWhy] = useState<string | null>(null);
  useEffect(() => setWatched(getWatch()), []);

  useEffect(() => {
    if (!season || !id) { setMissing(true); return; }
    setMissing(false);
    setM(null);
    loadMatchup(season, id).then((x) => {
      const nm = normalizeMatchup(x);
      setOut(nm.game.completed ? new Set() : loadOut(season, id, defaultsOut(nm), listedIds(nm)));
      setM(nm);
    }).catch(() => setMissing(true));
    loadTeams(season).then(setTeams);
    setShootWhy(null);
    loadShootout(season).then((p) => setShootWhy(pickWhyFor(p, id)));
    setUpsetWhy(null);
    loadUpset(season).then((p) => setUpsetWhy(pickWhyFor(p, id)));
  }, [season, id]);

  const base = raw;
  const defaults = useMemo(() => (base ? defaultsOut(base) : new Set<number>()), [base]);
  const view = useMemo(() => (base && !base.game.completed ? applyWhatIf(base, out) : base), [base, out]);

  if (missing) return <p className="empty">No breakdown for this game. <Link href="/">Back to all games</Link></p>;
  if (!base || !view) return <p className="empty">Loading breakdown…</p>;

  const toggle = (pid: number, isOut: boolean) => {
    const next = new Set(out);
    if (isOut) next.add(pid); else next.delete(pid);
    setOut(next);
    saveOut(season, id, next, defaults);
  };
  const reset = () => { setOut(new Set(defaults)); saveOut(season, id, defaults, defaults); };
  const banner = base.game.completed ? null : whatIfText(base, out, defaults);
  const m = view;
  const g = m.game;
  const tabs = visibleTabs(m);
  const gaps = topGaps(m.sections);
  return (
    <article className="matchup">
      <div className="crumbrow">
        <BackButton />
        <button className={`watchbtn ${watched.includes(id) ? "on" : ""}`} aria-pressed={watched.includes(id)}
          onClick={() => setWatched(toggleWatch(id))}>
          <Bell className="icon sm" aria-hidden fill={watched.includes(id) ? "currentColor" : "none"} />
          {watched.includes(id) ? "Watching" : "Watch"}
        </button>
      </div>
      <p className="crumb">{g.seasonType === "postseason" ? `${g.season} postseason` : `${g.season} · Week ${g.week}`}</p>
      <Hero m={m} teams={teams} />
      {shootWhy && <PickNote tag="Shootout of the Week" why={shootWhy} />}
      {upsetWhy && <PickNote tag="Upset Watch" heading="Why that could be wrong" why={upsetWhy} />}
      {banner && <WhatIfBanner text={banner} canReset={differs(out, defaults)} onReset={reset} />}
      {m.notes.map((n) => <div key={n} className="callout">{n}</div>)}
      <SectionTabs show={tabs} />

      <section id="preview">
        <h3 className="sec-title">Preview</h3>
        <SwingCard swing={m.swing} teams={teams} />
        <EdgeCard sections={m.sections} teams={teams} overall={m.swing?.overallEdge} home={m.game.home} away={m.game.away} />
        {gaps.length > 0 && <div className="card">
          <h4>Biggest edges</h4>
          {gaps.map(({ section, row, phase }) => (
            <div key={`${section.offenseTeam}-${row.key}`}>
              <div className="h2h-context">When {section.offenseTeam} {phase === "run" ? "runs" : "passes"}</div>
              <HeadToHead row={row} offense={section.offenseTeam} defense={section.defenseTeam} teams={teams} />
            </div>
          ))}
        </div>}
      </section>

      <section id="passing">
        <h3 className="sec-title">Passing game</h3>
        <PhaseCards sections={m.sections} verb="passes" teams={teams} />
      </section>

      {tabs.includes("running") && <section id="running">
        <h3 className="sec-title">Running game</h3>
        <PhaseCards sections={m.sections.map(runView).filter((s): s is Section => s !== null)} verb="runs" teams={teams} />
      </section>}

      <section id="qb">
        <h3 className="sec-title">QB splits</h3>
        {m.sections.map((s) => <QbTiers key={s.offenseTeam} section={s} qb={m.quarterbacks[s.offenseTeam]?.name ?? null} teams={teams} />)}
      </section>

      {tabs.includes("availability") && <section id="availability">
        <h3 className="sec-title">Availability watch</h3>
        {[g.away, g.home].map((t) => (
          <AvailabilityWatch key={t} team={t} data={m.availability?.[t]} completed={g.completed} out={out} onToggle={toggle} info={teams[t]} />
        ))}
        <p className="muted small">Our check uses each team&apos;s own box scores. It says what happened, never why.</p>
      </section>}
    </article>
  );
}

export default function GamePage() {
  return (
    <Suspense fallback={<p className="empty">Loading breakdown…</p>}>
      <MatchupView />
    </Suspense>
  );
}
