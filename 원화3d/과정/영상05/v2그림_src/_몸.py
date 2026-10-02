# -*- coding: utf-8 -*-
"""블록 마네킹(9-1): 가슴 상자 · 골반 상자 · 허리는 선 하나(말벌 허리) · 머리 · 팔다리 각기둥.  키 약 8(머리 하나 1). 앞은 -y."""
import math
import _블록 as B
from mathutils import Vector, Euler, Matrix


def R(rot): return Euler([math.radians(a) for a in rot]).to_matrix()


def chest_pts(): return B.tbox(-0.8, 0.8, 1.35, 0.95, 1.9, 1.1)
def pelvis_pts(): return B.tbox(-0.45, 0.45, 1.25, 0.85, 1.6, 1.0)


def seg(a, b, w0, w1, color=B.CLAY, parent=None):
    """a→b 로 가늘어지는 사각 기둥(끝 단면 w0 → w1)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); u = d.cross(Vector((0, 1, 0)))
    if u.length < 1e-3: u = d.cross(Vector((1, 0, 0)))
    u.normalize(); v = d.cross(u)
    pts = [p + (u * sx + v * sy) * w / 2 for p, w in ((a, w0), (b, w1)) for sx in (-1, 1) for sy in (-1, 1)]
    return B.hull([tuple(p) for p in pts], "마디", color, parent)


def figure(x, chest_rot, pelvis_rot, chest_shift=0.0, limbs=True, y=0.0, z=0.0):
    P0 = Vector((x, y, 4.3 + z)); Rp = R(pelvis_rot)
    C0 = P0 + Rp @ Vector((chest_shift, 0, 0.45)) + Vector((0, 0, 1.25)); Rc = R(chest_rot)
    p = B.hull([tuple(P0 + Rp @ Vector(q)) for q in pelvis_pts()], "골반", B.COOL)
    c = B.hull([tuple(C0 + Rc @ Vector(q)) for q in chest_pts()], "가슴", B.WARM)
    B.rod(tuple(P0 + Rp @ Vector((0, 0.1, 0.45))), tuple(C0 + Rc @ Vector((0, 0.1, -0.8))), color=(0.15, 0.15, 0.18), t=0.05)
    out = [p, c]
    if not limbs: return out
    nk = C0 + Rc @ Vector((0, 0.05, 0.8)); hd = nk + Vector((0, -0.05, 0.75))
    out.append(seg(nk, nk + Vector((0, 0, 0.3)), 0.4, 0.38))
    out.append(B.hull([tuple(hd + Vector(q)) for q in B.cbox(-0.38, 0.38, -0.45, 0.45, -0.5, 0.5, c=0.1)], "머리"))
    out.append(B.hull([tuple(hd + Vector(q)) for q in ((-0.07, -0.45, 0.1), (0.07, -0.45, 0.1), (-0.11, -0.45, -0.18), (0.11, -0.45, -0.18), (0, -0.62, -0.16))], "코"))
    for s in (-1, 1):
        hip = P0 + Rp @ Vector((s * 0.48, 0, -0.35)); foot = Vector((x + s * 0.55, y - 0.1, 0.25 + z))
        knee = (hip + foot) / 2 + Vector((0, -0.12, 0))
        out += [seg(hip, knee, 0.62, 0.42), seg(knee, foot, 0.42, 0.28)]
        out.append(B.hull([tuple(foot + Vector(q)) for q in B.cbox(-0.18, 0.18, -0.65, 0.2, -0.25, 0.05)], "발"))
        sh = C0 + Rc @ Vector((s * 1.05, 0, 0.6)); el = sh + Vector((s * 0.12, 0.05, -1.45)); wr = el + Vector((s * 0.05, -0.1, -1.3))
        out += [seg(sh, el, 0.42, 0.32), seg(el, wr, 0.32, 0.22)]
        out.append(seg(wr, wr + Vector((s * 0.02, -0.05, -0.55)), 0.3, 0.2))
    return out


ORANGE = (0.95, 0.66, 0.42)


def arm(g, elbow=0.0, wrist=0.0, twist=0.0, hand=True):
    """팔 블록(어깨 원점 · 아래 -z · 앞 -y · 바깥 +x · 손바닥 앞). 어깨 쐐기(진한 주황) · 위팔 각기둥 ·
    아래팔 = 바깥 쐐기(주황, 위팔 끝을 덮고 엄지 쪽으로) + 안 쐐기(파랑, 새끼 쪽으로) + 가는 심 · 손목 · 손.
    elbow/wrist = 굽힘(도) · twist = 아래팔 비틀림(도). 반환 [모든 조각]."""
    out = []
    out.append(B.hull([(-0.45, -0.6, 0.45), (0.6, -0.55, 0.4), (-0.45, 0.6, 0.45), (0.6, 0.55, 0.4), (0.75, 0, 0.05),
                       (0.62, -0.18, -1.55), (0.62, 0.18, -1.55), (0.1, -0.62, -0.5), (0.1, 0.62, -0.5)], "어깨쐐기", ORANGE, g))
    out.append(B.hull(B.tbox(-3.0, 0.1, 0.95, 0.68, 0.85, 1.0), "위팔", B.CLAY, g))
    e = B.empty("팔꿈치", loc=(0, 0.1, -2.9), rot=(-elbow, 0, 0), parent=g)
    e2 = B.empty("비틀", rot=(0, 0, twist), parent=e)
    out.append(B.hull([(0.38, -0.5, 0.95), (0.62, 0.15, 0.85), (0.72, -0.3, 0.3), (0.2, -0.55, 0.0), (0.7, 0.25, -0.3),
                       (0.35, -0.35, -2.5), (0.48, -0.1, -2.5)], "바깥쐐기", B.WARM, e2))
    out.append(B.hull([(-0.62, 0.35, 0.15), (-0.55, -0.45, 0.0), (-0.1, -0.58, -0.2), (-0.72, -0.05, -0.4),
                       (-0.3, -0.35, -2.5), (-0.42, -0.05, -2.5)], "안쐐기", B.COOL, e2))
    out.append(B.hull(B.tbox(-2.75, 0.3, 0.62, 0.36, 0.7, 0.75, y0=0.02, y1=0.12), "아래팔", B.CLAY, e2))
    w = B.empty("손목", loc=(0, 0.0, -2.75), rot=(-wrist, 0, 0), parent=e2)
    out.append(B.hull(B.tbox(-0.32, 0.02, 0.85, 0.4, 0.8, 0.45), "손목", B.CLAY, w))
    if hand:
        out.append(B.hull([(sx * a, y, z) for sx in (-1, 1) for a, y, z in ((0.47, -0.17, -0.32), (0.47, 0.17, -0.32), (0.45, -0.1, -1.45), (0.45, 0.1, -1.45))], "손", B.CLAY, w))
        out.append(B.hull([(0.42, -0.15, -0.35), (0.42, 0.1, -0.35), (0.62, -0.25, -0.7), (0.72, -0.4, -1.1), (0.6, -0.4, -1.15), (0.45, -0.1, -0.85)], "엄지", B.CLAY, w))
    return out


def hand(g, curls=(10, 10, 10, 10), thumb=(20, 10), spread=6, color=B.CLAY, palm_color=B.WARM):
    """각진 손(손목 원점 · 손가락은 -z · 손등 +y · 엄지 +x). curls = 검지~새끼 마디 굽힘(도, 세 마디 같이) · thumb = (벌림, 굽힘)."""
    out = [B.hull([(x, y, z) for x, y, z in ((-0.5, -0.17, 0), (0.45, -0.22, 0), (-0.5, 0.17, 0), (0.45, 0.22, 0),
                                              (-0.55, -0.15, -1.25), (0.58, -0.17, -1.3), (-0.55, 0.15, -1.25), (0.58, 0.17, -1.3))], "손바닥", palm_color, g)]
    xs = (0.42, 0.14, -0.14, -0.42); L = ((0.55, 0.36, 0.28), (0.62, 0.4, 0.3), (0.58, 0.38, 0.28), (0.45, 0.3, 0.24))
    for i, (x, c) in enumerate(zip(xs, curls)):
        p = B.empty("손가락", loc=(x, 0, -1.28 - (0.04 if i in (1, 2) else 0)), rot=(-c, (i - 1.5) * -spread * 0, (i - 1.5) * spread * 0.0), parent=g)
        w = 0.29 - 0.015 * i
        for j, l in enumerate(L[i]):
            out.append(B.hull(B.cbox(-w / 2, w / 2, -0.15, 0.15, -l, 0, c=0.03), "마디", color, p))
            p = B.empty("관절", loc=(0, 0, -l), rot=(-c, 0, 0), parent=p); w *= 0.92
    t = B.empty("엄지뿌리", loc=(0.45, -0.05, -0.15), rot=(-thumb[1] * 0.5, -35 - thumb[0], 0), parent=g)
    out.append(B.hull(B.tbox(-0.75, 0, 0.3, 0.3, 0.42, 0.36), "엄지바닥", palm_color, t))
    t = B.empty("엄지", loc=(0, 0, -0.75), rot=(-thumb[1], 0, 0), parent=t)
    for l in (0.42, 0.32):
        out.append(B.hull(B.cbox(-0.13, 0.13, -0.13, 0.13, -l, 0, c=0.03), "마디", color, t))
        t = B.empty("관절", loc=(0, 0, -l), rot=(-thumb[1], 0, 0), parent=t)
    return out
