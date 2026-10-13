"""새 검증용 사람분할 모델 후보 — Printables 검색 · 규칙으로만 고름(사람 눈 안 씀) · 10-13
python 새후보.py → 새후보.json [{id, short}] (사람분할받기.py 인자로)
규칙: 이름에 주제어(로봇 · 메카 · 건담 · 트랜스포머 · 아머 · 피규어) 있고 액세서리어(받침 · 거치 · 무기 · 손 · 공구 등) 없음 · 이미 받은 id 제외 · 무료 · STL/3MF/OBJ 8 개 이상 · 합 ≤ 300 MB · 씨앗 20261015 로 섞어 앞에서 30 개"""
import json, random, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "실험_20261001"))
import 사람분할받기 as B
Q = ["articulated mech", "robot action figure", "mecha model kit", "gundam", "transformers", "battlemech",
     "articulated robot", "power armor", "mech kit", "poseable robot", "mecha figure", "robot kit"]
주제 = re.compile(r"robot|mech|gundam|transformer|armou?r|figure|zaku|android|cyborg|droid", re.I)
빼기 = re.compile(r"stand|base|holder|display|enclosure|workstation|cooz|sprue|plaque|lamp|keycap|grommet|tap|hand|swimmer|repair|building|fidget|weapon|guns?|sword|box|xrp|otto|dice|sign|logo|ornament|cookie|cutter", re.I)
있음 = {int(d.name.split("_")[0]) for d in B.ROOT.iterdir() if d.is_dir() and d.name.split("_")[0].isdigit()}
ids = {}
for q in Q:
    for it in B.gql(f'query{{ searchPrints2(query:"{q}", limit:60){{ items{{ id name }} }} }}')["searchPrints2"]["items"]:
        if int(it["id"]) not in 있음 and 주제.search(it["name"]) and not 빼기.search(it["name"]): ids[int(it["id"])] = it["name"]
print("검색 새 id", len(ids), flush=True)
후보 = sorted(ids); random.Random(20261015).shuffle(후보); out = []
for pid in 후보:
    if len(out) == 30: break
    try: p = B.info(pid)
    except Exception as e: print(pid, "오류", e); continue
    if p is None or p.get("premium") or (p.get("price") or 0) > 0: continue
    fs = [f for f in p["stls"] + p["otherFiles"] if f["name"].lower().endswith(B.EXT)]
    if len(fs) < 8 or sum(f["fileSize"] for f in fs) > 300 * 2**20: continue
    short = re.sub(r"[^0-9A-Za-z가-힣]", "", p["name"])[:20] or str(pid)
    out.append({"id": pid, "short": short}); print(len(out), pid, p["name"][:60], len(fs), flush=True)
json.dump(out, open(Path(__file__).with_name("새후보.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
