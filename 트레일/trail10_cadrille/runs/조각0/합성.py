# -*- coding: utf-8 -*-
"""조각0 합성 — 어휘(조각.py) 로 지은 부품 · cadrille 렌더 + 정답 조각(단위 상자 [0,1]³ 좌표)
python runs/조각0/합성.py N [일꾼=12]  →  합성/NNNN.png · 정답/NNNN.json"""
import os, sys, json, random, tempfile
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(os.path.dirname(H))
sys.path[:0] = [T, os.path.join(T, "s0", "stub"), os.path.join(T, "s0"), H]
from 조각 import 종류

def 프로그램(rng):   # 첫 몸통 + 붙는 덩어리 0~2 + 빼기 0~4 (mm 비슷한 임의 단위)
    P = []; sx, sy, sz = rng.uniform(30, 90), rng.uniform(20, 70), rng.uniform(8, 50)
    P.append((rng.choice(["상자", "상자", "원통z", "원통x"]), (0, 0, 0), (sx, sy, sz)))
    for _ in range(rng.randint(0, 2)):
        t = rng.choice(["상자", "원통z", "원통x", "원통y", "공"]); s = [rng.uniform(8, 35) for _ in range(3)]
        ax = rng.randrange(3); c = [rng.uniform(-v / 2, v / 2) for v in (sx, sy, sz)]; c[ax] = rng.choice([-1, 1]) * ((sx, sy, sz)[ax] / 2 + s[ax] * .3)
        if t == "공": s = [s[0]] * 3
        P.append((t, tuple(c), tuple(s)))
    for _ in range(rng.randint(0, 4)):
        t = rng.choice(["구멍z", "구멍z", "구멍x", "구멍y", "사각구멍"]); r = rng.uniform(4, 14)
        c = [rng.uniform(-v * .35, v * .35) for v in (sx, sy, sz)]
        s = {"구멍z": (r, r, 300), "구멍x": (300, r, r), "구멍y": (r, 300, r), "사각구멍": (rng.uniform(6, 25), rng.uniform(6, 25), rng.uniform(6, 40))}[t]
        P.append((t, tuple(c), s))
    return P

def 짓기(P):
    import cadquery as cq
    r = None
    for t, c, s in P:
        if t in ("상자", "사각구멍"): o = cq.Workplane("XY").box(*s)
        elif t == "공": o = cq.Workplane("XY").sphere(s[0] / 2)
        else:
            ax = t[-1]; h = {"x": s[0], "y": s[1], "z": s[2]}[ax]; rr = sum(v for k, v in zip("xyz", s) if k != ax) / 4
            o = cq.Workplane({"x": "YZ", "y": "XZ", "z": "XY"}[ax]).cylinder(h, rr)
        o = o.translate(c)
        if 종류[t] > 0: r = o if r is None else r.union(o)
        else: r = r.cut(o)
    return r

def 일(a):
    i0, i1 = a
    import cadquery as cq, trimesh, numpy as np
    from s0 import unit, item_img
    p = os.path.join(tempfile.gettempdir(), "조각0_%d.stl" % os.getpid())
    for i in range(i0, i1):
        rng = random.Random(1000 + i)
        while True:
            try:
                P = 프로그램(rng); cq.exporters.export(짓기(P), p, tolerance=0.05, angularTolerance=0.2); m = trimesh.load(p)
                assert m.is_watertight and len(m.faces) > 10; break
            except Exception: continue
        lo, hi = m.bounds; s = 1.0 / (hi - lo).max(); mid = (lo + hi) / 2
        _, g = item_img(unit(m)); g.save(os.path.join(H, "합성", "%04d.png" % i))
        Q = [(t, [float((c[k] - mid[k]) * s + .5) for k in range(3)], [float(v * s) for v in sz]) for t, c, sz in P]   # 단위 상자 좌표
        json.dump(Q, open(os.path.join(H, "정답", "%04d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)

if __name__ == "__main__":
    from multiprocessing import Pool
    N = int(sys.argv[1]); k = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    for d in ("합성", "정답"): os.makedirs(os.path.join(H, d), exist_ok=True)
    step = (N + k - 1) // k
    with Pool(k) as pool: pool.map(일, [(a, min(a + step, N)) for a in range(0, N, step)])
    print("ok", N)
