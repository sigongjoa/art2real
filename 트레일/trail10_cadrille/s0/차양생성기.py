# -*- coding: utf-8 -*-
"""차양 생성기 v0 (2026-10-05 · 첫 학습 데이터) — 메카 차양: V 자 판 + (모따기) + (홈 0~2)
레시피는 CAD-Recode 문체(sketch().segment…close().assemble().finalize().extrude · 정수 좌표 · ±100 안)로 써서 cadrille 가 아는 말투를 따른다.
python s0/차양생성기.py <출력 폴더> <개수> <씨앗> [모두=0|1: 1 이면 모따기 · 홈을 항상 넣음(시험지용)]"""
import os, sys, random

def 차양(rng, 모두=False):
    import os
    if os.environ.get("BIG") == "1":   # run3: cadrille 는 물체가 ±100 을 꽉 채우게 배움 — v0 은 칸의 1/4 크기로 찍혀 모따기가 작았다 → 크기 · 두께 · 모따기를 키움(렌더는 그대로)
        S = rng.randint(85, 98); d = rng.randint(45, 75); a = rng.randint(-5, 25); w = rng.randint(24, 40); c = rng.randint(6, 18); t = rng.randint(24, 44)
    else:
        S = rng.randint(55, 95); d = rng.randint(25, 55); a = rng.randint(-5, 20); w = rng.randint(14, 28); c = rng.randint(4, 14)
        t = rng.randint(10, 28)
    pts = [(-S, a), (-c, -d), (c, -d), (S, a), (S - w // 2, a + w), (0, -d + w), (-(S - w // 2), a + w)]
    seg = "".join(f".segment(({x},{y}))" for x, y in pts[2:])
    code = ("import cadquery as cq\nw0=cq.Workplane('XY',origin=(0,0,%d))\n" % (-t // 2)) + \
           f"r=w0.sketch().segment(({pts[0][0]},{pts[0][1]}),({pts[1][0]},{pts[1][1]})){seg}.close().assemble().finalize().extrude({t})"
    ch = 모두 or rng.random() < 0.6
    if ch: code += f".edges('>Z').chamfer({rng.randint(2, max(3, min(t // 2, 7))) if os.environ.get('BIG') != '1' else rng.randint(5, min(t // 2, 12))})"
    n = (rng.randint(1, 2) if 모두 else rng.choice([0, 1, 1, 2]))
    for i in range(n):
        gx = 0 if (n == 1 and rng.random() < 0.5) else rng.randint(-S // 2, S // 2); gw = rng.randint(3, 8) if os.environ.get('BIG') != '1' else rng.randint(5, 12); gd = rng.randint(3, max(4, t // 2))
        code += f".cut(cq.Workplane('XY').box({gw},200,{2 * gd}).translate(({gx},0,{t - t // 2})))"
    return code

if __name__ == "__main__":
    O, N, SEED = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); 모두 = len(sys.argv) > 4 and sys.argv[4] == "1"
    os.makedirs(O, exist_ok=True); rng = random.Random(SEED)
    for i in range(N): open(os.path.join(O, "%04d.py" % i), "w", encoding="utf-8").write(차양(rng, 모두))
