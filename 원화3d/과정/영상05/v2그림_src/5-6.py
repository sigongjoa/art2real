# -*- coding: utf-8 -*-
"""5-6: 흰 판 양쪽의 검은 원기둥 토막. (a) 왼쪽 가는 토막의 속이 오른쪽 굵은 토막 속에 통째로 들어감 → 이어 보임 · (b) 서로 일부만 겹침 → 안 이어짐. python 5-6.py"""
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity
from cetz_util import poly, build
def body(x0, x1, w, cap_l, cap_r, n=80):
    """옆에서 본 회전체: 윗선 w(x) · 아랫선 -w(x) · 양 끝은 볼록한 호(cap = 호의 불룩함)."""
    xs = np.linspace(x0, x1, n); top = [(x, w(x)) for x in xs]
    a = np.linspace(-np.pi / 2, np.pi / 2, 30)
    right = [(x1 + cap_r * np.cos(t), w(x1) * np.sin(t)) for t in a[::-1]]
    left = [(x0 - cap_l * np.cos(t), w(x0) * np.sin(t)) for t in a]
    return Polygon(top + right[1:] + [(x, -y) for x, y in top[::-1]] + left[1:])
thin = lambda: body(-6.0, -1.0, lambda x: 0.52 + 0.24 * np.exp(-((x + 6.0) / 0.5) ** 2) - 0.02 * (x + 6), 0.35, 0.0)
thick = lambda: body(0.6, 5.0, lambda x: 1.62 - 0.32 * np.sin(np.pi * (x - 0.6) / 3.6) * (x < 4.2) + 0.15 * max(0, x - 4.2), 0.0, 0.55)
c = []
for ox, dyl, dyr, rot, tag in ((-8.6, 0.0, 0.0, 0, "a"), (8.6, 1.15, -0.5, 4, "b")):
    L = affinity.rotate(affinity.translate(thin(), ox, dyl), rot, origin=(ox - 1.0, dyl)); R = affinity.translate(thick(), ox, dyr)
    c += poly(L) + poly(R)
    c.append("rect((%.2f, -2.4), (%.2f, 2.6), fill: white, stroke: 1.8pt + black)" % (ox - 1.3, ox + 0.9))
    c.append("content((%.2f, -4.2), [(%s)])" % (ox - 0.2, tag))
build("5-6", c, length="0.9cm")
