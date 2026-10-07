"""사람이 나눈 출력용 메카 3D 를 Printables 에서 받는다 (10-05).

후보: claudedocs/후보_사람분할3D_20261005.md · 개인 연구용 · 재배포 · 커밋 금지.
저장: 원화3d/out/레퍼런스/사람분할/<id>_<짧은이름>/ + 출처.json · 끝에 목록.json.
받는 법: GraphQL print(id) 로 파일 목록 → getDownloadLink(fileType:stl|other) → 파일마다 받음.
다시 돌리면 크기가 같은 파일은 건너뛴다. 끝에 trimesh 로 모델마다 STL 3 개 load.
"""
import json, re, shutil, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://api.printables.com/graphql/"
ROOT = Path(__file__).resolve().parents[1] / "out" / "레퍼런스" / "사람분할"
MAX = 500 * 2**20
EXT = (".stl", ".3mf", ".obj")
HEAD = re.compile(r"head|helmet|face|horn|visor|antenna|jaw|eye|mask|crest|chin|forehead|vfin|v.fin|vulcan|ear|crown|skull|cheek|mouth|teeth", re.I)

# (id, 짧은이름) — 상위 10 · 예비 3 · 나머지는 머리 조각 많은 순 · G1 은 셋만
MODELS = [
    (1426030, "EVA01흉상"), (932257, "RX78머리"), (678249, "고릴라기사"), (885858, "EVA00_D13"),
    (924146, "EVA01_D13"), (674707, "기사_D13"), (1306918, "걸프라빈인형"), (1168517, "Zodiarks_Leo"),
    (1327052, "TF코스프레헬멧"), (1523169, "패트레이버헬다이버"),
    (153476, "MechaWarrior01"), (334966, "메가트론키트"), (1630920, "블랙나이트_D13"),
    (624957, "볼트론"), (516327, "EZinMoov머리"), (57160, "만달로리안분할"), (1280672, "RobotHead2"),
    (892338, "Gladiosmech"), (334967, "옵티머스키트"), (46310, "G1옵티머스"), (46313, "G1범블비"),
    (46318, "G1라쳇"), (113294, "만달로리안핀"), (1223729, "REPO로봇"), (400101, "폴아웃로봇"),
    (335719, "스타스크림키트"), (910221, "EVA02_D13"), (1640140, "RX78_2"), (27107, "툰로봇"),
    (981111, "Dummy13"), (251907, "Stray로봇머리"),
    # 10-05 「모두 받아봐」 — 후보 표 나머지 전부
    (1021397, "폴아웃X01흉상"), (890972, "EVA0304_D13"), (813280, "건담_D13"), (982988, "건담D13완성"),
    (864699, "D13건담옷"), (1286204, "T800_D13"), (1038885, "베르세르크13"), (1177517, "헤일로스파르탄_D13"),
    (1837784, "DVa메카_D13"), (680191, "Sisters13"), (1572649, "CARBON13M"), (1172932, "BattleMech_Goliath"),
    (1192644, "BattleMech_Predator"), (495843, "Ulfberhtmech"), (1211381, "MWO_Linebacker"),
    (1402376, "콘치로봇"), (807598, "마징가Z"), (46446, "G1클리프점퍼"), (70938, "G1프라울"),
    (70939, "G1블루스트릭"), (70940, "G1재즈"), (70941, "G1하운드"), (70946, "G1사이드스와이프"), (70953, "G1킥백"),
]


def retry(fn):
    # ponytail: 고정 백오프 · 429 · 연결 끊김만 다시
    def w(*a):
        for i in range(6):
            try:
                return fn(*a)
            except Exception as e:
                if i == 5 or not ("429" in str(e) or "10054" in str(e) or "timed out" in str(e)):
                    raise
                time.sleep(60 * (i + 1))
    return w


@retry
def gql(q):
    time.sleep(2)  # API 는 IP 당 429 를 준다 · 파일 CDN 은 안 막힘
    req = urllib.request.Request(API, json.dumps({"query": q}).encode(), {"content-type": "application/json", "user-agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if "errors" in d:
        raise RuntimeError(d["errors"])
    return d["data"]


def info(pid):
    return gql(f'query{{ print(id:"{pid}"){{ id name license{{name}} user{{publicUsername}} premium price '
               f'stls{{id name fileSize}} otherFiles{{id name fileSize}} downloadPacks{{id fileSize fileType}} }} }}')["print"]


def link(fid, pid, kind):
    r = gql(f'mutation{{ getDownloadLink(id:"{fid}", printId:"{pid}", fileType:{kind}, source:model_detail){{ ok output{{ link }} errors{{messages}} }} }}')["getDownloadLink"]
    if not r["ok"]:
        raise RuntimeError(r["errors"])
    return r["output"]["link"]


def safe(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .") or "file"


@retry
def fetch(job):
    pid, f, kind, path = job
    if path.exists() and path.stat().st_size == f["fileSize"]:
        return path
    url = link(f["id"], pid, kind)
    req = urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        path.write_bytes(r.read())
    return path


def one(pid, short):
    d = ROOT / f"{pid}_{short}"
    if (d / "출처.json").exists():  # 받은 폴더는 API 안 부름
        src = json.loads((d / "출처.json").read_text(encoding="utf-8"))
        names = [x.name for x in d.iterdir() if x.suffix.lower() in EXT]
        return {"id": pid, "이름": src["이름"], "라이선스": src["라이선스"],
                "크기MB": round(sum(x.stat().st_size for x in d.iterdir()) / 2**20, 1),
                "폴더": str(d.relative_to(ROOT.parents[2])), "파일수": len(names),
                "머리관련파일수": sum(bool(HEAD.search(n)) for n in names), "상태": "받음"}
    p = info(pid)
    if p is None:
        return {"id": pid, "이름": short, "상태": "없음(삭제 · 비공개)"}
    row = {"id": pid, "이름": p["name"], "라이선스": p["license"]["name"] if p["license"] else None}
    if p.get("premium") or (p.get("price") or 0) > 0:
        return {**row, "상태": "건너뜀: 유료"}
    files = [(f, "stl") for f in p["stls"]] + [(f, "other") for f in p["otherFiles"]]
    files = [(f, k) for f, k in files if f["name"].lower().endswith(EXT)]
    size = sum(f["fileSize"] for f, _ in files)
    row["크기MB"] = round(size / 2**20, 1)
    if size > MAX:
        return {**row, "상태": "건너뜀: 500MB 넘음"}
    d.mkdir(parents=True, exist_ok=True)
    pack = next((k for k in p.get("downloadPacks") or [] if k["fileType"] == "MODEL_FILES"), None)
    if pack and pack["fileSize"] < 2 * MAX:
        names = unpack(link(pack["id"], pid, "pack"), d)
    else:
        names = per_file(pid, files, d)
    (d / "출처.json").write_text(json.dumps({
        "이름": p["name"], "url": f"https://www.printables.com/model/{pid}", "작가": p["user"]["publicUsername"],
        "라이선스": row["라이선스"], "받은날": time.strftime("%Y-%m-%d"), "파일수": len(names),
        "메모": "개인 연구용 · 재배포 금지 · 원작 IP 팬아트"}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {**row, "폴더": str(d.relative_to(ROOT.parents[2])), "파일수": len(names),
            "머리관련파일수": sum(bool(HEAD.search(n)) for n in names), "상태": "받음"}


@retry
def unpack(url, d):
    """모델 zip 하나(API 1 회) → STL · 3MF · OBJ 만 평평하게 푼다."""
    tmp = d / "_pack.zip"
    req = urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    names, seen = [], set()
    with zipfile.ZipFile(tmp) as z:
        for m in z.infolist():
            if m.is_dir() or not m.filename.lower().endswith(EXT):
                continue
            n = safe(m.filename.rsplit("/", 1)[-1])
            if n.lower() in seen:
                n = safe(m.filename.replace("/", "_"))
            seen.add(n.lower())
            with z.open(m) as a, open(d / n, "wb") as b:
                shutil.copyfileobj(a, b)
            names.append(n)
    tmp.unlink()
    return names


def per_file(pid, files, d):
    jobs, seen = [], set()
    for f, k in files:
        n = safe(f["name"])
        if n.lower() in seen:
            n = f"{f['id']}_{n}"
        seen.add(n.lower())
        jobs.append((pid, f, k, d / n))
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(fetch, jobs))
    return [j[3].name for j in jobs]


def check(row):
    import trimesh
    d = ROOT.parents[2] / row["폴더"]
    stls = sorted(d.glob("*.stl"), key=lambda p: p.stat().st_size)[:3] or sorted(d.glob("*.3mf"))[:2]
    faces = []
    for s in stls:
        try:
            m = trimesh.load(s, force="mesh")
            faces.append(len(m.faces))
        except Exception as e:
            faces.append(f"오류 {e}")
    return faces


if __name__ == "__main__":
    assert safe('a:b?.stl') == "a_b_.stl" and HEAD.search("Upper Jaw v3.stl") and not HEAD.search("leg.stl")
    if len(sys.argv) > 1:   # 10-07: 에이전트 후보 json 들(id · short) — 이미 받은 폴더는 one() 이 건너뜀 · 목록.json 은 전부 다시 씀
        MODELS += [(int(c["id"]), safe(str(c["short"]))[:20]) for f in sys.argv[1:] for c in json.load(open(f, encoding="utf-8"))]
        MODELS = list(dict(MODELS).items())
    rows = []
    for pid, short in MODELS:
        try:
            row = one(pid, short)
        except Exception as e:
            row = {"id": pid, "이름": short, "상태": f"실패: {e}"[:300]}
        if row["상태"] == "받음":
            row["열기확인_면수"] = check(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        rows.append(row)
    (ROOT / "목록.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
