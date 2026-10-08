# -*- coding: utf-8 -*-
"""정답을 아는 합성 부품 → cadrille 와 같은 렌더(2×2 · 128) + 정답 표 (인코더0 · 10-08)
python runs/인코더0/합성.py N  →  runs/인코더0/합성/NNNN.png · 정답.json"""
import os, sys, json, random, math, tempfile
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(os.path.dirname(H))
sys.path[:0] = [T, os.path.join(T, "s0", "stub"), os.path.join(T, "s0")]
import cadquery as cq, trimesh, numpy as np
O = os.path.join(H, "합성"); os.makedirs(O, exist_ok=True)

def 부품(rng):
    바탕, 구멍, 모따기, 대칭, 비율 = rng.randrange(3), rng.randrange(4), rng.random() < .5, rng.random() < .5, rng.randrange(3)
    L, W, Z = {0: (70, 70, 14), 1: (55, 55, 50), 2: (110, 40, 50)}[비율]
    if 바탕 == 0: s = cq.Workplane("XY").box(L, W, Z)
    elif 바탕 == 1:   # 윤곽판: 좌우 대칭 다각형(x 반쪽을 만들고 뒤집음) → z 로 밀기
        n = rng.randint(2, 4); half = [(L / 2 * rng.uniform(.6, 1), W / 2 * (1 - 2 * i / n) * rng.uniform(.8, 1)) for i in range(n + 1)]
        pts = half + [(-x, y) for x, y in reversed(half)]; s = cq.Workplane("XY").polyline(pts).close().extrude(Z).translate((0, 0, -Z / 2))
    else:             # 회전체: 반지름 프로파일을 x 축으로 돌림
        L, r = {0: (24, 40), 1: (60, 30), 2: (110, 20)}[비율]; W = Z = 2 * r   # 납작 = 원판 · 정 = 굵은 통 · 길 = 막대
        k = rng.randint(2, 4); xs = np.linspace(-L / 2, L / 2, k + 1)
        prof = [(xs[0], 0)] + [(x, r * rng.uniform(.55, 1)) for x in xs] + [(xs[-1], 0)]
        s = cq.Workplane("XY").polyline(prof).close().revolve(360, (xs[0], 0, 0), (xs[-1], 0, 0))
    if 모따기:
        try: s = s.edges().chamfer(min(L, W, Z) * .12)
        except Exception: s = s.edges("|Z").chamfer(min(L, W) * .12)
    # 구멍: z 관통 · 대칭이면 ±x 짝(+ 홀수면 가운데 하나) · 아니면 아무 데나 + 한쪽 홈
    rr = min(L, W) * .09; xs = []
    if 대칭: xs = ([0.0] if 구멍 % 2 else []) + [v for i in range(구멍 // 2) for v in (L * (.18 + .14 * i), -L * (.18 + .14 * i))]
    else: xs = [L * (-.3 + .2 * i) + rng.uniform(-3, 3) for i in range(구멍)]
    for x in xs:
        s = s.cut(cq.Workplane("XY").cylinder(Z * 3, rr).translate((x, 0 if 대칭 else rng.uniform(-W * .1, W * .1), 0)))
    if not 대칭:   # 한쪽만 깎은 홈 — 대칭이 아님을 보이게
        s = s.cut(cq.Workplane("XY").box(L * .2, W * .5, Z * .5).translate((L * .45, W * .3, Z * .3)))
    return s, {"구멍": 구멍, "모따기": int(모따기), "바탕": 바탕, "대칭": int(대칭), "비율": 비율}

if __name__ == "__main__":
    from s0 import unit, item_img
    N = int(sys.argv[1]); rng = random.Random(0); 정답 = {}; p = os.path.join(tempfile.gettempdir(), "합성_%d.stl" % os.getpid())
    for i in range(N):
        while True:
            try: s, y = 부품(rng); cq.exporters.export(s, p); m = trimesh.load(p); assert len(m.faces) > 10; break
            except Exception as e: continue
        _, g = item_img(unit(m)); g.save(os.path.join(O, "%04d.png" % i)); 정답["%04d" % i] = y
        if i % 100 == 0: print(i, y, flush=True)
    json.dump(정답, open(os.path.join(H, "정답.json"), "w", encoding="utf-8"), ensure_ascii=False)
