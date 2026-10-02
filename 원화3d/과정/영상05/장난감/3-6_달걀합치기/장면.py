"""3-6 달걀 합치기(Hoffman & Singh 1997) — 고양이가 달걀 하나를 머리로 밀어 다른 달걀에 파묻는다 · 옆 눈금이 골의 꺾임(부품의 세기)을 보여 준다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
egg = mat("달걀", (0.98, 0.72, 0.55), 0.45)
SX, SY = 0.5, 0.38
A = ball(1, egg, loc=(-0.8, 0, SY), scale=(SX, SY, SY))
B = ball(1, egg, loc=(0.8, 0, SY), scale=(SX, SY, SY))
for o in (A, B): o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
glass, fillm, ink = mat("유리", (0.9, 0.95, 1.0), 0.2), mat("눈금", (1.0, 0.35, 0.2), 0.4, emit=1.5), mat("글씨", (0.1, 0.1, 0.14), 0.5)
MX = -1.35
cyl(0.11, 1.3, glass, loc=(MX, 0.3, 0.7)); cyl(0.16, 0.08, ink, loc=(MX, 0.3, 0.04))
fill = cyl(0.085, 1.0, fillm, loc=(MX, 0.3, 0.08)); fill.data.vertices.foreach_set("co", [c for v in fill.data.vertices for c in (v.co.x, v.co.y, v.co.z + 0.5)])
FONT = bpy.data.fonts.load("C:/Windows/Fonts/malgunbd.ttf")
bpy.ops.object.text_add(location=(MX, 0.15, 1.5), rotation=(math.pi / 2, 0, 0)); t = bpy.context.object
t.data.body = "골 꺾임"; t.data.font = FONT; t.data.size = 0.16; t.data.align_x = "CENTER"; t.data.extrude = 0.01; t.data.materials.append(ink)
cat = 고양이("고양이", (1.65, -0.0, 0)); cat[0].rotation_euler.z = math.pi

cams = {"front": camera("front", (0, -3.6, 1.0), (0, 0, 0.6), 28),
        "close": camera("close", (0.0, -1.9, 0.75), (0, 0, 0.4), 30),
        "low": camera("low", (-0.5, -1.6, 0.15), (0.0, 0, 0.45), 24),
        "side": camera("side", (1.6, -2.4, 1.3), (0, 0, 0.35), 28),
        "meter": camera("meter", (-0.5, -3.0, 0.9), (-0.6, 0, 0.6), 30)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    c = 0.8 - 0.3 * on(1, 0, 0.5) - 0.32 * on(3, 0, 0.9) + 0.03 * math.sin(fr / 6) * on(4)
    A.location.x, B.location.x = -c, c
    A.keyframe_insert("location", frame=fr); B.keyframe_insert("location", frame=fr)
    turn = 1 - (2 / math.pi) * math.acos(min(c / SX, 1)) if c < SX else 0      # 0..1 (닿는 순간 1)
    k = (turn if c < SX else 0.0) + 0.02
    fill.scale = (1, 1, k * 1.15); fill.keyframe_insert("scale", frame=fr)
    pushing = fr < T.lines[5][0]
    cat[0].location.x = c + SX + 0.35 + (0.4 * on(5, 0, 0.5)); cat[0].keyframe_insert("location", frame=fr)
    moving = (0 < on(1, 0, 0.5) < 1) or (0 < on(3, 0, 0.9) < 1)
    cat[1].rotation_euler = (0, 0.25 if pushing else -0.5, 0.3 * math.sin(fr / 9) * (not pushing)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, moving)
끝(T, cams)
