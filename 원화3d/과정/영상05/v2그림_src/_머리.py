# -*- coding: utf-8 -*-
"""평면 조각 머리(브리지먼식 블록) — 머리뼈 상자 · 얼굴 덩어리 · 코 쐐기 · 눈썹 턱 · 귀 · 목.  앞은 -y · 높이 약 2.2(정수리 1.1 · 턱 -1.1)."""
import _블록 as B


def face_pts():
    pts = []
    for s in (-1, 1):
        pts += [(s * 0.62, -0.80, 0.34), (s * 0.71, -0.52, -0.05), (s * 0.36, -0.82, -0.55),
                (s * 0.20, -0.78, -1.06), (s * 0.60, 0.12, -0.74), (s * 0.69, 0.30, -0.10), (s * 0.15, -0.50, -1.10)]
    return pts + [(0, -0.86, 0.34), (0, -0.90, -0.45), (0, -0.82, -1.10)]


def nose_pts(k=1.0):
    p = []
    for s in (-1, 1):
        p += [(s * 0.09, -0.86, 0.22), (s * 0.15, -1.15, -0.26), (s * 0.21, -0.86, -0.36), (s * 0.16, -1.04, -0.33)]
    p += [(0, -0.92, 0.24), (0, -1.19, -0.22), (0, -1.10, -0.38)]
    return [(x * k, (y + 0.86) * k - 0.86, z) for x, y, z in p]


def decal(o, quad_xz, color, depth=0.04):
    """머리 껍질 앞면에 붙는 얇은 판(눈구멍 · 입). quad_xz = [(x, z)...] 앞(-y)에서 쏴서 붙인다."""
    B.bpy.context.view_layer.update(); pts = []
    q = quad_xz; samp = [(q[i][0] + (q[(i + 1) % len(q)][0] - q[i][0]) * t / 6, q[i][1] + (q[(i + 1) % len(q)][1] - q[i][1]) * t / 6)
                         for i in range(len(q)) for t in range(6)]
    for x, z in samp:
        ok, hit, n, i = o.ray_cast(B.Vector((x, -5, z)), B.Vector((0, 1, 0)))
        assert ok, (x, z)
        pts += [(x, hit.y - 0.012, z), (x, hit.y + depth, z)]
    return B.hull(pts, "판", color, o.parent)


def head(parent=None, color=B.CLAY, neck=True, ears=True, nose_color=None, eyes=True):
    h = B.hull(B.cbox(-0.74, 0.74, -0.70, 1.10, -0.15, 1.10, c=0.30) + face_pts(), "머리", color, parent)
    ob = [h, B.hull(nose_pts(), "코", nose_color or color, parent)]
    if eyes:
        for s in (-1, 1):
            ob.append(decal(h, [(s * 0.12, 0.2), (s * 0.5, 0.2), (s * 0.5, 0.0), (s * 0.12, -0.02)], B.DARK2))
        ob.append(decal(h, [(-0.3, -0.52), (0.3, -0.52), (0.3, -0.58), (-0.3, -0.58)], B.DARK))
    if ears:
        for s in (-1, 1):
            ob.append(B.hull(B.cbox(s * 0.70 - 0.05, s * 0.70 + 0.05, 0.05, 0.42, -0.32, 0.22, c=0.03), "귀", color, parent))
    if neck:
        ob.append(B.hull(B.tbox(-1.55, -0.55, 0.9, 0.9, 0.84, 0.86, y0=0.34, y1=0.3), "목", color, parent))
    return ob
