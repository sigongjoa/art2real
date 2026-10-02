# -*- coding: utf-8 -*-
"""5-1: 막대(두 선) 앞뒤로 지나가는 검은 「벌레」 실루엣 — 윤곽 안에 선이 하나도 없다. python 5-1.py"""
import numpy as np
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union
from cetz_util import smooth, poly, polyline, build
path = [(-1.9, 4.3), (0.2, 4.5), (1.9, 3.7), (2.0, 2.4), (0.6, 1.0), (-1.2, -0.4), (-2.1, -2.0), (-1.2, -3.6), (0.6, -4.1), (1.8, -3.6)]
C = LineString(smooth(path)); w = lambda t: 0.95 - 0.25 * abs(2 * t - 1) ** 3
ts = np.linspace(0, 1, 200); P = [C.interpolate(t, normalized=True) for t in ts]
xs = np.array([p.x for p in P]); i1 = int(xs[:100].argmax()); i2 = 100 + int(xs[100:].argmin())   # 오른 끝 · 왼 끝에서 앞/뒤를 바꾼다
piece = lambda a, b: unary_union([P[i].buffer(w(ts[i]), 48) for i in range(a, b)]).simplify(0.004)
front = unary_union([piece(0, i1 + 1), piece(i2, 200)]); back = piece(i1, i2 + 1).difference(box(-0.75, -9, 0.75, 9))
c = poly(back, fill="rgb(\"#1e1e1e\")") + [polyline([(x, -6.6), (x, 6.6)], w="1.6pt") for x in (-0.75, 0.75)] + poly(front, fill="rgb(\"#1e1e1e\")")
build("5-1", c, length="1.15cm")
