"""5-4 윤곽은 이어지는데 완성 실패(Tse 1999 그림3) — 판 뒤 블록 둘: 정면에선 윗선 · 아랫선이 맞지만 왼쪽은 얇고 앞, 오른쪽은 두껍고 뒤. 판이 들리면 고양이가 틈으로 지나감."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
CZ, CY = 1.6, -5.4                                  # 정면 카메라 높이 · 위치
H = 1.2                                              # 왼쪽 블록 앞면 높이
yL, tL = -0.15, 0.3                                  # 왼쪽: 앞면 y, 두께
yR, tR = 0.55, 1.1                                   # 오른쪽: 앞면 y, 두께
hR = H * (yR - CY) / (yL - CY)                       # 정면에서 윗선 · 아랫선이 맞도록
left = box((1.4, tL, H), mat("왼쪽", (0.98, 0.55, 0.35), 0.6), loc=(-1.0, yL + tL / 2, CZ), bevel=0.03)
right = box((1.4, tR, hR), mat("오른쪽", (0.4, 0.75, 0.6), 0.6), loc=(1.0 * (yR - CY) / (yL - CY), yR + tR / 2, CZ), bevel=0.03)
leg = mat("다리", (0.85, 0.8, 0.7), 0.8)
for o, h, t in ((left, H, tL), (right, hR, tR)):           # 받침 다리(블록이 떠 보이지 않게)
    zb = CZ - h / 2
    for dx in (-0.45, 0.45): cyl(0.07, zb, leg, loc=(o.location.x + dx, o.location.y, zb / 2))
board = box((0.9, 0.08, 3.4), mat("판", (0.55, 0.7, 0.95), 0.7), loc=(0, -0.6, 1.7), bevel=0.03)
# 정면에서 이어 보이는 윗선 · 아랫선 — 주황 막대(2줄)
glow = mat("선", (1.0, 0.45, 0.08), 0.5, emit=2.2, alpha=True); ga = alpha_of(glow)
lines = [bar((-1.75, -0.8, CZ + s * (H / 2) * (-0.8 - CY) / (yL - CY)), (1.75, -0.8, CZ + s * (H / 2) * (-0.8 - CY) / (yL - CY)), 0.018, glow) for s in (-1, 1)]
cat = 고양이("고양이", (0, -1.6, 0)); cat[0].rotation_euler.z = math.pi / 2

cams = {"front": camera("front", (0, CY, CZ), (0, 0, CZ), 25),
        "close": camera("close", (0, -3.6, CZ), (0, 0, CZ), 26),
        "orbit": camera("orbit", (0, CY, CZ), (0, 0.3, 1.4), 25),
        "top": camera("top", (2.6, -2.6, 4.4), (0, 0.3, 1.2), 24),
        "low": camera("low", (-1.6, -2.4, 0.3), (0.2, 0.3, 1.3), 21),
        "catcam": camera("catcam", (0, -2.6, 0.5), (0, 1.0, 0.4), 24)}

for fr in range(1, T.end + 1):
    a = 0.9 * T.u(1, 0.1, 0.4, fr) * (1 - T.u(2, 0, 0.3, fr)) if T.lines[1][0] <= fr < T.lines[3][0] else 0
    ga.default_value = a; ga.keyframe_insert("default_value", frame=fr)
    for l in lines: l.hide_render = a < 0.02; l.keyframe_insert("hide_render", frame=fr)
    # 궤도: 2줄에 정면 → 오른쪽 45° · 5줄에 다시 반대편으로
    oc, _ = cams["orbit"]
    u = T.u(2, 0, 0.8, fr) if fr >= T.lines[2][0] else 0
    if fr >= T.lines[5][0]: u = 1 - 1.8 * T.u(5, 0, 1, fr)
    ang = math.radians(-90 + 50 * u); oc.location = (-CY * math.cos(ang), -CY * math.sin(ang), CZ + 0.8 * abs(u))
    oc.keyframe_insert("location", frame=fr)
    # 판: 4줄에 들림 · 고양이가 틈으로 지나감
    lift = T.u(4, 0, 0.35, fr) if fr >= T.lines[4][0] else 0
    board.location.z = 1.7 + 4.0 * lift; board.keyframe_insert("location", frame=fr)
    w = T.u(4, 0.3, 1.0, fr) if fr >= T.lines[4][0] else 0
    cat[0].location = (0, -1.6 + 3.6 * w, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.3 * (1 - w) + 0.1 * w, 0.4 * math.sin(fr / 10) * (1 - w)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < w < 1)
    cc, ct = cams["catcam"]; cc.location.y = -2.6 + 2.4 * w; ct.location.y = 1.0 + 2.4 * w
    cc.keyframe_insert("location", frame=fr); ct.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = 2.6 - 0.8 * math.sin(fr / 30); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
