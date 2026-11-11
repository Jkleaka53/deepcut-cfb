"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bell, Star } from "lucide-react";
import ChipRow from "@/components/ChipRow";
import GotwCard from "@/components/GotwCard";
import PickCard from "@/components/PickCard";
import ScoreRow from "@/components/ScoreRow";
import { loadGames, loadGotw, loadIndex, loadPlayers, loadShootout, loadTeams } from "@/lib/data";
import { gotwFor, pickFor, type GotwPicks } from "@/lib/gotw";
import { getFavorites, toggleFavorite } from "@/lib/favorites";
import { getWatch, toggleWatch } from "@/lib/watchlist";
import { FILTERS, type Filter, groupByDay, loadView, myTeamGames, passes, POST, saveView, weekChips, weekValue } from "@/lib/filters";
import { matchGame } from "@/lib/search";
import type { GameSummary, Index, PlayerEntry, TeamInfo } from "@/lib/types";

export default function Home() {
  const [index, setIndex] = useState<Index | null>(null);
  const [season, setSeason] = useState<number | null>(null);
  const [games, setGames] = useState<GameSummary[]>([]);
  const [teams, setTeams] = useState<Record<string, TeamInfo>>({});
  const [gotw, setGotw] = useState<GotwPicks>({});
  const [shoot, setShoot] = useState<GotwPicks>({});
  const [players, setPlayers] = useState<PlayerEntry[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [watched, setWatched] = useState<number[]>([]);
  const [query, setQuery] = useState("");
  const [week, setWeek] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setFavorites(getFavorites());
    setWatched(getWatch());
    loadIndex()
      .then((ix) => {
        setIndex(ix);
        const saved = loadView();
        if (saved && ix.seasons.includes(saved.season)) {
          setSeason(saved.season);
          setWeek(saved.week);
          setFilter(saved.filter);
        } else {
          setSeason(ix.currentSeason);
          setWeek(ix.seasonType === "postseason" ? POST : String(ix.currentWeek));
        }
      })
      .catch(() => setError("Game data isn't available yet."));
    loadPlayers().then(setPlayers).catch(() => setPlayers([]));
  }, []);

  useEffect(() => {
    if (season === null) return;
    loadGames(season).then(setGames).catch(() => setError(`No games found for ${season}.`));
    loadTeams(season).then(setTeams);
    loadGotw(season).then(setGotw);
    loadShootout(season).then(setShoot);
  }, [season]);

  useEffect(() => {
    if (season !== null && week) saveView({ season, week, filter });
  }, [season, week, filter]);

  const currentWeek = index && season === index.currentSeason
    ? (index.seasonType === "postseason" ? POST : String(index.currentWeek)) : null;

  const chips = useMemo(
    () => weekChips(games).map((c) => (c.value === currentWeek && c.value !== POST ? { ...c, label: `Week ${c.value}` } : c)),
    [games, currentWeek],
  );

  const weekRow = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const row = weekRow.current;
    const on = row?.querySelector<HTMLElement>(".chip.on");
    if (row && on) row.scrollLeft = on.offsetLeft - row.offsetLeft - (row.clientWidth - on.clientWidth) / 2;
  }, [chips, week]);

  const searching = query.trim().length > 0;
  const visible = useMemo(
    () => games
      .filter((g) => searching || weekValue(g) === week)
      .filter((g) => passes(g, filter, favorites, watched))
      .filter((g) => matchGame(g, query, players)),
    [games, week, filter, favorites, watched, query, players, searching],
  );

  const myGames = useMemo(() => myTeamGames(games, week, favorites), [games, favorites, week]);

  const featured = searching ? null : gotwFor(gotw, week, games, filter, favorites);
  const shootout = searching ? null : pickFor(shoot, week, games, filter, favorites);

  const onToggle = (team: string) => setFavorites(toggleFavorite(team));
  const onWatch = (id: number) => setWatched(toggleWatch(id));
  const row = (g: GameSummary) => (
    <ScoreRow key={g.id} game={g} teams={teams} favorites={favorites} onToggle={onToggle} watched={watched.includes(g.id)} onWatch={onWatch} />
  );

  if (error && !index) return <p className="empty">{error}</p>;
  if (!index) return <p className="empty">Loading games…</p>;

  return (
    <>
      <div className="filters">
        <div className="chiprow" role="group" aria-label="Week" ref={weekRow}>
          {chips.map((c) => (
            <button key={c.value} className={`chip week ${c.value === week ? "on" : ""}`} aria-pressed={c.value === week}
              onClick={() => setWeek(c.value)}>{c.label}</button>
          ))}
          <select className="chip week" aria-label="Season" value={season ?? ""} onChange={(e) => setSeason(Number(e.target.value))}>
            {[...index.seasons].sort((a, b) => b - a).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <ChipRow label="Filter games" value={filter} onChange={(v) => setFilter(v as Filter)}
          chips={FILTERS.map((f) => (f.value === "mine" ? { ...f, icon: <Star className="icon sm" aria-hidden /> }
            : f.value === "watch" ? { ...f, icon: <Bell className="icon sm" aria-hidden /> } : f))} />
      </div>

      <input id="search" className="home-search" type="search" placeholder="Search a team, player or conference..."
        value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search games" />
      {searching && <p className="empty">Searching the whole {season} season.</p>}

      {featured && <GotwCard game={featured.game} why={featured.why} teams={teams} />}
      {shootout && <PickCard tag="Shootout of the Week" game={shootout.game} teams={teams} />}

      {!searching && favorites.length > 0 && myGames.length > 0 && filter === "all" && (
        <section id="my-teams">
          <div className="dayhead"><Star className="icon sm" aria-hidden fill="currentColor" /> My Teams</div>
          {myGames.map(row)}
        </section>
      )}

      <section id="games">
        {visible.length === 0 ? (
          <p className="empty">{filter === "mine" && favorites.length === 0 ? "Star a team to pin its games here."
            : filter === "watch" ? "Tap the bell on a game to add it to your watch list for this week." : "No games match."}</p>
        ) : (
          groupByDay(visible).map((d) => (
            <div key={d.day}>
              <div className="dayhead">{d.day}</div>
              {d.games.map(row)}
            </div>
          ))
        )}
      </section>
    </>
  );
}
