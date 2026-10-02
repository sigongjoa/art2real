"""5-8 판 관통 덩어리들(Tse 1999 그림13) — 판에 꽂힌 알 · 뿔 · 막대. 눈은 끝 모양으로 판 뒤를 채움 → 판 칠이 위에서 아래로 빠지며 유리판이 되어 확인."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
egg = ball(0.36, mat("알", (0.95, 0.42, 0.55), 0.55), loc=(0, 0.42, 2.35), scale=(4.4, 1, 1))
horn = cone(0.36, 3.2, mat("뿔", (0.98, 0.7, 0.25), 0.55), loc=(0, 0.42, 1.45), rot=(0, math.pi / 2, 0))
bar_o = box((3.1, 0.42, 0.42), mat("막대", (0.4, 0.72, 0.62), 0.55), loc=(0, 0.42, 0.55), bevel=0.06)
things = [egg, horn, bar_o]
glass = mat("유리", (0.7, 0.85, 1.0), 0.2, alpha=True); alpha_of(glass).default_value = 0.18
gb = box((1.0, 0.06, 2.9), glass, loc=(0, -0.1, 1.45), bevel=0.02)
paint = box((1.02, 0.08, 2.9), mat("판", (0.55, 0.7, 0.95), 0.7), loc=(0, -0.1, 1.45), bevel=0.02)
frame_m = mat("틀", (0.85, 0.8, 0.7), 0.8)
for x in (-0.53, 0.53): box((0.06, 0.1, 2.95), frame_m, loc=(x, -0.1, 1.47))
cat = 고양이("고양이", (-1.3, -0.9, 0))

cams = {"front": camera("front", (0, -5.6, 1.5), (0, 0, 1.45), 25),
        "close": camera("close", (0.3, -3.6, 1.55), (0, 0, 1.45), 25),
        "low": camera("low", (1.4, -2.6, 0.25), (0, 0.1, 1.4), 21),
        "top": camera("top", (-1.5, -2.8, 4.0), (0, 0.1, 1.2), 24),
        "orbit": camera("orbit", (0, -5.6, 1.6), (0, 0.1, 1.45), 25)}

for fr in range(1, T.end + 1):
    # 덩어리들 살짝 숨쉬듯 흔들림(판을 꿰뚫은 채 축 방향 미세 이동)
    for k, o in enumerate(things):
        o.location.x = 0.06 * math.sin(fr / 13 + k * 2); o.keyframe_insert("location", frame=fr)
    # 3줄: 판 칠이 위에서 아래로 빠짐(아래쪽 고정)
    d = T.u(3, 0.15, 0.85, fr) if fr >= T.lines[3][0] else 0
    s = max(1 - d, 0.001); paint.scale.z = 2.9 * s; paint.location.z = 1.45 * s; paint.hide_render = s < 0.01
    paint.keyframe_insert("scale", frame=fr); paint.keyframe_insert("location", frame=fr); paint.keyframe_insert("hide_render", frame=fr)
    # 고양이: 판 앞을 왼쪽 → 오른쪽으로 걷다(0~2줄) 3줄엔 앉아 올려다봄 · 4줄 펄쩍
    w = T.u(0, 0.1, 1, fr) * 0.5 + (T.u(2, 0, 0.8, fr) * 0.5 if fr >= T.lines[2][0] else 0)
    hop = 0.3 * math.sin(math.pi * T.u(4, 0.1, 0.3, fr)) if fr >= T.lines[4][0] else 0
    cat[0].location = (-1.3 + 2.4 * w, -0.9, hop); cat[0].keyframe_insert("location", frame=fr)
    walking = (0 < T.u(0, 0.1, 1, fr) < 1) or (fr >= T.lines[2][0] and 0 < T.u(2, 0, 0.8, fr) < 1)
    cat[1].rotation_euler = (0, -0.6, 0.6 * math.sin(fr / 12) if not walking else 0.6); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walking)
    oc, _ = cams["orbit"]; u = T.u(4, 0, 1, fr) if fr >= T.lines[4][0] else 0
    ang = math.radians(-90 + 55 * u); oc.location = (5.6 * math.cos(ang), 5.6 * math.sin(ang), 1.6 + 1.2 * u); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.5 + 1.5 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
