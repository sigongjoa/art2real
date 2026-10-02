"""3-4 경계의 주인 — 빨강 · 파랑 지온 인형이 겹쳐 씨름 · 겹친 경계선은 앞 인형 색으로 빛남 · 자리를 바꾸면 선의 주인도 바뀐다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
eye = mat("눈", (0.04, 0.04, 0.05), 0.2)
def 인형(name, rgb, x, y, s):
    m = mat(name, rgb, 0.55); root = empty(name, loc=(x, y, 0))
    cyl(0.25, 0.7, m, root, (0, 0, 0.95), bevel=0.08)
    ball(0.21, m, root, (0, 0, 1.52))
    for e in (-1, 1): ball(0.03, eye, root, (e * 0.08, -0.19, 1.56))
    for e in (-1, 1): cyl(0.085, 0.62, m, root, (e * 0.12, 0, 0.31))
    arms = []
    for e in (-1, 1):
        a = empty(name + "팔", root, (e * 0.27, 0, 1.2)); cyl(0.07, 0.5, m, a, (0, 0, -0.25)); a.rotation_euler = (0, -e * s * 1.2, 0); arms.append(a)
    return root, arms
red, ra = 인형("빨강", (0.92, 0.3, 0.25), -0.25, -0.25, 1)
blue, ba = 인형("파랑", (0.3, 0.5, 0.95), 0.25, 0.25, 1)
rg, bg = mat("빨선", (1, 0.3, 0.2), 0.4, emit=1.0), mat("파선", (0.3, 0.6, 1), 0.4, emit=1.0)
rline = cyl(0.035, 0.75, rg, red, (0.255, -0.12, 0.95)); bline = cyl(0.035, 0.75, bg, blue, (-0.255, -0.12, 0.95))
cat = 고양이("고양이", (-1.6, -1.0, 0)); cat[0].rotation_euler.z = 0.4

cams = {"front": camera("front", (0, -4.7, 1.0), (0, 0, 1.0), 35),
        "close": camera("close", (0, -3.1, 1.15), (0, 0, 1.15), 32),
        "side": camera("side", (2.6, -0.4, 1.3), (0, 0, 1.0), 30),
        "top": camera("top", (0.4, -1.4, 3.6), (0, 0, 0.9), 26),
        "wide": camera("wide", (1.8, -3.6, 1.8), (0, 0, 0.8), 28)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    sw = on(4, 0.1, 0.9); arc = math.sin(math.pi * sw)
    wob = 0.05 * math.sin(fr / 4) * (1 - arc)              # 씨름하듯 밀고 당김
    red.location = (-0.25 - 0.5 * arc + wob, -0.25 + 0.5 * sw, 0.03 * abs(math.sin(fr / 4)))
    blue.location = (0.25 + 0.5 * arc + wob, 0.25 - 0.5 * sw, 0.03 * abs(math.cos(fr / 4)))
    red.rotation_euler.z = 0.08 * math.sin(fr / 5); blue.rotation_euler.z = -0.08 * math.sin(fr / 5)
    for o in (red, blue): o.keyframe_insert("location", frame=fr); o.keyframe_insert("rotation_euler", frame=fr)
    for k, a in enumerate(ra + ba):
        e = (-1, 1, -1, 1)[k]; a.rotation_euler = (0.3 * math.sin(fr / 4 + k), -e * (0.85 + 0.25 * math.sin(fr / 3 + k)), 0); a.keyframe_insert("rotation_euler", frame=fr)
    r_on = on(2, 0.1, 0.3) * (1 - on(4, 0, 0.15)); b_on = on(5, 0.1, 0.3)
    pulse = 1 + 0.25 * math.sin(fr / 2.5)
    rline.scale = (r_on * pulse + 1e-3, r_on * pulse + 1e-3, 1); bline.scale = (b_on * pulse + 1e-3, b_on * pulse + 1e-3, 1)
    rline.keyframe_insert("scale", frame=fr); bline.keyframe_insert("scale", frame=fr)
    cat[1].rotation_euler = (0, -0.4, 0.3 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.x = -1.6 + 0.3 * on(0, 0.2, 0.8); cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.2, 0.8) < 1)
    for n, y0 in (("front", -4.7), ("close", -3.1)):
        c = cams[n][0]; c.location.y = y0 + 0.2 * math.sin(fr / 35); c.keyframe_insert("location", frame=fr)
끝(T, cams)
