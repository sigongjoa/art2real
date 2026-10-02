"""4-6 T 접합 vs 홀로 끝난 선(Hummel & Biederman 1992 그림 15) — 두 토막 막대 앞에 판. 판 가장자리에서 T 자로 끝나면 한 막대, 고양이가 판을 밀어 치우면 허공에서 끝나 두 토막."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
wood, red = mat("판", (0.82, 0.62, 0.4), 0.8), mat("막대", (0.35, 0.55, 0.95), 0.45)
glow = mat("표시", (1.0, 0.35, 0.05), 0.5, emit=1.3)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, mat("벽", (0.97, 0.95, 0.9), 1.0, emit=1.35), loc=(0, 1.3, 1.4)).scale = (4.5, 2.8, 1)
plank = box((1.0, 0.08, 1.75), wood, loc=(0, 0, 0.875), bevel=0.03)
bars = [cyl(0.07, 0.9, red, loc=(x, 0.3, 1.25), rot=(0, math.pi / 2, 0)) for x in (-0.9, 0.9)]   # -1.35..-0.45 · 0.45..1.35
def ring(x):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.018, rotation=(math.pi / 2, 0, 0), location=(x, -0.12, 1.25))
    o = bpy.context.object; o.data.materials.append(glow); return o
tj = [ring(-0.5), ring(0.5)]; fe = [ring(-0.45), ring(0.45)]
for o in fe: o.location.y = 0.15
cat = 고양이("고양이", (-1.2, -0.05, 0))
cams = {"front": camera("front", (0, -4.0, 1.3), (0, 0, 1.2), 30),
        "close": camera("close", (0.35, -1.9, 1.35), (0.45, 0, 1.25), 34),
        "side": camera("side", (2.0, -2.2, 1.9), (0.3, 0, 1.15), 28),
        "wide": camera("wide", (1.6, -4.2, 0.6), (0.6, 0, 1.0), 24),
        "low": camera("low", (-1.0, -1.6, 0.25), (0, 0.2, 1.0), 22),
        "back": camera("back", (0.9, -1.0, 3.5), (0, 0.35, 1.2), 26)}
L = T.lines
for fr in range(1, T.end + 1):
    out = T.u(3, 0.25, 0.95, fr); back = T.u(5, 0.35, 0.95, fr)
    px = 2.4 * out * (1 - back)
    plank.location.x = px; 키_ = plank.keyframe_insert("location", frame=fr)
    # 고양이: 판 왼쪽에서 밀어 내고(3), 오른쪽으로 돌아가 다시 밀어 넣는다(5)
    if fr < L[5][0]:
        x = -1.2 + 0.65 * T.u(1, 0, 0.6, fr); x = max(x, px - 0.78) if out > 0 else x
        x = -0.55 + (px - 0.0) if out > 0 else x; rz = 0.0
    else:
        go = T.u(5, 0, 0.35, fr); x = (2.4 - 0.55) + 1.4 * go * (1 - go) * 0 ; x = 1.85 + 1.0 * math.sin(math.pi * go) if go < 1 else px + 0.6; rz = math.pi * min(1, go * 2)
    walk = (0 < T.u(1, 0, 0.6, fr) < 1) or (0 < out < 1) or (0 < back < 1) or (fr >= L[5][0] and T.u(5, 0, 0.35, fr) < 1)
    cat[0].location = (x, -0.05, 0); cat[0].rotation_euler.z = rz
    cat[1].rotation_euler = (0.35 * math.sin(fr / 6) * (T.u(4, 0.2, 0.3, fr) - T.u(5, 0, 0.1, fr)), -0.5, 0)
    (cat[0].keyframe_insert("location", frame=fr), cat[0].keyframe_insert("rotation_euler", frame=fr), cat[1].keyframe_insert("rotation_euler", frame=fr))
    고양이_키(cat, fr, walk)
    show_t = (L[1][0] + 8 <= fr < L[3][0]) or fr >= L[6][0]
    show_f = L[4][0] + 4 <= fr < L[5][0] + 10
    pulse = 1 + 0.15 * math.sin(fr / 2.5)
    for o in tj: o.hide_render = not show_t; o.scale = (pulse,) * 3; o.keyframe_insert("hide_render", frame=fr); o.keyframe_insert("scale", frame=fr)
    for o in fe: o.hide_render = not show_f; o.scale = (pulse,) * 3; o.keyframe_insert("hide_render", frame=fr); o.keyframe_insert("scale", frame=fr)
    c = cams["front"][0]; c.location.y = -4.0 + 0.5 * fr / T.end; c.keyframe_insert("location", frame=fr)
    c = cams["back"][0]; c.location.x = 0.9 - 0.9 * T.u(5, 0, 1, fr); c.keyframe_insert("location", frame=fr)
끝(T, cams)
