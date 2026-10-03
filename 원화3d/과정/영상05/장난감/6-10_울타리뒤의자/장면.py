"""6-10 울타리 뒤 의자(pix2gestalt 2024 그림1) — 울타리 위로 등받이 · 판만 보인다. 울타리가 땅으로 꺼지면 다리 넷 · 고양이가 의자에 뛰어오른다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

wood = mat("의자", (0.55, 0.75, 0.95), 0.6)
box((0.95, 0.9, 0.09), wood, loc=(0, 0.3, 0.8), bevel=0.03)
box((0.95, 0.09, 0.85), wood, loc=(0, 0.72, 1.27), bevel=0.03)
for x in (-0.4, 0.4):
    for y in (-0.08, 0.68): cyl(0.045, 0.78, wood, loc=(x, y, 0.39))
fm = mat("울타리", (0.97, 0.93, 0.85), 0.7)
fence = empty("울타리")
for k in range(-7, 8):
    box((0.2, 0.06, 0.95), fm, fence, (k * 0.27, -0.45, 0.475), bevel=0.02)
    cone(0.14, 0.14, fm, fence, (k * 0.27, -0.45, 1.0), rot=(0, 0, math.pi / 4)).scale = (1, 0.3, 1)
for z in (0.25, 0.7): box((4.2, 0.04, 0.1), fm, fence, (0, -0.5, z))

cat = 고양이("고양이", (-1.5, -1.1, 0)); cat[0].scale = (1.4, 1.4, 1.4)
cams = {"front": camera("front", (0, -4.0, 1.0), (0, 0, 0.95), 30),
        "close": camera("close", (0.15, -2.9, 1.05), (0, 0, 0.95), 28),
        "low": camera("low", (-0.4, -3.0, 0.3), (0, 0, 0.9), 22),
        "side": camera("side", (1.7, -3.2, 1.3), (0, 0.2, 0.75), 26),
        "wide": camera("wide", (0, -5.0, 1.5), (0, 0, 0.9), 28)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    sink = T.u(3, 0.1, 0.8, fr)
    fence.location.z = -1.15 * sink + 0.04 * math.sin(math.pi * sink * 6) * (0 < sink < 1)
    fence.keyframe_insert("location", frame=fr)
    # 고양이: 울타리 앞을 서성이다 · 걷히면 의자로 걸어가 판 위로 폴짝
    x, y, z, walk = -1.5 + 0.35 * math.sin(fr / 30), -1.1, 0.0, True
    w = T.u(4, 0.0, 0.5, fr); j = T.u(4, 0.5, 0.9, fr)
    if w > 0: x, y = x + (-0.75 - x) * w, -1.1 + 0.9 * w; walk = w < 1
    if j > 0: x = -0.75 + 0.75 * j; y = -0.2 + 0.35 * j; z = 0.85 * j + 0.4 * math.sin(math.pi * j); walk = False
    cat[0].location = (x, y, z); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.35, 0.35 * math.sin(fr / 10)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    for k, (c, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        c.location = p; c.keyframe_insert("location", frame=fr)
끝(T, cams)
