# -*- coding: utf-8 -*-
"""5-8: 이을 선도 면도 없는데 하나로 보이는 다섯 장면.
(a) 판 셋을 뚫은 검은 나팔 셋 · (b) 구멍 뚫린 판을 지나 흘러내리는 젤 · (c) 판을 뚫은 검은 물체 · (d) 가림 막대 뒤로 돌아가는 덩어리 · (e) 좁은 고리를 지나는 덩어리.
python 5-8.py"""
import numpy as np
from shapely.geometry import Point, Polygon, LineString, box
from shapely import affinity
from shapely.ops import unary_union
from cetz_util import tube, poly, polyline, build

BLK, GRY, LGT = 'rgb("#141414")', 'rgb("#a8a8a8")', 'rgb("#d6d6d6")'
def place(g, ang, dx, dy, origin=(0, 0)): return affinity.translate(affinity.rotate(g, ang, origin=origin), dx, dy)
def profile(xs, r, cap=0.0):
    """x 축을 따라 반지름 r(x) 인 옆모습. cap>0 이면 끝(오른쪽)을 볼록한 호로."""
    top = [(x, r(x)) for x in xs]; a = np.linspace(np.pi / 2, -np.pi / 2, 30)
    end = [(xs[-1] + cap * np.cos(t), r(xs[-1]) * np.sin(t)) for t in a] if cap else []
    return Polygon(top + end + [(x, -y) for x, y in top[::-1]])
def slab(cx, cy, w, t, ang, depth=(0.35, 0.3), fill=LGT):
    """앞면 w×t 직사각형 + 윗면 평행사변형(깊이) — 회전 ang."""
    f = box(-w / 2, -t / 2, w / 2, t / 2); dx, dy = depth
    top = Polygon([(-w / 2, t / 2), (w / 2, t / 2), (w / 2 + dx, t / 2 + dy), (-w / 2 + dx, t / 2 + dy)])
    side = Polygon([(w / 2, -t / 2), (w / 2, t / 2), (w / 2 + dx, t / 2 + dy), (w / 2 + dx, -t / 2 + dy)])
    out = []
    for g, fc in ((top, 'rgb("#efefef")'), (side, 'rgb("#b8b8b8")'), (f, fill)):
        out += poly(place(g, ang, cx, cy), stroke="black", fill=fc, w="2pt")
    return out
c = []
# ---------- (a) ----------
A = (-11.5, 4.3)
horn = profile(np.linspace(0, 4.0, 60), lambda x: 0.33 + 0.75 * max(0, (x - 2.4) / 1.6) ** 2.2, cap=0.35)
parts = [Point(0, 0).buffer(0.95, 64)] + [place(horn, ang, 0, 0) for ang in (30, 150, 270)]
c += poly(affinity.translate(unary_union(parts), *A), fill=BLK)
for ang in (30, 150, 270):
    r = np.radians(ang); c += slab(A[0] + 1.6 * np.cos(r), A[1] + 1.6 * np.sin(r), 2.1, 0.45, ang - 90)
c.append('content((%.2f, %.2f), [(a)])' % (A[0] - 3.6, A[1] - 0.6))
# ---------- (b) 젤 ----------
B = (0.0, 4.6)
gel_top = Polygon([(0.85 * x, 1.2 + 0.8 * np.sin(x * 1.3) ** 2 + 0.35 * np.cos(x * 2.1) - 0.25 * x * x) for x in np.linspace(-2.6, 2.6, 40)] + [(3.0, 0.0), (-3.0, 0.0)]).buffer(0.45, 32).buffer(-0.45, 32)
drips = [tube([(x, 0.0), (x + 0.05, -L * 0.5), (x - 0.05, -L)], lambda t, w=w: w * (1 - 0.35 * t) + 0.05 * np.exp(-((t - 1) / 0.08) ** 2)) for x, L, w in ((-2.4, 2.6, 0.22), (-1.4, 1.6, 0.18), (0.0, 3.3, 0.32), (1.2, 2.2, 0.2), (2.3, 3.0, 0.25))]
gel = unary_union([gel_top] + drips)
c += poly(affinity.translate(gel, *B), stroke="black", fill=GRY, w="1.6pt")
plate = Polygon([(-3.6, -0.25), (2.9, -0.25), (3.7, 0.55), (-2.8, 0.55)])
c += poly(affinity.translate(plate, *B), stroke="black", fill='rgb(40, 40, 40, 170)', w="1.6pt")
c += poly(affinity.translate(affinity.scale(Point(0, 0).buffer(1, 48), 0.5, 0.18), B[0] + 0.1, B[1] + 0.15), fill="black")
c.append('content((%.2f, %.2f), [(b)])' % (B[0] - 3.4, B[1] - 2.4))
# ---------- (c) ----------
C = (11.0, 4.3)
bell = profile(np.linspace(0, 7.6, 120), lambda x: (0.55 + 1.7 * np.exp(-x / 0.9)) if x < 6.4 else 0.55 + 0.9 * ((x - 6.4) / 1.2) ** 2, cap=0.0)
bell = unary_union([bell, affinity.scale(Point(0, 0).buffer(1, 64), 0.5, 2.25)])
cb = place(bell, -50, C[0] - 2.4, C[1] + 2.6, origin=(0, 0))
c += poly(cb, fill=BLK)
base_c = (C[0] - 2.4 + 7.6 * np.cos(np.radians(-50)), C[1] + 2.6 + 7.6 * np.sin(np.radians(-50)))
for k, f in ((1.0, 'rgb("#444")'), (0.75, 'rgb("#666")'), (0.5, 'rgb("#888")'), (0.28, 'rgb("#555")')):
    c += poly(place(affinity.scale(Point(0, 0).buffer(1, 64), 0.42 * k, 1.47 * k), -50, *base_c), stroke="black", fill=f, w="1.4pt")
sc_ = (C[0] - 2.4 + 2.9 * np.cos(np.radians(-50)), C[1] + 2.6 + 2.9 * np.sin(np.radians(-50)))
c += slab(sc_[0], sc_[1], 2.6, 0.4, 40, depth=(0.25, 0.3), fill='rgb("#f4f4f4")')
c.append('content((%.2f, %.2f), [(c)])' % (C[0] + 2.6, C[1] + 0.2))
# ---------- (d) 막대 뒤로 돌아가는 덩어리 ----------
D = (-6.0, -4.6)
rng = np.random.default_rng(5)
fingers = [tube([(0, 0), (1.6 * np.cos(a), 1.6 * np.sin(a)), (2.6 * np.cos(a + 0.25), 2.6 * np.sin(a + 0.25))], lambda t: 0.5 - 0.15 * t + 0.12 * np.exp(-((t - 1) / 0.15) ** 2))
           for a in np.linspace(0, 2 * np.pi, 9, endpoint=False) + 0.2]
blob = unary_union([Point(0, 0).buffer(1.4, 64)] + fingers).buffer(0.08)
c += poly(affinity.translate(blob, *D), stroke="black", fill="white", w="2.4pt")
bar = place(box(-4.2, -0.3, 4.2, 0.3), 40, *D); bar_side = place(Polygon([(-4.2, 0.3), (4.2, 0.3), (4.45, 0.55), (-3.95, 0.55)]), 40, *D)
c += poly(bar_side, stroke="black", fill='rgb("#3a3a3a")', w="1.6pt") + poly(bar, fill=BLK)
c.append('content((%.2f, %.2f), [(d)])' % (D[0], D[1] - 3.7))
# ---------- (e) 좁은 고리를 지나는 덩어리 ----------
E = (6.0, -4.4)
def lumpy(cx, cy, seed):
    r = np.random.default_rng(seed); lobes = [Point(cx + 1.3 * np.cos(a), cy + 1.0 * np.sin(a)).buffer(r.uniform(0.55, 0.8), 48) for a in np.linspace(0, 2 * np.pi, 8, endpoint=False) + r.uniform(0, 1)]
    return unary_union([affinity.scale(Point(cx, cy).buffer(1.3, 64), 1.25, 1.0)] + lobes)
top_b, bot_b = lumpy(E[0], E[1] + 2.0, 1), lumpy(E[0], E[1] - 2.0, 2)
for b in (top_b, bot_b):
    c += poly(b, stroke="black", fill="white", w="2.2pt")
    for x in np.arange(b.bounds[0], b.bounds[2], 0.38):
        for y in np.arange(b.bounds[1], b.bounds[3], 0.38):
            if b.buffer(-0.15).contains(Point(x, y)): c.append("circle((%.2f, %.2f), radius: 0.035, fill: black, stroke: none)" % (x, y))
collar = Polygon([(E[0] - 0.75, E[1] + 0.85), (E[0] + 0.75, E[1] + 0.85), (E[0] + 0.6, E[1] - 0.85), (E[0] - 0.6, E[1] - 0.85)])
c += poly(collar, fill=BLK)
for k in (-0.4, -0.12, 0.18, 0.42): c.append(polyline([(E[0] + k * 1.05, E[1] + 0.75), (E[0] + k, E[1] - 0.75)], w="1.6pt", paint="white"))
c.append('content((%.2f, %.2f), [(e)])' % (E[0] + 3.4, E[1]))
build("5-8", c, length="0.82cm")
