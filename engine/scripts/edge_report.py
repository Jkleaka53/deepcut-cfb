"""Old vs new edge labels over finished games: `uv run python scripts/edge_report.py OLD_DIR NEW_DIR OUT_MD`.
OLD_DIR / NEW_DIR are season folders (holding matchups/*.json)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXAMPLES = [("Missouri", "Ole Miss", 7), ("Florida", "Missouri", 5), ("Texas A&M", "LSU", 4)]
BANDS = ("even", "slight", "clear")


def load(d: Path) -> dict[int, dict]:
    return {int(f.stem): json.loads(f.read_text()) for f in (d / "matchups").glob("*.json")}


def finished(m: dict) -> bool:
    g = m["game"]
    return bool(g.get("completed")) and g.get("homePoints") is not None and bool(m.get("swing"))


def winner(g: dict) -> str | None:
    if g["homePoints"] == g["awayPoints"]:
        return None
    return g["home"] if g["homePoints"] > g["awayPoints"] else g["away"]


def summarize(ms: list[dict]) -> dict:
    out = {b: {"games": 0, "fav": 0, "favWon": 0, "blowouts": 0} for b in BANDS}
    for m in ms:
        o = m["swing"].get("overallEdge")
        if not o:
            continue
        g, r = m["game"], out[o["edge"]]
        r["games"] += 1
        r["blowouts"] += abs(g["homePoints"] - g["awayPoints"]) >= 21
        if o["team"]:
            r["fav"] += 1
            r["favWon"] += winner(g) == o["team"]
    return out


def contradictions(m: dict) -> list[str]:
    bad = []
    for sec in m["sections"]:
        for units_key, edge_key, verb in (("units", "edge", "passes"), ("runUnits", "runEdge", "runs")):
            e = sec.get(edge_key)
            if not e or e == "even":
                continue
            side = e.split("-")[1]
            rows = [r["edge"] for u in sec.get(units_key) or [] for r in u["rows"] if r.get("edge") and r["edge"] != "even"]
            other = sum(1 for x in rows if not x.endswith(side))
            if rows and other > len(rows) / 2:
                g = m["game"]
                bad.append(f"wk {g['week']} {g['away']} at {g['home']}: when {sec['offenseTeam']} {verb}, label {e} "
                           f"but {other}/{len(rows)} rows lean the other way")
    return bad


def pct(a: int, b: int) -> str:
    return f"{a / b:.0%}" if b else "n/a"


def main(old_dir: str, new_dir: str, out_md: str) -> None:
    old, new = load(Path(old_dir)), load(Path(new_dir))
    ids = [i for i in new if i in old and finished(new[i]) and finished(old[i])]
    so, sn = summarize([old[i] for i in ids]), summarize([new[i] for i in ids])
    lines = [f"# Edge score report (2026 finished games: {len(ids)})", "",
             "| Label | Old games | New games | Old: favored won | New: favored won | Old: decided by 21+ | New: decided by 21+ |",
             "|---|---|---|---|---|---|---|"]
    for b in BANDS:
        o, n = so[b], sn[b]
        name = {"clear": "Big"}.get(b, b.capitalize())
        lines.append(f"| {name} | {o['games']} | {n['games']} | {pct(o['favWon'], o['fav'])} ({o['favWon']}/{o['fav']}) | "
                     f"{pct(n['favWon'], n['fav'])} ({n['favWon']}/{n['fav']}) | {pct(o['blowouts'], o['games'])} | "
                     f"{pct(n['blowouts'], n['games'])} |")
    total_sections = sum(1 for i in ids for s in new[i]["sections"] for k in ("edge", "runEdge")
                         if s.get(k) and s[k] != "even")
    bad = [b for i in ids for b in contradictions(new[i])]
    lines += ["", f"Section labels that lean against most of their own table: {len(bad)} of {total_sections} "
              f"({pct(len(bad), total_sections)})."]
    if total_sections and len(bad) / total_sections > 0.05:
        lines += [""] + [f"- {b}" for b in bad]
    lines += ["", "## Spec examples", ""]
    for away, home, wk in EXAMPLES:
        for i in ids:
            g = new[i]["game"]
            if g["away"] == away and g["home"] == home and g["week"] == wk:
                oo, on = old[i]["swing"]["overallEdge"], new[i]["swing"]["overallEdge"]
                lines.append(f"- {away} at {home} (wk {wk}, final {g['awayPoints']}-{g['homePoints']}): "
                             f"old {oo['edge']}{' ' + oo['team'] if oo['team'] else ''}; "
                             f"new {on['edge']}{' ' + on['team'] if on['team'] else ''} {on['score']}")
    Path(out_md).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:4])
