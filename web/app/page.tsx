"use client";

import { useEffect, useMemo, useState } from "react";
import GameRow from "@/components/GameRow";
import { loadGames, loadIndex, loadPlayers } from "@/lib/data";
import { getFavorites, toggleFavorite } from "@/lib/favorites";
import { matchGame } from "@/lib/search";
import type { GameSummary, Index, PlayerEntry } from "@/lib/types";

const POST = "post";

function weekValue(g: GameSummary): string {
  return g.seasonType === "postseason" ? POST : String(g.week);
}

function byKickoff(a: GameSummary, b: GameSummary): number {
  return a.start.localeCompare(b.start) || a.id - b.id;
}

export default function Home() {
  const [index, setIndex] = useState<Index | null>(null);
  const [season, setSeason] = useState<number | null>(null);
  const [games, setGames] = useState<GameSummary[]>([]);
  const [players, setPlayers] = useState<PlayerEntry[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [week, setWeek] = useState<string>("");
  const [conf, setConf] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setFavorites(getFavorites());
    loadIndex()
      .then((ix) => {
        setIndex(ix);
        setSeason(ix.currentSeason);
        setWeek(ix.seasonType === "postseason" ? POST : String(ix.currentWeek));
      })
      .catch(() => setError("Game data isn't available yet."));
    loadPlayers().then(setPlayers).catch(() => setPlayers([]));
  }, []);

  useEffect(() => {
    if (season === null) return;
    loadGames(season).then(setGames).catch(() => setError(`No games found for ${season}.`));
  }, [season]);

  const weeks = useMemo(() => {
    const regular = [...new Set(games.filter((g) => g.seasonType === "regular").map((g) => g.week))].sort((a, b) => a - b);
    const hasPost = games.some((g) => g.seasonType === "postseason");
    return [...regular.map(String), ...(hasPost ? [POST] : [])];
  }, [games]);

  const conferences = useMemo(() => {
    const all = new Set<string>();
    games.forEach((g) => { if (g.homeConf) all.add(g.homeConf); if (g.awayConf) all.add(g.awayConf); });
    return [...all].sort();
  }, [games]);

  const searching = query.trim().length > 0;

  const visible = useMemo(
    () =>
      games
        .filter((g) => searching || !week || weekValue(g) === week)
        .filter((g) => !conf || g.homeConf === conf || g.awayConf === conf)
        .filter((g) => matchGame(g, query, players))
        .sort(byKickoff),
    [games, week, conf, query, players, searching],
  );

  const myGames = useMemo(() => {
    if (!index || season !== index.currentSeason) return [];
    const current = index.seasonType === "postseason" ? POST : String(index.currentWeek);
    return games
      .filter((g) => weekValue(g) === current)
      .filter((g) => favorites.includes(g.home) || favorites.includes(g.away))
      .sort(byKickoff);
  }, [games, favorites, index, season]);

  const onToggle = (team: string) => setFavorites(toggleFavorite(team));

  if (error && !index) return <p className="muted">{error}</p>;
  if (!index) return <p className="muted">Loading games…</p>;

  return (
    <>
      <section id="my-teams">
        <h2>★ My Teams</h2>
        {favorites.length === 0 ? (
          <p className="muted">Star a team to pin its games here.</p>
        ) : myGames.length === 0 ? (
          <p className="muted">None of your teams play this week.</p>
        ) : (
          <div>{myGames.map((g) => <GameRow key={g.id} game={g} favorites={favorites} onToggle={onToggle} />)}</div>
        )}
      </section>

      <section id="games">
        <h2>All games</h2>
        <input
          type="search"
          placeholder="Search a team, player or conference..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search games"
        />
        <div className="controls">
          <select aria-label="Season" value={season ?? ""} onChange={(e) => setSeason(Number(e.target.value))}>
            {[...index.seasons].sort((a, b) => b - a).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select aria-label="Week" value={week} onChange={(e) => setWeek(e.target.value)} disabled={searching}>
            <option value="">All weeks</option>
            {weeks.map((w) => <option key={w} value={w}>{w === POST ? "Bowls / Playoff" : `Week ${w}`}</option>)}
          </select>
          <select aria-label="Conference" value={conf} onChange={(e) => setConf(e.target.value)}>
            <option value="">All conferences</option>
            {conferences.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        {searching && <p className="muted">Searching the whole {season} season.</p>}
        {visible.length === 0 ? (
          <p className="muted">No games match.</p>
        ) : (
          <div>{visible.map((g) => <GameRow key={g.id} game={g} favorites={favorites} onToggle={onToggle} />)}</div>
        )}
      </section>
    </>
  );
}
