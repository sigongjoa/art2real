# -*- coding: utf-8 -*-
"""5 장 2D 그림 공용: shapely 도형 → CeTZ 명령 · 굽기. 원판을 늘어놓아 굵기가 변하는 관(tube)을 만든다."""
import os, subprocess, numpy as np
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

def smooth(pts, k=24):
    """캣멀롬으로 점 사이를 매끈하게."""
    P = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [np.array(v, float) for v in P[i - 1:i + 3]]
        for t in np.linspace(0, 1, k, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float)); return np.array(out)

def tube(pts, wfun, n=160):
    """중심선 pts(매끈하게) 를 따라 반지름 wfun(t∈[0,1]) 원판을 늘어놓은 합."""
    c = smooth(pts); L = LineString(c)
    return unary_union([Point(L.interpolate(t, normalized=True)).buffer(max(1e-3, wfun(t)), 48) for t in np.linspace(0, 1, n)]).simplify(0.004)

def tz(p): return "(%.3f, %.3f)" % (p[0], p[1])

def rings(g):
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.geom_type != "Polygon": continue
        yield list(p.exterior.coords)
        for r in p.interiors: yield list(r.coords)

def poly(g, stroke="none", fill="black", w="2.2pt"):
    s = ("(paint: %s, thickness: %s, join: \"round\")" % (stroke, w)) if stroke != "none" else "none"
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.geom_type != "Polygon": continue
        if len(p.interiors) == 0:
            out.append("line(%s, close: true, stroke: %s, fill: %s)" % (", ".join(tz(c) for c in p.exterior.coords), s, fill))
        else:  # 구멍: 바깥을 칠하고 구멍을 흰색으로
            out.append("line(%s, close: true, stroke: %s, fill: %s)" % (", ".join(tz(c) for c in p.exterior.coords), s, fill))
            for r in p.interiors: out.append("line(%s, close: true, stroke: %s, fill: white)" % (", ".join(tz(c) for c in r.coords), s))
    return out

def polyline(pts, w="2.2pt", paint="black", close=False):
    return "line(%s, close: %s, stroke: (paint: %s, thickness: %s, cap: \"round\", join: \"round\"))" % (", ".join(tz(c) for c in pts), "true" if close else "false", paint, w)

def build(name, cmds, length="1cm", size="24pt"):
    typ = """// %s: 생성 = %s.py (shapely → CeTZ)
#import "@preview/cetz:0.4.2"
#set page(width: 33.867cm, height: 19.05cm, margin: 0cm, fill: white)
#set text(font: "Malgun Gothic", size: %s, weight: "bold", fill: rgb("#282828"))
#align(center + horizon, cetz.canvas(length: %s, {
  import cetz.draw: *
  %s
}))
""" % (name, name, size, length, "\n  ".join(cmds))
    p = os.path.join(HERE, name + ".typ"); open(p, "w", encoding="utf-8").write(typ)
    subprocess.run(["typst", "compile", "--format", "png", "--ppi", "144", p, os.path.join(OUT, name + ".png")], check=True); print("저장", name)
