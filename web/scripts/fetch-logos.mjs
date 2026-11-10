// Prebuild: download each FBS team's logos (light + dark) into public/logos. Git-ignored, never committed.
// Always exits 0: a failed download only means that team shows its abbreviation tile instead.
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;
const dataDir = join(root, "public", "data");
const outDir = join(root, "public", "logos");
mkdirSync(join(outDir, "dark"), { recursive: true });

const jobs = new Map();
for (const season of existsSync(dataDir) ? readdirSync(dataDir) : []) {
  const f = join(dataDir, season, "teams.json");
  if (!existsSync(f)) continue;
  for (const t of JSON.parse(readFileSync(f, "utf8"))) {
    if (t.id == null) continue;
    if (t.logo) jobs.set(join(outDir, `${t.id}.png`), t.logo);
    if (t.logoDark) jobs.set(join(outDir, "dark", `${t.id}.png`), t.logoDark);
  }
}

let ok = 0, failed = 0, skipped = 0;
async function one([dest, url]) {
  if (existsSync(dest)) { skipped++; return; }
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
    if (!res.ok) throw new Error(String(res.status));
    writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
    ok++;
  } catch {
    failed++;
  }
}
const list = [...jobs];
for (let i = 0; i < list.length; i += 8) await Promise.all(list.slice(i, i + 8).map(one));
console.log(`logos: ${ok} downloaded, ${skipped} already present, ${failed} failed`);
process.exit(0);
