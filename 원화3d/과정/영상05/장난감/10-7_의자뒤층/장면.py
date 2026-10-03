"""10-7 의자 뒤층 — 정면 카메라엔 안락의자만 · 카메라가 옆으로 밀리면 뒤의 바닥 · 벽 · 숨은 고양이(뒤층)가 드러난다 · 의자가 반투명해지며 두 겹(Dhamo 2019 그림 1)."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
wall_m, floor_m = mat("벽", (0.98, 0.9, 0.75), 0.85), mat("깔개", (0.75, 0.55, 0.85), 0.8)
ch_m = mat("의자", (0.95, 0.48, 0.4), 0.6, alpha=True); ca = alpha_of(ch_m); ch_m.show_transparent_back = False
box((5.0, 0.12, 2.2), wall_m, loc=(0, 1.0, 1.1), bevel=0.02)
box((2.4, 1.6, 0.02), floor_m, loc=(0, 0.2, 0.011), bevel=0.01)
chair = empty("의자")
box((0.8, 0.6, 0.42), ch_m, chair, (0, 0, 0.21), bevel=0.06)
box((0.8, 0.18, 0.62), ch_m, chair, (0, 0.24, 0.72), bevel=0.06)
for s in (-1, 1): box((0.16, 0.6, 0.26), ch_m, chair, (s * 0.4, 0, 0.53), bevel=0.06)
# 뒤층 윤곽: 의자에 가려진 자리 — 깜빡이는 점선 테
glow = mat("뒤층", (0.3, 0.95, 1.0), 0.5, emit=2.5, alpha=True); ga = alpha_of(glow)
dashes = []
for k in range(14):
    a = 2 * math.pi * k / 14; p = Vector((0.55 * math.cos(a), 0.62, 0.45 + 0.42 * math.sin(a)))
    q = Vector((0.55 * math.cos(a + 0.25), 0.62, 0.45 + 0.42 * math.sin(a + 0.25))); dashes.append(bar(p, q, 0.015, glow))

cat = 고양이("고양이", (0.05, 0.62, 0)); cat[0].rotation_euler.z = -math.pi / 2
cams = {"front": camera("front", (0, -3.0, 0.8), (0, 0.3, 0.6), 36),
        "close": camera("close", (0, -2.0, 0.75), (0, 0.3, 0.55), 34),
        "slide": camera("slide", (0, -3.0, 0.8), (0, 0.4, 0.5), 34),
        "peek": camera("peek", (1.6, -1.2, 1.2), (0.0, 0.55, 0.3), 34),
        "top": camera("top", (0.3, -1.3, 2.9), (0, 0.4, 0.3), 30),
        "wide": camera("wide", (0.8, -3.6, 0.6), (0, 0.4, 0.7), 30)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    sl = g(2, 0.0, 1.0); sc = cams["slide"][0]
    a = math.radians(-90 + 55 * sl); sc.location = (3.0 * math.cos(a), 0.3 + 3.3 * math.sin(a), 0.8 + 0.6 * sl); sc.keyframe_insert("location", frame=fr)
    ghost = g(4, 0.1, 0.5) * (1 - g(6, 0.3, 0.8)); ca.default_value = 1 - 0.7 * ghost; ca.keyframe_insert("default_value", frame=fr)
    blink = ghost * (0.6 + 0.4 * math.sin(fr / 3)); ga.default_value = blink; ga.keyframe_insert("default_value", frame=fr)
    for d in dashes: d.hide_render = ghost <= 0.01; d.keyframe_insert("hide_render", frame=fr)
    chair.scale = (1, 1, 1 + 0.05 * math.sin(math.pi * g(1, 0.1, 0.4))); chair.keyframe_insert("scale", frame=fr)
    peek = g(3, 0.3, 0.6) * (1 - g(5, 0.6, 0.9))
    cat[0].location = (0.05 + 0.45 * peek, 0.62, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 9), -0.2, 0.5 * peek * math.sin(fr / 6)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < peek < 1)
끝(T, cams)
