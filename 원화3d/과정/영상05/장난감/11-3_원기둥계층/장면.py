"""11-3 Marr–Nishihara 원기둥 계층 — 원기둥 하나(전신) → 몸통 · 머리 · 팔 · 다리 → 오른팔이 위팔 · 아래팔 · 손 → 손이 손바닥 + 손가락 다섯. 고양이도 원기둥 나무."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
items = []                                    # (obj, 중심, 나타날 창, 사라질 창, 갈라져 나온 자리)
def piece(p, q, r, col, show, hide, origin):
    p, q = Vector(p), Vector(q); o = bar(p, q, r, mat("m%d" % len(items), col, 0.55))
    items.append((o, (p + q) / 2, show, hide, Vector(origin))); return (p + q) / 2
NEVER = (99, 0, 1)
c0 = piece((0, 0, 0.05), (0, 0, 2.65), 0.36, (0.6, 0.68, 0.85), None, (2, 0, 0.35), (0, 0, 1.35))
L1 = (2, 0.15, 0.55)
piece((0, 0, 1.2), (0, 0, 1.95), 0.27, (0.6, 0.75, 0.95), L1, NEVER, c0)                 # 몸통
piece((0, 0, 2.15), (0, 0, 2.55), 0.2, (0.98, 0.82, 0.6), L1, NEVER, c0)                 # 머리
piece((-0.33, 0, 1.9), (-0.72, 0, 1.0), 0.085, (0.45, 0.78, 0.6), L1, NEVER, c0)         # 왼팔
arm = piece((0.33, 0, 1.92), (1.55, 0, 2.02), 0.085, (0.98, 0.6, 0.45), L1, (3, 0.05, 0.4), c0)   # 오른팔(한 개)
piece((-0.15, 0, 1.15), (-0.2, 0, 0.08), 0.11, (0.7, 0.55, 0.9), L1, NEVER, c0)
piece((0.15, 0, 1.15), (0.2, 0, 0.08), 0.11, (0.7, 0.55, 0.9), L1, NEVER, c0)
L2 = (3, 0.15, 0.5)
piece((0.33, 0, 1.92), (0.85, 0, 1.96), 0.09, (0.98, 0.6, 0.45), L2, NEVER, arm)
piece((0.85, 0, 1.96), (1.3, 0, 2.0), 0.08, (0.98, 0.72, 0.3), L2, NEVER, arm)
hand = piece((1.3, 0, 2.0), (1.55, 0, 2.02), 0.07, (0.98, 0.82, 0.6), L2, (4, 0.05, 0.35), arm)
L3 = (4, 0.15, 0.5)
piece((1.3, 0, 2.0), (1.43, 0, 2.01), 0.075, (0.98, 0.82, 0.6), L3, NEVER, hand)          # 손바닥
for k, a in enumerate((-50, -20, 0, 20, 40)):
    d = Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
    base = Vector((1.43, 0, 2.01)) + Vector((0, 0, 0.0)); piece(base + d * 0.02, base + d * (0.15 if k else 0.1), 0.018, (0.95, 0.5, 0.55), L3, NEVER, hand)
root_items = [i[0] for i in items]
cat = 고양이("고양이", (-1.3, -0.5, 0)); cat[0].rotation_euler.z = math.radians(30)

cams = {"front": camera("front", (0.3, -4.8, 1.45), (0.3, 0, 1.4), 26),
        "close": camera("close", (0.5, -3.8, 1.9), (0.3, 0, 1.7), 28),
        "low": camera("low", (1.2, -2.6, 0.25), (0, 0, 1.5), 21),
        "top": camera("top", (-1.6, -3.2, 4.4), (0, 0, 1.4), 24),
        "arm": camera("arm", (1.0, -2.0, 2.05), (0.95, 0, 1.95), 30),
        "hand": camera("hand", (1.45, -0.85, 2.05), (1.45, 0, 2.0), 35),
        "catcam": camera("catcam", (-1.9, -1.6, 0.45), (-1.25, -0.4, 0.3), 26)}

def win(w, fr):
    li, a, b = w
    return 0.0 if li >= len(T.lines) or fr < T.lines[li][0] else T.u(li, a, b, fr)
for fr in range(1, T.end + 1):
    for o, c, show, hide, org in items:
        g = 1.0 if show is None else win(show, fr); h = win(hide, fr)
        s = max(g * (1 - h), 0.001); o.scale = (s, s, s); o.location = org.lerp(c, g) if show else c
        o.hide_render = s < 0.01
        o.keyframe_insert("scale", frame=fr); o.keyframe_insert("location", frame=fr); o.keyframe_insert("hide_render", frame=fr)
    # 고양이: 5줄에 몸이 반투명하게 → 원기둥이 보이게 대신 펄쩍 · 고개
    hop = 0.3 * math.sin(math.pi * win((5, 0.1, 0.35), fr))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.6 + 0.15 * math.sin(fr / 9), 0.3 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    ac, _ = cams["arm"]; ac.location.y = -2.0 + 0.4 * win((3, 0, 1), fr); ac.keyframe_insert("location", frame=fr)
    hc, _ = cams["hand"]; hc.location.y = -0.85 + 0.2 * win((4, 0, 1), fr); hc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.6 + 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
