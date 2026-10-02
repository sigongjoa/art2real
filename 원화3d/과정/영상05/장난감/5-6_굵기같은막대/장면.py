"""5-6 판 양쪽 그루터기 병합(Tse 1999 그림18) — 판 위쪽 막대는 양쪽 굵기가 같고(한 개) 아래쪽은 굵기가 다름(두 개). 고양이가 밀어서 확인."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
ZT, ZB = 1.25, 0.42
rod = cyl(0.15, 2.9, mat("위막대", (0.95, 0.42, 0.55), 0.55), loc=(0, 0.25, ZT), rot=(0, math.pi / 2, 0), bevel=0.04)
thick = cyl(0.26, 1.35, mat("굵은", (0.4, 0.72, 0.62), 0.55), loc=(-0.78, 0.25, ZB), rot=(0, math.pi / 2, 0), bevel=0.05)
thin = cyl(0.09, 1.35, mat("가는", (0.98, 0.7, 0.25), 0.55), loc=(0.78, 0.25, ZB), rot=(0, math.pi / 2, 0), bevel=0.03)
board = box((0.85, 0.08, 1.85), mat("판", (0.55, 0.7, 0.95), 0.7), loc=(0, -0.1, 0.925), bevel=0.03)
cat = 고양이("고양이", (1.95, -0.05, 0)); cat[0].rotation_euler.z = math.pi
cams = {"front": camera("front", (0, -4.3, 1.1), (0, 0, 0.85), 24),
        "close": camera("close", (0.4, -2.7, 1.0), (0.1, 0, 0.8), 25),
        "low": camera("low", (1.8, -1.9, 0.2), (0.2, 0.2, 0.7), 21),
        "top": camera("top", (-1.0, -2.4, 3.2), (0, 0.2, 0.7), 24),
        "catcam": camera("catcam", (2.9, -1.1, 0.7), (0.3, 0.2, 0.8), 24)}

for fr in range(1, T.end + 1):
    p1 = T.u(3, 0.25, 0.55, fr) if fr >= T.lines[3][0] else 0           # 위 막대 밀기(점프)
    p2 = T.u(4, 0.2, 0.5, fr) if fr >= T.lines[4][0] else 0             # 아래 가는 막대 밀기
    rod.location.x = -0.45 * p1; thin.location.x = 0.78 - 0.45 * p2
    rod.keyframe_insert("location", frame=fr); thin.keyframe_insert("location", frame=fr)
    thick.location.z = ZB + 0.02 * math.sin(fr * 2.5) * (T.u(4, 0.5, 0.6, fr) * (1 - T.u(4, 0.7, 0.8, fr)) if fr >= T.lines[4][0] else 0)
    thick.keyframe_insert("location", frame=fr)
    # 고양이: 3줄 앞에서 점프해 위 막대 끝을 밀고 · 4줄에 걸어가 아래 막대를 밈
    x, z, walk = 1.95, 0.0, False
    if fr >= T.lines[3][0]:
        j = T.u(3, 0.05, 0.6, fr); z = 0.8 * math.sin(math.pi * j)
        x = 1.95 - 0.2 * T.u(3, 0.05, 0.25, fr) - 0.45 * p1 + 0.65 * T.u(3, 0.7, 0.95, fr); walk = 0.7 < T.u(3, 0.7, 0.95, fr) < 1 and False
    if fr >= T.lines[4][0]:
        x = 1.95 - 0.2 * T.u(4, 0, 0.15, fr) - 0.45 * p2; walk = 0 < T.u(4, 0, 0.5, fr) < 1
    cat[0].location = (x, -0.05, z); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.5 if fr < T.lines[4][0] else 0.0, 0.3 * math.sin(fr / 12)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    tc, _ = cams["top"]; tc.location.x = -1.0 + 1.6 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.y = -4.3 + 0.4 * math.sin(fr / 50); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
