"""5-13 Speed Plate XII · 미켈란젤로 습작 — 타원 덩어리를 하나씩 쌓아 팔을 만든다 → 검은 그림자로 바꾸면 겹친 곳마다 윤곽이 꺾임 → 떼어 보면 타원 가장자리들."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
board = mat("판", (1, 1, 1), 1.0, emit=1.45)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, board, loc=(0, 1.3, 2.0)).scale = (3.4, 4.0, 1)
box((1.2, 0.8, 0.3), mat("받침", (0.85, 0.8, 0.7), 0.8), loc=(0, 0, 0.15), bevel=0.03)
Z0 = 0.3
M = [  # 이름, 위치, 반지름(x,y,z), 색, 떼어낼 방향
    ("어깨", (0, 0.1, 3.0), (0.48, 0.4, 0.4), (0.98, 0.6, 0.45), (0, 0, 0.5)),
    ("세모근", (0.2, -0.08, 2.6), (0.3, 0.3, 0.45), (0.95, 0.45, 0.5), (0.6, -0.2, 0.2)),
    ("뒤팔", (-0.14, 0.12, 2.05), (0.27, 0.27, 0.55), (0.6, 0.75, 0.95), (-0.6, 0.2, 0)),
    ("앞팔", (0.08, -0.12, 1.98), (0.28, 0.28, 0.55), (0.98, 0.72, 0.3), (0.6, -0.2, 0)),
    ("팔꿈치", (-0.04, 0, 1.42), (0.2, 0.2, 0.2), (0.7, 0.55, 0.9), (-0.5, 0, 0)),
    ("아래팔위", (0.1, -0.06, 1.12), (0.27, 0.24, 0.42), (0.45, 0.78, 0.6), (0.6, -0.2, 0)),
    ("아래팔아래", (-0.04, 0.05, 0.68), (0.17, 0.16, 0.42), (0.98, 0.55, 0.65), (-0.6, 0.2, 0)),
    ("손", (0.03, -0.02, 0.24), (0.19, 0.09, 0.2), (0.98, 0.82, 0.6), (0.5, -0.2, -0.05)),
]
black = mat("그림자", (0.02, 0.02, 0.025), 0.6)
parts = []
for name, loc, rad, col, out in M:
    p = Vector(loc) + Vector((0, 0, Z0))
    a = ball(1.0, mat(name, col, 0.6), loc=p, scale=rad)
    b = ball(1.0, black, loc=p, scale=rad)
    parts.append((a, b, p, Vector(rad), Vector(out)))
cat = 고양이("고양이", (-1.25, -0.6, 0)); cat[0].rotation_euler.z = math.radians(20)

cams = {"front": camera("front", (0, -6.0, 1.9), (0, 0, 1.9), 26),
        "close": camera("close", (0.3, -3.9, 2.4), (0, 0, 2.2), 27),
        "low": camera("low", (1.3, -2.8, 0.3), (0, 0, 1.8), 21),
        "top": camera("top", (1.6, -3.2, 4.8), (0, 0, 1.7), 24),
        "build": camera("build", (-1.0, -4.6, 1.4), (0, 0, 1.8), 25)}

n = len(parts)
for fr in range(1, T.end + 1):
    sil = T.lines[2][0] <= fr < T.lines[3][0]                      # 2줄: 그림자(검정)
    ex = T.u(3, 0.05, 0.45, fr) * (1 - T.u(3, 0.8, 1.0, fr)) if fr >= T.lines[3][0] and fr < T.lines[4][0] else 0
    for k, (a, b, p, rad, out) in enumerate(parts):
        g = T.u(1, k / n * 0.9, k / n * 0.9 + 0.18, fr) if fr >= T.lines[1][0] else 0  # 하나씩 쏙
        if fr < T.lines[1][0]: g = 1.0                                                  # 0줄: 완성된 팔
        if T.lines[1][0] <= fr and k / n * 0.9 > (fr - T.lines[1][0]) / max(1, T.lines[1][1] - T.lines[1][0]): g = 0
        pop = 1 + 0.25 * math.sin(math.pi * min(1, g * 1.0)) * (g < 1)
        s = rad * max(g * pop, 0.001)
        loc = p + out * ex * 1.4 + Vector((0, 0, 0.6 * (1 - g)))
        for o, show in ((a, not sil), (b, sil)):
            o.scale = s; o.location = loc; o.hide_render = not show or g <= 0.001
            o.keyframe_insert("scale", frame=fr); o.keyframe_insert("location", frame=fr); o.keyframe_insert("hide_render", frame=fr)
    cat[1].rotation_euler = (0, -0.7 + 0.15 * math.sin(fr / 9), 0.3 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    hop = 0.3 * math.sin(math.pi * T.u(3, 0.05, 0.25, fr)) if fr >= T.lines[3][0] else 0
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, False)
    bc, _ = cams["build"]; bc.location.x = -1.0 + 0.8 * (T.u(1, 0, 1, fr) if fr >= T.lines[1][0] else 0); bc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = 1.6 - 1.2 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.y = -6.0 + 0.4 * math.sin(fr / 50); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
