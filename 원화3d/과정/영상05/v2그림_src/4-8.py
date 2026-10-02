# -*- coding: utf-8 -*-
"""4-8: 브레그만의 B 와 리퍼의 코끼리 — (a) 조각만(가림 판 테두리의 L 꼭짓점 남음) · (b) 검은 가림 얼룩을 얹음 · (c) L 꼭짓점(가림 테두리 선)을 지움
(d) 코끼리 조각(검게) · (e) 가림 테두리 선을 지운 코끼리 윤곽. shapely 로 도형을 계산해 CeTZ(.typ)로 쓰고 typst 로 굽는다.
python 4-8.py"""
import os, subprocess, numpy as np
from shapely.geometry import box, Point, LineString, MultiLineString
from shapely import affinity
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(3)

def B_letter(x, y, s=1.0, rot=0):
    up = unary_union([box(0, 2.6, 1.7, 5.0), Point(1.7, 3.8).buffer(1.2, 64)])
    lo = unary_union([box(0, 0, 1.9, 2.6), Point(1.9, 1.3).buffer(1.3, 64)])
    holes = unary_union([box(0.65, 3.2, 1.7, 4.4), Point(1.7, 3.8).buffer(0.6, 64), box(0.65, 0.6, 1.9, 2.0), Point(1.9, 1.3).buffer(0.7, 64)])
    g = unary_union([up, lo]).difference(holes)
    g = affinity.rotate(g, rot, origin=(1.4, 2.5)); g = affinity.scale(g, s, s, origin=(0, 0)); return affinity.translate(g, x, y)

def worm(x0, y0, n=6, step=0.9, w=0.55):
    pts = [(x0, y0)]; a = rng.uniform(0, 6.3)
    for _ in range(n):
        a += rng.uniform(-0.9, 0.9); pts.append((pts[-1][0] + step * np.cos(a), pts[-1][1] + step * np.sin(a)))
    return LineString(pts).buffer(w * rng.uniform(0.8, 1.2), 32)

def ellipse(cx, cy, rx, ry, rot=0):
    return affinity.translate(affinity.rotate(affinity.scale(Point(0, 0).buffer(1, 64), rx, ry), rot), cx, cy)

def elephant():
    body = ellipse(0, 0.3, 3.0, 1.8)
    head = ellipse(3.1, 1.1, 1.25, 1.2)
    trunk = LineString([(3.9, 0.7), (4.4, -0.4), (4.5, -1.6), (4.3, -2.8)]).buffer(0.33, 32)
    legs = [box(x, -3.4, x + 0.95, -0.4) for x in (-2.5, -1.3, 0.7, 1.9)]
    tail = LineString([(-2.9, 0.4), (-3.5, -0.5)]).buffer(0.12, 16)
    return unary_union([body, head, trunk, tail] + legs)

def tz(p): return "(%.3f, %.3f)" % p

def rings(g):
    gs = getattr(g, "geoms", [g])
    for p in gs:
        if p.is_empty or p.geom_type != "Polygon": continue
        yield list(p.exterior.coords)
        for r in p.interiors: yield list(r.coords)

def lines(g):
    gs = getattr(g, "geoms", [g])
    for l in gs:
        if l.geom_type == "LineString" and l.length > 0.05: yield list(l.coords)
        elif hasattr(l, "geoms"): yield from lines(l)

def poly_cmds(g, stroke="black", fill="none", w="2.2pt"):
    return ["line(%s, close: true, stroke: %s, fill: %s)" % (", ".join(tz(c) for c in r), ("(paint: %s, thickness: %s, join: \"round\")" % (stroke, w)) if stroke != "none" else "none", fill) for r in rings(g)]

def line_cmds(g, w="2.2pt"):
    return ["line(%s, stroke: (paint: black, thickness: %s, cap: \"round\", join: \"round\"))" % (", ".join(tz(c) for c in l), w) for l in lines(g)]

def shift(g, dx, dy): return affinity.translate(g, dx, dy)

# ---- B 셋 + 얼룩 가림 ----
Bs = unary_union([B_letter(-3.2, -0.2, 0.62, -8), B_letter(-0.6, 0.5, 0.62, 6), B_letter(1.4, -3.4, 0.62, -4), B_letter(-2.6, -3.6, 0.62, 10)])
seeds = [Bs.boundary.interpolate(t, normalized=True) for t in np.linspace(0, 1, 22, endpoint=False) + 0.013]
O = unary_union([worm(q.x, q.y, n=3, step=0.45, w=0.27) for q in seeds])
O = O.intersection(Bs.convex_hull.buffer(0.6, 32))   # 얼룩은 글자 둘레 안에서만
frag = Bs.difference(O)
# ---- 코끼리 + 가림 ----
E = affinity.scale(elephant(), 0.9, 0.9, origin=(0, 0))
OE = unary_union([box(-2.2, 0.6, -0.9, 1.6), box(0.2, -0.9, 1.4, 0.2), box(1.5, 1.2, 2.6, 2.0), box(-2.3, -2.6, 1.6, -1.9), box(3.9, -1.3, 4.9, -0.7), box(-3.2, -0.5, -2.0, 0.2), box(2.5, -0.3, 3.6, 0.5), box(-0.8, 1.4, 0.6, 2.3), box(-1.6, -1.2, -0.6, -0.5)])
fragE = E.difference(OE)

cmds = []
for cx, tag in ((-11.0, "a"), (0.0, "b"), (11.0, "c")):
    if tag == "a": cmds += poly_cmds(shift(frag, cx, 4.2))
    if tag == "b": cmds += poly_cmds(shift(Bs, cx, 4.2), fill="white") + poly_cmds(shift(O, cx, 4.2), stroke="none", fill="black")
    if tag == "c": cmds += line_cmds(shift(Bs.boundary.difference(O.buffer(0.02)), cx, 4.2))
    cmds.append('content((%.2f, -0.6), [(%s)])' % (cx, tag))
for cx, tag in ((-6.5, "d"), (6.5, "e")):
    cmds.append("rect((%.2f, -8.6), (%.2f, -1.6), stroke: 1.4pt + black)" % (cx - 5.6, cx + 5.6))
    if tag == "d": cmds += poly_cmds(shift(fragE, cx - 0.4, -4.8), stroke="none", fill="black")
    else: cmds += line_cmds(shift(E.boundary.difference(OE.buffer(0.02)), cx - 0.4, -4.8))
    cmds.append('content((%.2f, -9.3), [(%s)])' % (cx, tag))

typ = """// 4-8: 생성 = 4-8.py (shapely 계산 → CeTZ)
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: 22pt, weight: "bold", fill: rgb("#282828"))
#align(center + horizon, cetz.canvas(length: 0.82cm, {
  import cetz.draw: *
  %s
}))
""" % "\n  ".join(cmds)
p = os.path.join(HERE, "4-8.typ"); open(p, "w", encoding="utf-8").write(typ)
subprocess.run(["typst", "compile", "--format", "png", "--ppi", "144", p, os.path.join(os.path.dirname(HERE), "4-8.png")], check=True)
print("저장 4-8")
