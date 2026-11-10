"""Throwaway spike: what does the free CFBD data support? Run: uv run python spike/pressure_spike.py"""
import collections, json, os, re
from pathlib import Path
from cfbm.cfbd_client import CfbdClient

ROOT = Path(__file__).resolve().parents[2]
key = os.environ.get("CFBD_API_KEY") or dict(l.split("=", 1) for l in (ROOT / ".env").read_text().split() if "=" in l)["CFBD_API_KEY"]
c = CfbdClient(key, ROOT / "engine/.cache")
OUT = ROOT / "engine/spike/out"; OUT.mkdir(exist_ok=True)

plays = []
for wk in (5, 6, 7):
    plays += c.get("/plays", {"year": 2025, "week": wk, "seasonType": "regular"})
print("plays:", len(plays))
print("keys:", sorted(plays[0].keys()))
types = collections.Counter(p["playType"] for p in plays)
print("\nplayType counts:"); [print(f"  {n:6d} {t}") for t, n in types.most_common()]

# scores: look at a touchdown play and the play after it
tds = [p for p in plays if p.get("scoring") and "Touchdown" in p["playType"]][:3]
for td in tds:
    print("\nTD:", td["playType"], "offScore", td["offenseScore"], "defScore", td["defenseScore"], "|", td["playText"][:90])
    same = sorted([p for p in plays if p["gameId"] == td["gameId"]], key=lambda p: int(p["id"]))
    i = [p["id"] for p in same].index(td["id"])
    for nx in same[i-1:i+3]:
        print("   ", nx["offense"], nx["offenseScore"], "-", nx["defense"], nx["defenseScore"], nx["playType"], "|", nx["playText"][:60])

rush = [p for p in plays if p["playType"] in ("Rush", "Rushing Touchdown")]
scr = [p for p in rush if re.search(r"scrambl", p["playText"] or "", re.I)]
teams_with_scr = {p["offense"] for p in scr}
print(f"\nrush plays {len(rush)}, 'scramble' in text {len(scr)}, offenses with any {len(teams_with_scr)} of {len({p['offense'] for p in plays})}")
print("scramble examples:", [p["playText"][:80] for p in scr[:3]])
inc = [p for p in plays if p["playType"] == "Pass Incompletion"]
thr = [p for p in inc if re.search(r"thrown away|throw ?away|threw it away", p["playText"] or "", re.I)]
print(f"incompletions {len(inc)}, throwaway text {len(thr)}", [p["playText"][:80] for p in thr[:2]])
gr = [p for p in plays if re.search(r"grounding", p["playText"] or "", re.I)]
print("grounding:", len(gr), collections.Counter(p["playType"] for p in gr), [p["playText"][:80] for p in gr[:2]])
print("ppa null share:", sum(p.get("ppa") is None for p in plays) / len(plays))
print("sample sack text:", [p["playText"][:80] for p in plays if p["playType"] == "Sack"][:3])

box = c.get("/games/players", {"year": 2025, "week": 5, "seasonType": "regular", "category": "passing"})
(OUT / "box_week5.json").write_text(json.dumps(box[:3], indent=1))
print("\nbox games:", len(box), "first team keys:", list(box[0]["teams"][0].keys()))
print("passing stat names:", [s["name"] for s in box[0]["teams"][0]["categories"][0]["types"]])

adv = c.get("/stats/game/advanced", {"year": 2025, "week": 5})
print("\nadvanced game offense keys:", sorted(adv[0]["offense"].keys()))
ppa = c.get("/ppa/players/games", {"year": 2025, "week": 5, "position": "QB"})
print("ppa player game keys:", sorted(ppa[0].keys()), "avgPPA keys:", sorted(ppa[0].get("averagePPA", {}).keys()))

sadv = c.get("/stats/season/advanced", {"year": 2025})
print("\nseason adv defense havoc:", sadv[0]["defense"].get("havoc"))

for yr, team in ((2024, "Washington State"), (2025, "Oklahoma")):
    b = c.get("/games/players", {"year": yr, "team": team, "category": "passing", "seasonType": "regular"})
    ath = collections.Counter()
    for g in b:
        for t in g["teams"]:
            if t["team"] != team: continue
            for cat in t["categories"]:
                for ty in cat["types"]:
                    if ty["name"] == "C/ATT":
                        for a in ty["athletes"]: ath[(a["id"], a["name"])] += 1
    print(f"{yr} {team} passers:", ath.most_common(3))

post = c.get("/games", {"year": 2024, "seasonType": "postseason"})
print("\npostseason weeks:", collections.Counter(g["week"] for g in post), "game keys:", sorted(post[0].keys()))
fbs = c.get("/teams/fbs", {"year": 2025})
print("fbs teams 2025:", len(fbs))
print("\ncalls_made:", c.calls_made)
