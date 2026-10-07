# -*- coding: utf-8 -*-
"""수확 · 정제 코드를 모양 자 묶음으로 다시 매긴다 (10-07)
통과 = IoU ≥ 0.8 · 위상(덩어리 · 관통 구멍 수) 같음 · 모서리 F1 ≥ 0.5 (모서리 문턱은 비교 그림 6 개로 잡은 잠정값 — 그림으로 더 확인)
python s0/다시채점.py <입력 jsonl(결과 · 정제)> <출력 jsonl> [일꾼=4]  — 이어서 돌릴 수 있음"""
import os, sys, json, tempfile, trimesh
from concurrent.futures import ProcessPoolExecutor, as_completed
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
통과 = lambda m: m["iou"] >= 0.8 and m["위상같음"] and m["edge_f1"] >= 0.5

def 일꾼(args):
    name, codes = args
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(H)), "trail11_zerotocad", "s"))
    from score import cap; cap()
    import cadquery as cq, s0 as S
    from 모양자 import 재기
    gt = S.unit(trimesh.load(R + name, force="mesh")); gt.apply_translation([-0.5] * 3); gt.apply_scale(2.0)
    out = []
    for c in codes:
        try:
            ns = {"cq": cq}; exec(c, ns)
            obj = ns.get("r") or next(v for v in ns.values() if isinstance(v, cq.Workplane)); p = os.path.join(tempfile.gettempdir(), "다시_%d.stl" % os.getpid())
            cq.exporters.export(obj, p); m = trimesh.load(p); m.apply_scale(1 / 100.0); r = 재기(m, gt); r["통과"] = 통과(r); out.append(r)
        except Exception:
            out.append(None)
    return {"부품": name, "자": out}

if __name__ == "__main__":
    src, O = sys.argv[1], sys.argv[2]; NW = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    done = {json.loads(l)["부품"] for l in open(O, encoding="utf-8")} if os.path.exists(O) else set()
    jobs = []
    for l in open(src, encoding="utf-8"):
        r = json.loads(l)
        if r["부품"] in done: continue
        codes = [c for (m, c), v in zip(r["코드들"], r["IoU"]) if v >= 0.4] if "코드들" in r else ([r["코드"]] if r.get("코드") else [])
        if codes: jobs.append((r["부품"], codes))
    print("부품", len(jobs), flush=True)
    with ProcessPoolExecutor(NW) as pool:
        fs = {pool.submit(일꾼, j): j for j in jobs}
        for f in as_completed(fs):
            try: res = f.result()
            except Exception as e: print("실패", fs[f][0][:40], e, flush=True); continue
            open(O, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n")
