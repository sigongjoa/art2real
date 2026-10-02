"""5-7 판 관통 두 원기둥(Tse 1999 그림19) — 판 왼쪽 관은 올라가고 오른쪽 관은 내려감 · 각도가 달라도 휘어진 관 하나. 고양이가 공을 넣으면 반대쪽으로 나옴 · 판이 들리면 굽은 관."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def spline(pts, n=160):
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []; m = n // (len(P) - 3)
    for i in range(1, len(P) - 2):
        for k in range(m):
            t = k / m; p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out + [P[-2]]
def tube(pts, r, m):
    cu = bpy.data.curves.new("관", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new("관", cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
pts = spline([(-1.4, 0.25, 0.3), (-0.95, 0.25, 1.0), (-0.4, 0.25, 1.75), (0, 0.25, 2.1), (0.4, 0.25, 2.0), (0.9, 0.25, 1.55), (1.4, 0.25, 1.1)])
pipe = tube(pts, 0.17, mat("관", (0.4, 0.72, 0.62), 0.5))
cap_m = mat("구멍", (0.05, 0.08, 0.07), 0.9)                       # 관 끝 구멍(어두운 원판)
for a, b in ((pts[0], pts[1]), (pts[-1], pts[-2])):
    d = (a - b).normalized(); h = cyl(0.13, 0.01, cap_m, loc=a + d * 0.002); h.rotation_mode = "QUATERNION"; h.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
board = box((0.9, 0.08, 2.9), mat("판", (0.55, 0.7, 0.95), 0.7), loc=(0, -0.05, 1.45), bevel=0.03)
ball_o = ball(0.1, mat("공", (0.95, 0.3, 0.3), 0.4), loc=(-1.85, 0.25, 0.1))
L = [0.0]
for i in range(1, len(pts)): L.append(L[-1] + (pts[i] - pts[i - 1]).length)
def along(s):                                # 관 속 길이 s 지점
    s = min(max(s, 0), L[-1])
    for i in range(1, len(L)):
        if L[i] >= s: t = (s - L[i - 1]) / max(1e-6, L[i] - L[i - 1]); return pts[i - 1].lerp(pts[i], t)
    return pts[-1]
cat = 고양이("고양이", (-2.35, 0.25, 0))

cams = {"front": camera("front", (-0.3, -5.6, 1.4), (-0.3, 0, 1.25), 24),
        "close": camera("close", (0.2, -3.6, 1.5), (0, 0, 1.4), 26),
        "low": camera("low", (-1.4, -2.4, 0.25), (0.2, 0.2, 0.9), 21),
        "top": camera("top", (1.6, -2.6, 3.8), (0, 0.2, 0.8), 24),
        "catcam": camera("catcam", (-3.0, -1.6, 0.7), (-1.0, 0.3, 0.7), 24),
        "orbit": camera("orbit", (0, -5.6, 1.5), (0, 0.2, 1.2), 24)}

end_dir = (pts[-1] - pts[-2]).normalized()
for fr in range(1, T.end + 1):
    # 공: 3줄 앞 20% 고양이 코로 굴려 관 입구 → 관 속(숨김) → 오른쪽 끝에서 튀어나와 떨어져 구름
    walk = False; cx = -2.35
    if fr < T.lines[3][0]: bp = Vector((-1.85, 0.25, 0.1)); hide = False
    else:
        r = T.u(3, 0, 0.2, fr); cx = -2.35 + 0.45 * r; walk = 0 < r < 1
        bp = Vector((-1.85, 0.25, 0.1)).lerp(pts[0], r); hide = False
        t = T.u(3, 0.2, 0.55, fr)
        if t > 0: bp = along(L[-1] * t); hide = t < 0.98
        f = T.u(3, 0.55, 0.85, fr)
        if f > 0:
            bp = pts[-1] + end_dir * 0.5 * f + Vector((0, 0, 0)); bp.z = pts[-1].z * (1 - f) ** 2 + 0.1 * f + 0.2 * math.sin(math.pi * f) * 0.5; hide = False
        g = T.u(3, 0.85, 1.0, fr); bp.x += 0.4 * g
        if fr >= T.lines[4][0]: bp = Vector((pts[-1].x + 0.5 + 0.4, 0.25, 0.1))
    ball_o.location = bp; ball_o.hide_render = hide
    ball_o.keyframe_insert("location", frame=fr); ball_o.keyframe_insert("hide_render", frame=fr)
    cat[0].location.x = cx; cat[0].keyframe_insert("location", frame=fr)
    peek = T.u(3, 0.3, 0.6, fr) if fr >= T.lines[3][0] else 0
    cat[1].rotation_euler = (0, -0.3 - 0.25 * math.sin(fr / 14) ** 2, 0.35 * math.sin(fr / 11) * (1 - peek)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    lift = T.u(4, 0.05, 0.5, fr) if fr >= T.lines[4][0] else 0
    if fr >= T.lines[5][0]: lift = 1 - T.u(5, 0.3, 0.7, fr)
    board.location.z = 1.45 + 3.8 * lift; board.keyframe_insert("location", frame=fr)
    oc, _ = cams["orbit"]; u = T.u(4, 0, 1, fr) if fr >= T.lines[4][0] else 0
    ang = math.radians(-90 + 40 * u); oc.location = (5.6 * math.cos(ang), 5.6 * math.sin(ang), 1.5 + 1.0 * u); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = 1.6 - 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
