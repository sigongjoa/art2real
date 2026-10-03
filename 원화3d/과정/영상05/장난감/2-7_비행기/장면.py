"""2-7 비행기 — 몸통 · 날개 · 꼬리 셋이 먼저 날아와 붙고(벌써 비행기), 코 · 꼬리끝 · 꼬리날개 둘 · 엔진 둘이 더해져 아홉 · 마지막에 날아간다(Biederman 1987 그림 13)."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
body_m, wing_m, acc_m, eng_m = mat("동체", (0.95, 0.95, 0.98), 0.45), mat("날개", (0.4, 0.62, 0.95), 0.5), mat("꼬리", (0.95, 0.45, 0.4), 0.5), mat("엔진", (0.98, 0.8, 0.3), 0.5)
plane = empty("비행기", loc=(0, 0, 1.15)); plane.rotation_euler.z = 0.35
P2 = math.pi / 2
parts = [cyl(0.14, 1.3, body_m, plane, (0, 0, 0), (0, P2, 0), bevel=0.03),                 # 1 동체
         box((0.36, 1.9, 0.045), wing_m, plane, (0.05, 0, -0.03), bevel=0.015),          # 2 날개
         box((0.3, 0.04, 0.34), acc_m, plane, (-0.55, 0, 0.27), bevel=0.012),            # 3 꼬리(수직)
         cone(0.14, 0.32, body_m, plane, (0.81, 0, 0), (0, P2, 0)),                     # 4 코
         cone(0.14, 0.3, body_m, plane, (-0.8, 0, 0), (0, -P2, 0)),                     # 5 꼬리 끝
         box((0.2, 0.32, 0.03), acc_m, plane, (-0.62, 0.2, 0.03), bevel=0.01),           # 6 꼬리날개 왼
         box((0.2, 0.32, 0.03), acc_m, plane, (-0.62, -0.2, 0.03), bevel=0.01),          # 7 꼬리날개 오
         cyl(0.07, 0.3, eng_m, plane, (0.12, 0.45, -0.12), (0, P2, 0), bevel=0.015),    # 8 엔진 왼
         cyl(0.07, 0.3, eng_m, plane, (0.12, -0.45, -0.12), (0, P2, 0), bevel=0.015)]   # 9 엔진 오
for p in parts[3:5]: bpy.context.view_layer.objects.active = p; bpy.ops.object.shade_smooth()
home = [(p.location.copy(), p.scale.copy()) for p in parts]
FROM = [Vector((0, 0, 2.0)), Vector((0, -2.5, 0.5)), Vector((-1.5, 0, 1.5)), Vector((2.0, 0, 0.3)), Vector((-2.0, 0, 0.3)),
        Vector((-0.5, 1.8, 0.8)), Vector((-0.5, -1.8, 0.8)), Vector((0.5, 1.5, -1.0)), Vector((0.5, -1.5, -1.0))]
# 언제 오나: (줄, 시작, 끝)
WHEN = [(1, 0.0, 0.25), (1, 0.25, 0.5), (1, 0.5, 0.75), (3, 0.0, 0.2), (3, 0.2, 0.4), (3, 0.45, 0.65), (3, 0.6, 0.8), (4, 0.0, 0.25), (4, 0.2, 0.45)]

cat = 고양이("고양이", (-0.4, -1.1, 0)); cat[0].rotation_euler.z = 0.9
cams = {"front": camera("front", (1.0, -2.6, 2.6), (0, 0, 1.0), 30),
        "close": camera("close", (0.9, -1.7, 2.1), (0, 0, 1.1), 30),
        "side": camera("side", (-0.9, -2.6, 2.2), (0, 0, 1.0), 30),
        "low": camera("low", (0.6, -2.4, 0.2), (0, 0, 0.9), 24),
        "orbit": camera("orbit", (1.0, -2.6, 2.6), (0, 0, 1.0), 30),
        "wide": camera("wide", (0.8, -4.0, 0.6), (0, 0, 1.6), 24)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    for k, p in enumerate(parts):
        u = min(1, 1 - g(0, 0.72, 0.95) + g(*WHEN[k])); loc, sc = home[k]
        p.location = loc + FROM[k] * (1 - u); p.scale = sc * max(1e-3, u)
        p.keyframe_insert("location", frame=fr); p.keyframe_insert("scale", frame=fr)
    fly = g(6, 0.35, 1.0)
    plane.location = (0 + 3.0 * fly * fly, 0.8 * fly * fly, 1.15 + 0.06 * math.sin(fr / 9) + 2.4 * fly * fly)
    plane.rotation_euler = (0.08 * math.sin(fr / 13), -0.35 * fly, 0.55 + 0.1 * math.sin(fr / 21))
    plane.keyframe_insert("location", frame=fr); plane.keyframe_insert("rotation_euler", frame=fr)
    oc = cams["orbit"][0]; a = math.radians(-67 + 70 * g(5, 0, 1)); oc.location = (2.8 * math.cos(a), 2.8 * math.sin(a), 2.6); oc.keyframe_insert("location", frame=fr)
    hop = 0.2 * math.sin(math.pi * g(2, 0.1, 0.4)) + 0.2 * math.sin(math.pi * g(4, 0.5, 0.75))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.25 * math.sin(fr / 11), -0.75 - 0.4 * fly, -0.3 * fly); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
