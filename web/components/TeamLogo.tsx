"use client";

import { useState } from "react";
import { logoPath } from "@/lib/logos";
import type { TeamInfo } from "@/lib/types";

interface Props { team: TeamInfo | undefined; name: string; size?: number; tile?: boolean }

/** Team logo (light and dark versions swap with the theme in CSS). Falls back to an abbreviation tile. */
export default function TeamLogo({ team, name, size = 26, tile = false }: Props) {
  const [broken, setBroken] = useState(false);
  const light = logoPath(team, "light");
  const dark = logoPath(team, "dark");
  const box = { width: size, height: size };
  if (broken || !light) {
    return (
      <span className="logo-fallback" style={{ ...box, background: team?.fill ?? "var(--ink)", fontSize: size * 0.38 }} aria-label={`${name} logo`}>
        {team?.abbr ?? name.slice(0, 3).toUpperCase()}
      </span>
    );
  }
  return (
    <span className={tile ? "logo-tile" : "logo-plain"} style={tile ? { width: size * 1.35, height: size * 1.35 } : box}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="lg-light" src={light} alt={`${name} logo`} style={box} onError={() => setBroken(true)} />
      {dark && dark !== light && !tile && (
        // eslint-disable-next-line @next/next/no-img-element
        <img className="lg-dark" src={dark} alt="" aria-hidden style={box} onError={() => setBroken(true)} />
      )}
    </span>
  );
}
