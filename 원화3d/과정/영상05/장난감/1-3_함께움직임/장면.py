"""1-3 함께 움직임(Kellman & Spelke 1983) — 나무 판 뒤로 위아래 막대 토막이 같이 왕복 → 하나로 보임 · 판이 올라가면 두 토막. 고양이가 고개로 따라본다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘(비스듬한 카메라에 판 끝이 보이던 것)
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140
wood, post_m, red = mat("판", (0.8, 0.6, 0.38), 0.8), mat("기둥", (0.6, 0.42, 0.26), 0.8), mat("막대", (0.9, 0.25, 0.22), 0.45)
board = box((1.6, 0.07, 1.0), wood, loc=(0, 0, 1.1), bevel=0.02)
posts = [cyl(0.035, 0.6, post_m, loc=(x, 0, 0.3)) for x in (-0.6, 0.6)]
top = cyl(0.1, 0.75, red, loc=(0, 0.16, 1.68))       # z 1.30–2.05 (판 윗변 1.6)
bot = cyl(0.1, 0.7, red, loc=(0, 0.16, 0.6))         # z 0.25–0.95 (판 아랫변 0.6)
cat = 고양이("고양이", (-0.75, -0.9, 0)); cat[0].rotation_euler.z = 0.7

cams = {"front": camera("front", (0, -3.6, 1.15), (0, 0, 1.15), 32),
        "close": camera("close", (0, -2.4, 1.2), (0, 0, 1.2), 30),
        "side": camera("side", (1.2, -2.7, 0.9), (0, 0.1, 1.1), 28),
        "wide": camera("wide", (0, -4.4, 1.4), (0, 0, 1.4), 28),
        "low": camera("low", (0.5, -2.3, 0.3), (0, 0, 1.0), 26)}

for fr in range(1, T.end + 1):
    still = T.u(4, 0.5, 0.9, fr) if fr >= T.lines[4][0] else 0     # 두 토막 공개 뒤엔 멈춤
    x = 0.45 * math.sin(fr / 24 * 2.2) * (1 - still)
    for o in (top, bot): o.location.x = x; o.keyframe_insert("location", frame=fr)
    lift = T.u(3, 0.1, 0.9, fr) if fr >= T.lines[3][0] else 0
    board.location.z = 1.1 + 4.5 * lift; board.rotation_euler.y = 0.15 * math.sin(math.pi * lift)
    board.keyframe_insert("location", frame=fr); board.keyframe_insert("rotation_euler", frame=fr)
    for p in posts: p.location.z = 0.3 + 4.5 * lift; p.keyframe_insert("location", frame=fr)
    # 고양이 고개가 막대를 따라간다(목 yaw) · 공개 순간 고개 위로
    cat[1].rotation_euler = (0, -0.35 - 0.25 * lift, 0.5 * x)
    cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
