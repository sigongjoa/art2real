# -*- coding: utf-8 -*-
"""8-8 위에서 본 원뿔 하나: 창으로 빛이 들고 눈이 본다. 가장 밝은 점(입사각 = 반사각) · 그림자 시작(창에서 스치는 접선) ·
맞은편 벽에서 되돌아온 빛. 원 둘레 밝기는 창 표본에서 램버트로 실제 계산한다.  python 8-8.py → cetz/8-8.typ → 8-8.png"""
import math, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
X0, X1, Y0, Y1 = 2.2, 13.8, 1.1, 7.7          # 방
B, C = (3.6, Y1), (6.6, Y1)                     # 창(위 벽)
CX, CY, R = (6.0, 4.4, 1.3)                     # 원뿔(위에서 본 원)
D = (12.6, 4.4)                                 # 눈
WIN = [(B[0] + (C[0] - B[0]) * (i + .5) / 24, Y1) for i in range(24)]
WALL = [(X0 + (X1 - X0) * (i + .5) / 40, Y0) for i in range(40)]   # 맞은편(아래) 벽

def P(t): return (CX + R * math.cos(t), CY + R * math.sin(t))
def lam(t, srcs):
    n = (math.cos(t), math.sin(t)); p = P(t); s = 0
    for q in srcs:
        v = (q[0] - p[0], q[1] - p[1]); L = math.hypot(*v); s += max(0, (n[0] * v[0] + n[1] * v[1]) / L)
    return s / len(srcs)

N = 240; ts = [2 * math.pi * i / N for i in range(N)]
direct = [lam(t, WIN) for t in ts]; bounce = [lam(t, WALL) for t in ts]
dm = max(direct)
def grey(i):
    d = direct[i] / dm
    v = 0.50 + 0.47 * d if d > 0.02 else 0.50 + 0.16 * bounce[i] / max(bounce)
    return int(v * 255)

def unit(v): L = math.hypot(*v); return (v[0] / L, v[1] / L)
Wc = ((B[0] + C[0]) / 2, Y1)
def spec(t):
    n = (math.cos(t), math.sin(t)); p = P(t); w = unit((Wc[0] - p[0], Wc[1] - p[1])); e = unit((D[0] - p[0], D[1] - p[1]))
    h = unit((w[0] + e[0], w[1] + e[1])); return n[0] * h[0] + n[1] * h[1]
th = max(ts, key=spec); H = P(th)
ang = lambda u, v: math.degrees(math.acos(max(-1, min(1, u[0] * v[0] + u[1] * v[1]))))
nH = (math.cos(th), math.sin(th))
assert abs(ang(nH, unit((Wc[0] - H[0], Wc[1] - H[1]))) - ang(nH, unit((D[0] - H[0], D[1] - H[1])))) < 2, "입사각 ≠ 반사각"
def tangent(q, side):
    """q 에서 원에 스치는 접점(side ±1)."""
    dx, dy = CX - q[0], CY - q[1]; d = math.hypot(dx, dy); a = math.atan2(dy, dx) + math.pi; b = math.acos(R / d)
    return P(a + side * b)
TB, TC = tangent(B, +1), tangent(C, -1)                  # 그림자 시작(창 양 끝에서 스치는 선)
br = max(range(N), key=lambda i: bounce[i] if direct[i] < 0.02 else -1); RB = P(ts[br])
E = (CX + 1.6, Y0)                                       # 반사광이 오는 벽 자리

f = lambda p: "(%.3f, %.3f)" % p
L = []
L.append('#import "@preview/cetz:0.4.2"\n#set page(width: 16cm, height: 9cm, margin: 0cm, fill: white)\n#set text(font: "Malgun Gothic", size: 10pt, weight: "bold")')
L.append('#place(top + left, cetz.canvas(length: 1cm, {\n  import cetz.draw: *')
L.append('  rect((0, 0), (16, 9), stroke: none)')
L.append('  line(%s, %s, %s, %s, close: true, stroke: 1.6pt + black)' % (f((X0, Y1)), f((X0, Y0)), f((X1, Y0)), f((X1, Y1))))
L.append('  line(%s, %s, stroke: 5pt + rgb("#9cc3e6"))' % (f(B), f(C)))
L.append('  circle(%s, radius: %.3f, fill: rgb("#f4f2ee"), stroke: none)' % (f((CX, CY)), R))
Pr = lambda t, r: (CX + r * math.cos(t), CY + r * math.sin(t))
for i in range(N):   # 둘레 띠 = 그 자리의 밝기
    a0, a1 = ts[i], ts[i] + 2 * math.pi / N + 0.01; g = grey(i)
    L.append('  line(%s, %s, %s, %s, close: true, fill: rgb(%d, %d, %d), stroke: none)' % (f(Pr(a0, R)), f(Pr(a1, R)), f(Pr(a1, R - .38)), f(Pr(a0, R - .38)), g, g, g))
L.append('  circle(%s, radius: %.3f, stroke: 1.4pt + black)' % (f((CX, CY)), R))
ray = '  line(%s, %s, stroke: (paint: %s, thickness: 0.9pt%s))'
L.append(ray % (f(Wc), f(H), 'rgb("#d98b00")', '')); L.append(ray % (f(H), f(D), 'rgb("#d98b00")', ''))
L.append(ray % (f(B), f(TB), 'rgb("#777")', ', dash: "dashed"')); L.append(ray % (f(C), f(TC), 'rgb("#777")', ', dash: "dashed"'))
L.append(ray % (f(E), f(RB), 'rgb("#5b8fc9")', ''))
L.append('  circle(%s, radius: 0.13, fill: rgb("#ffd34d"), stroke: 0.8pt + black)' % f(H))
for p in (TB, TC): L.append('  circle(%s, radius: 0.08, fill: black)' % f(p))
L.append('  circle(%s, radius: 0.08, fill: rgb("#5b8fc9"))' % f(RB))
# 눈
L.append('  line(%s, %s, %s, stroke: 1.4pt + black)' % (f((D[0] + .35, D[1] + .3)), f(D), f((D[0] + .35, D[1] - .3))))
lab = '  content(%s, text(fill: rgb("%s"))[%s])'
L += [lab % (f(((B[0] + C[0]) / 2, Y1 + .35)), "#3a6fa8", "창"), lab % (f((D[0] + .75, D[1])), "#222", "눈"),
      lab % (f((CX, CY)), "#333", "원뿔"), lab % (f((H[0] + 1.75, H[1] + .5)), "#a86a00", "가장 밝은 점"),
      lab % (f((CX - 1.2, CY - 1.65)), "#555", "그림자"), lab % (f((E[0] + .9, Y0 + .3)), "#3a6fa8", "벽 반사광")]
L.append('}))')
typ = os.path.join(OUT, "cetz", "8-8.typ"); open(typ, "w", encoding="utf-8").write("\n".join(L))
subprocess.run(["typst", "compile", "--format", "png", "--ppi", "304.8", typ, os.path.join(OUT, "8-8.png")], check=True)
print("H 각도 %.1f°  그림자 접점" % math.degrees(th), TB, TC)
