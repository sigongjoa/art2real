"""Fusion 360 Gallery Assembly → 부품별 STL (10-07).

입력: CAD조립/fusion_assembly/풀기/<조립>/ (7z 에서 *.obj · *.json 만 푼 것 · assembly.obj 는 뺌).
몸체 OBJ 는 컴포넌트 좌표 → 트리를 내려가며 occurrence transform 을 곱해 조립 자리에 놓는다(공식 assembly_graph 와 같은 식).
OBJ 는 B-rep 면마다 꼭짓점이 따로라 그대로는 10 % 만 닫힘 → 꼭짓점 1e-5 cm 로 합치면 95 %.
남기는 것: 보이는 몸체 · 닫힘 · 면 12 이상 · 같은 몸체(uuid)·같은 모양(면 수·넓이·부피) 하나만 · 12 개까지 · 4 개 미만이면 안 씀.
단위 cm 그대로. 저장: CAD조립/parts/fusion_<조립>/<순번>_<occurrence>_<몸체>.stl · 진행은 parts/fusion_log.jsonl.
돌리기: trail10_cadrille venv · 작업자 4 · cap(4 GB).
"""
import json, re, shutil, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, "G:/art2real/트레일/trail11_zerotocad/s")
ROOT = Path(__file__).resolve().parents[1] / "out" / "레퍼런스" / "CAD조립"
SRC, OUT = ROOT / "fusion_assembly" / "풀기", ROOT / "parts"
KEEP, MINP, TRY = 12, 4, 40


def mat(t):
    import numpy as np
    if t is None:
        return np.eye(4)
    v = lambda k, h: [t[k]["x"], t[k]["y"], t[k]["z"], h]
    return np.array([v("x_axis", 0), v("y_axis", 0), v("z_axis", 0), v("origin", 1)]).T


def bodies(a):
    # (몸체 uuid, 이름, 4x4) 를 트리 순서로 · 숨긴 것 뺌
    import numpy as np
    out = [(b, "root", np.eye(4)) for b, x in (a["root"].get("bodies") or {}).items() if x.get("is_visible", True)]
    occs = a.get("occurrences") or {}

    def walk(tree, T):
        for u, sub in tree.items():
            o = occs[u]
            if not o.get("is_visible", True):
                continue
            M = T @ mat(o.get("transform"))
            out.extend((b, o["name"], M) for b, x in (o.get("bodies") or {}).items() if x.get("is_visible", True))
            walk(sub, M)
    walk((a.get("tree") or {}).get("root") or {}, np.eye(4))
    return out


def one(d):
    import trimesh
    a = json.loads((d / "assembly.json").read_text("utf-8"))
    names = {k: v.get("name", "body") for k, v in (a.get("bodies") or {}).items()}
    seen, fps, got, st = set(), set(), [], {}
    for b, oname, M in bodies(a)[:TRY * 3]:
        if b in seen or len(got) >= KEEP or len(seen) >= TRY:
            continue
        seen.add(b)
        f = d / f"{b}.obj"
        if not f.exists():
            st["없음"] = st.get("없음", 0) + 1; continue
        try:
            m = trimesh.load(f, force="mesh")
            m = trimesh.Trimesh(m.vertices, m.faces)  # 법선 · UV 를 버려야 꼭짓점이 합쳐진다
            m.merge_vertices(digits_vertex=5); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
        except Exception:
            st["오류"] = st.get("오류", 0) + 1; continue
        if len(m.faces) < 12:
            st["면적음"] = st.get("면적음", 0) + 1; continue
        if not m.is_watertight:
            st["안닫힘"] = st.get("안닫힘", 0) + 1; continue
        fp = f"{len(m.faces)}_{m.area:.4g}_{abs(m.volume):.4g}"
        if fp in fps:
            st["같은모양"] = st.get("같은모양", 0) + 1; continue
        fps.add(fp)
        m.apply_transform(M)
        stem = re.sub(r"[^\w\-]+", "-", f"{len(got):02d}_{oname}_{names.get(b, 'body')}")[:60]
        got.append((stem, m))
    if len(got) >= MINP:
        o = OUT / f"fusion_{d.name}"
        shutil.rmtree(o, ignore_errors=True)  # 다시 돌릴 때 옛 판이 섞이지 않게
        o.mkdir(parents=True, exist_ok=True)
        for stem, m in got:
            m.export(o / f"{stem}.stl")
    return d.name, len(got), st


def safe(d):
    try:
        return one(d)
    except Exception as e:  # MemoryError 포함 · 조립 하나만 버린다
        return d.name, 0, {"실패": type(e).__name__}


def init():
    from score import cap
    cap(4)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    logp = OUT / "fusion_log.jsonl"
    done = {json.loads(l)["asm"] for l in logp.read_text("utf-8").splitlines()} if logp.exists() else set()
    todo = sorted(d for d in SRC.iterdir() if (d / "assembly.json").exists() and d.name not in done)
    print("할 조립", len(todo), flush=True)
    with open(logp, "a", encoding="utf-8") as lf, ProcessPoolExecutor(4, initializer=init) as ex:
        for k, (name, n, st) in enumerate(ex.map(safe, todo, chunksize=4)):
            lf.write(json.dumps({"asm": name, "parts": n, "st": st}, ensure_ascii=False) + "\n"); lf.flush()
            if k % 200 == 0:
                print(k, name, n, st, flush=True)
    print("끝", flush=True)
