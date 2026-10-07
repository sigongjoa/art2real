"""AutoMate STEP → 부품별 STL (10-07).

앞 3000 조립만(assemblyId 순 · STEP 부품 4 개 이상). 부품마다 cadquery 로 면 나눔 → trimesh 검사.
작업자 4 · 작업자마다 cap(4 GB) · 파일당 60 s 넘으면 작업자를 죽이고 새로 띄운다(10-06 PC 다운).
남기는 것: 닫힘 · 면 12 이상 · 같은 모양(면 수·넓이·부피) 하나만 · 조립당 12 개 · 4 개 미만이면 폴더 지움.
첫 출현 위치(transform · m→mm)를 입혀 조립 자리를 유지한다.
저장: CAD조립/parts/automate_<id>/<순번>_<부품id끝>.stl · 진행은 parts/automate_log.jsonl(다시 돌리면 이어감).
돌리기: trail10_cadrille venv.
"""
import json, multiprocessing as mp, os, queue, shutil, sys, tempfile, time, zipfile
from pathlib import Path

sys.path.insert(0, "G:/art2real/트레일/trail11_zerotocad/s")
ROOT = Path(__file__).resolve().parents[1] / "out" / "레퍼런스" / "CAD조립"
SRC, OUT = ROOT / "automate", ROOT / "parts"
NASM, TRY, KEEP, MINP, TIMEOUT, W = 3000, 20, 12, 4, 60, 4


def do(job):
    # 부품 하나: STEP 바이트 → STL · (상태, 모양 지문)
    key, out, data, T = job
    import cadquery as cq, numpy as np, trimesh
    p = os.path.join(tempfile.gettempdir(), f"am_{os.getpid()}.step")
    with open(p, "wb") as f:
        f.write(data)
    s = cq.importers.importStep(p).val()
    bb = s.BoundingBox()
    tol = max(bb.DiagonalLength * 2e-3, 1e-3)  # 크기 비례 · 큰 부품이 수백만 면 되는 것 막기
    q = p[:-5] + ".stl"
    cq.exporters.export(s, q, tolerance=tol, angularTolerance=0.2)
    m = trimesh.load(q, force="mesh")
    if len(m.faces) < 12:
        return "면적음", None
    if not m.is_watertight:
        return "안닫힘", None
    T = np.array(T, float).reshape(4, 4); T[:3, 3] *= 1000  # 조립 transform 은 m · STEP 은 mm 로 읽힘
    m.apply_transform(T)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    m.export(out)
    return "ok", f"{len(m.faces)}_{m.area:.4g}_{abs(m.volume):.4g}"


def worker(i, inq, outq):
    from score import cap
    cap(4)
    while (job := inq.get()) is not None:
        try:
            r = do(job)
        except MemoryError:
            r = ("메모리", None)
        except Exception as e:
            r = ("오류:" + type(e).__name__, None)
        outq.put((i, job[0], *r))


def jobs(log):
    # 조립 json 을 id 순으로 읽어 앞 3000 개 · 부품은 앞 20 개까지 시도
    az, sz = zipfile.ZipFile(SRC / "assemblies.zip"), zipfile.ZipFile(SRC / "step.zip")
    steps = set(sz.namelist())
    names = sorted(n for n in az.namelist() if n.endswith(".json"))
    nasm = 0
    for n in names:
        a = json.loads(az.read(n))
        if a is None:  # ponytail: 빈 json 있음
            continue
        ps = [(k, x["id"]) for k, x in enumerate(a["parts"]) if f"step/{x['id']}.step" in steps]
        if len(ps) < MINP:
            continue
        nasm += 1
        if nasm > NASM:
            return
        first = {}
        for o in a["occurrences"]:
            first.setdefault(o["part"], o["transform"])
        aid = a["assemblyId"]
        for j, (k, pid) in enumerate(ps[:TRY]):
            stem = f"{j:02d}_{pid.split('_')[-1]}"
            key = f"{aid}/{stem}"  # 키 = 파일 이름
            if key in log:
                continue
            out = OUT / f"automate_{aid}" / f"{stem}.stl"
            yield key, str(out), sz.read(f"step/{pid}.step"), first.get(k, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    logp = OUT / "automate_log.jsonl"
    log = {}
    if logp.exists():
        for l in logp.read_text("utf-8").splitlines():
            r = json.loads(l); log[r["key"]] = r
    lf = open(logp, "a", encoding="utf-8")
    outq = mp.Queue()
    ws = {}

    def spawn(i):
        q = mp.Queue(); p = mp.Process(target=worker, args=(i, q, outq), daemon=True); p.start()
        ws[i] = {"p": p, "q": q, "job": None, "t": 0}

    def done(key, st, fp):
        r = {"key": key, "st": st, "fp": fp}; log[key] = r
        lf.write(json.dumps(r, ensure_ascii=False) + "\n"); lf.flush()

    for i in range(W):
        spawn(i)
    it, more, n, shown, t0 = jobs(log), True, 0, 0, time.time()
    while more or any(w["job"] for w in ws.values()):
        for i, w in ws.items():
            if w["job"] is None and more:
                j = next(it, None)
                if j is None:
                    more = False; continue
                w["job"], w["t"] = j[0], time.time(); w["q"].put(j)
        try:
            i, key, st, fp = outq.get(timeout=1)
            if ws[i]["job"] == key:
                ws[i]["job"] = None; done(key, st, fp); n += 1
        except queue.Empty:
            pass
        for i, w in list(ws.items()):
            if w["job"] and (time.time() - w["t"] > TIMEOUT or not w["p"].is_alive()):
                st = "시간초과" if w["p"].is_alive() else "죽음"
                w["p"].kill(); w["p"].join(); done(w["job"], st, None); n += 1; spawn(i)
        if n >= shown + 500:
            shown = n; print(f"{n} 부품 · {(time.time() - t0) / 60:.0f} 분", flush=True)
    for w in ws.values():
        w["q"].put(None)
    return log


def tidy(log):
    # 조립마다: 실패 · 같은 모양 지우고 12 개까지 · 4 개 미만이면 폴더째 지움
    by = {}
    for k, r in log.items():
        by.setdefault(k.split("/")[0], []).append(r)
    keep = 0
    for aid, rs in by.items():
        d = OUT / f"automate_{aid}"
        if not d.exists():
            continue
        seen, ok = set(), []
        files = sorted(d.glob("*.stl"))
        fp = {r["key"].split("/")[1]: r["fp"] for r in rs if r["st"] == "ok"}
        for f in files:
            h = fp.get(f.stem)
            if h is None or h in seen or len(ok) >= KEEP:
                f.unlink(); continue
            seen.add(h); ok.append(f)
        if len(ok) < MINP:
            shutil.rmtree(d)
        else:
            keep += 1
    from collections import Counter
    print("상태:", dict(Counter(r["st"] for r in log.values())))
    print("남은 조립:", keep)


if __name__ == "__main__":
    tidy(run())
