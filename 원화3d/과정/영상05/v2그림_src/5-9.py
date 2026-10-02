# -*- coding: utf-8 -*-
"""5-9 · 5-10: 소라. 5-9 = 앞 입구(빗금 구멍) + 말려 들어간 선 끝 → 뒤의 반달 조각들이 나선으로 읽힘. 5-10 = 앞만 매끈한 알로 바꿈(뒤는 그대로).
python 5-9.py  (두 장을 함께 만든다)"""
import numpy as np
from shapely.geometry import Point, LineString
from shapely import affinity
from shapely.ops import unary_union
from cetz_util import tube, poly, polyline, build
G = 'rgb("#eeeeee")'
def ell(cx, cy, rx, ry, rot): return affinity.translate(affinity.rotate(affinity.scale(Point(0, 0).buffer(1, 96), rx, ry), rot), cx, cy)
def spire():
    c = poly(tube([(6.8, 2.45), (7.6, 2.4), (8.3, 1.6)], lambda t: 0.16 * (1 - t) + 0.02), stroke="black", fill=G, w="1.4pt")   # 끝 가시
    for (x, y, r, w) in ((6.2, 2.15, 0.95, "1.6pt"), (5.0, 1.85, 1.55, "2pt"), (3.3, 1.3, 2.4, "2.6pt")):
        c += poly(Point(x, y).buffer(r, 96), stroke="black", fill=G, w=w)
    return c
# 5-9
ap = ell(0.9, -3.5, 1.35, 2.25, -35)
body = unary_union([Point(-1.6, 0.4).buffer(4.3, 128), unary_union([Point(-1.6, 0.4).buffer(3.4, 64), ap]).convex_hull]).buffer(0.9, 64).buffer(-0.9, 64)   # 닫힘으로 오목 모서리를 매끈하게
c = spire() + poly(body, stroke="black", fill=G, w="3.4pt")
c += poly(ap, stroke="black", fill='rgb("#8a8a8a")', w="3.4pt")
for k in np.arange(-8, 8, 0.32):   # 입구 빗금
    seg = LineString([(k - 5, -9), (k + 5, 1)]).intersection(ap.buffer(-0.06))
    if not seg.is_empty and seg.length > 0.05: c.append(polyline(list(seg.coords), w="1.4pt", paint="rgb(\"#2a2a2a\")"))
s = np.linspace(0, 4.6, 120); cx, cy = -1.1, 0.6
curl = [(cx + 3.0 * np.exp(-0.45 * t) * np.cos(np.radians(-58) + t), cy + 3.0 * np.exp(-0.45 * t) * np.sin(np.radians(-58) + t)) for t in s]
c += poly(tube(curl[::6], lambda t: 0.14 * (1 - t) + 0.04), fill="black")
build("5-9", c, length="1.15cm")
# 5-10: 앞을 매끈한 알로
body2 = ell(-1.6, 0.0, 3.9, 4.5, -8)
build("5-10", spire() + poly(body2, stroke="black", fill=G, w="3.4pt"), length="1.15cm")
