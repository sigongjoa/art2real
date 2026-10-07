# -*- coding: utf-8 -*-
"""역산 정제 (10-07): 거의 맞은 코드(최고 IoU 문턱 아래)의 숫자만 조금씩 고쳐 IoU 를 올린다 — 모양 코드는 그대로 · 치수만.
언덕 오르기: 숫자 한두 개를 골라 크기에 비례해 흔들고, IoU 가 오르면 받아들인다. 0.85 넘으면 멈춤.
시험 모델(split.json)의 부품은 건드리지 않는다(학습 데이터로 새지 않게). CPU 일꾼 여럿 · 각 일꾼 8 GB 상한.
python s0/역산정제.py <split.json> [최소=0.5] [최대=0.8] [반복=80] [일꾼=4] [부품 수 제한]
→ runs/역산v2/정제.jsonl (부품마다 한 줄 · 이어서 돌릴 수 있음)"""
import os, sys, re, json, random, numpy as np, trimesh
from concurrent.futures import ProcessPoolExecutor, as_completed
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; V2 = os.path.join(os.path.dirname(H), "runs", "역산v2")
NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")

def 일꾼(args):
    name, codes, iters, seed = args
    from 역산수확 import 채점
    from score import cap; cap()
    import s0 as S
    gt = S.unit(trimesh.load(R + name, force="mesh")); g2 = gt.copy(); g2.apply_translation([-0.5] * 3); g2.apply_scale(2.0)
    gp = os.path.join(V2, "_정제_%d.stl" % os.getpid()); g2.export(gp)
    rng = random.Random(seed); best = (-9, None, None)
    for c0 in codes:   # 좌표 탐색: 숫자마다 ± 한 걸음 → 가장 좋은 쪽 · 한 바퀴 돌 때마다 걸음 절반 · iters = 채점 횟수 예산
        cur, cv = c0, 채점((c0, gp)); start = cv; used = 1; frac = 0.15
        while used < iters and cv < 0.85 and frac > 0.01:
            moved = False
            for k in range(len(list(NUM.finditer(cur)))):
                ms = list(NUM.finditer(cur))
                if k >= len(ms) or used >= iters: break
                m = ms[k]; v = float(m.group()); step = max(1.0 if "." not in m.group() else 0.05, abs(v) * frac)
                for nv in (v + step, v - step):
                    s_ = str(int(round(nv))) if "." not in m.group() else "%.2f" % nv
                    cand = cur[:m.start()] + s_ + cur[m.end():]; iv = 채점((cand, gp)); used += 1
                    if iv > cv + 1e-4: cur, cv, moved = cand, iv, True; break
            if not moved: frac /= 2
        if cv > best[0]: best = (cv, cur, start)
    os.remove(gp)
    return {"부품": name, "원래": round(best[2], 3), "정제": round(best[0], 3), "코드": best[1]}

if __name__ == "__main__":
    sp = sys.argv[1]; LO = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5; HI = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    IT = int(sys.argv[4]) if len(sys.argv) > 4 else 80; NW = int(sys.argv[5]) if len(sys.argv) > 5 else 4; LIM = int(sys.argv[6]) if len(sys.argv) > 6 else None
    test = set(json.load(open(sp, encoding="utf-8"))["시험모델"]); ONLY = os.environ.get("ONLYTEST") == "1"   # 1 = 시험 부품만(1 단계 점수 재기 · 학습엔 안 씀)
    O = V2 + ("/정제_시험.jsonl" if ONLY else "/정제.jsonl")
    done = {json.loads(l)["부품"] for l in open(O, encoding="utf-8")} if os.path.exists(O) else set()
    rows = [json.loads(l) for l in open(V2 + "/결과.jsonl", encoding="utf-8")]
    jobs = []
    for r in rows:
        if r["부품"] in done or ((r["부품"].split("/")[0] in test) != ONLY) or not (LO <= r["최고"] < HI) or "코드들" not in r: continue
        top = [c for v, (m, c) in sorted(zip(r["IoU"], r["코드들"]), key=lambda t: -t[0]) if v >= 0.4][:2]
        if top: jobs.append((r["부품"], top, IT, len(jobs)))
    jobs = jobs[:LIM]; print("정제 대상", len(jobs), flush=True)
    with ProcessPoolExecutor(NW) as pool:
        for f in as_completed([pool.submit(일꾼, j) for j in jobs]):
            try: res = f.result()
            except Exception as e: print("실패", e, flush=True); continue
            open(O, "a", encoding="utf-8").write(json.dumps(res, ensure_ascii=False) + "\n")
            print("%-40s %.3f → %.3f" % (res["부품"][:40], res["원래"], res["정제"]), flush=True)
