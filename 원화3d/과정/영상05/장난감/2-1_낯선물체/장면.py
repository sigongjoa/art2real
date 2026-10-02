"""2-1 낯선 물체 — 지온 다섯 개를 붙인 물건이 돈다. 처음엔 한 색 · 부품마다 색이 켜지고 · 마지막에 쪼개졌다 다시 붙는다(Biederman 1987 그림 1)."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
CREAM = (1.0, 0.94, 0.82)
COLS = [(0.35, 0.6, 0.95), (0.95, 0.45, 0.4), (0.98, 0.8, 0.3), (0.55, 0.85, 0.5), (0.8, 0.5, 0.9)]
piv = empty("물체", loc=(0, 0, 0.95))
mats = [mat("부품%d" % i, CREAM, 0.55) for i in range(5)]
parts = [cyl(0.24, 0.8, mats[0], piv, (0, 0, 0), (0, math.pi / 2, 0), bevel=0.03),          # 원통
         box((0.4, 0.4, 0.3), mats[1], piv, (0, 0, 0.36), bevel=0.03),                       # 상자
         cone(0.22, 0.42, mats[2], piv, (0.61, 0, 0), (0, math.pi / 2, 0)),                   # 원뿔
         None, ball(0.11, mats[4], piv, (0, 0, 0.62))]                                        # 고리 · 공
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, rotation=(math.pi / 2, 0, 0))
parts[3] = put(bpy.context.object, mats[3], piv, (-0.6, 0, 0)); bpy.ops.object.shade_smooth()
home = [p.location.copy() for p in parts]
out_dir = [Vector((0, 0, -0.35)), Vector((0, 0, 0.5)), Vector((0.45, 0, 0)), Vector((-0.45, 0, 0)), Vector((0, 0, 0.9))]
stand = mat("받침", (0.6, 0.45, 0.32), 0.8)
cyl(0.05, 0.75, stand, loc=(0, 0, 0.37)); cyl(0.3, 0.05, stand, loc=(0, 0, 0.025), bevel=0.02)
bsdf = [next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"] for m in mats]

cat = 고양이("고양이", (-1.15, -0.55, 0)); cat[0].rotation_euler.z = 0.45
cams = {"front": camera("front", (0, -2.9, 1.0), (0, 0, 0.95), 35),
        "close": camera("close", (0.8, -2.0, 1.25), (0, 0, 1.0), 35),
        "low": camera("low", (-0.9, -2.4, 0.3), (-0.75, 0, 0.65), 24),
        "side": camera("side", (1.5, -2.2, 1.3), (0, 0, 1.0), 32),
        "top": camera("top", (0.6, -1.8, 2.6), (0, 0, 1.0), 30)}

def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))
L = T.lines
for fr in range(1, T.end + 1):
    piv.rotation_euler.z = fr / FPS * 0.7; piv.keyframe_insert("rotation_euler", frame=fr)
    # 3 번째 줄(i=2): 부품마다 차례로 색 켜기 + 살짝 튀기
    for i, p in enumerate(parts):
        u = T.u(2, 0.1 + 0.16 * i, 0.26 + 0.16 * i, fr) if fr >= L[2][0] else 0
        bsdf[i].default_value = (*lerp(CREAM, COLS[i], u), 1); bsdf[i].keyframe_insert("default_value", frame=fr)
        hop = math.sin(math.pi * u) * 0.12
        ex = (T.u(5, 0.05, 0.35, fr) * (1 - T.u(5, 0.7, 0.95, fr))) if fr >= L[5][0] else 0
        ex += (T.u(4, 0.1, 0.4, fr) * 0.35 * (1 - T.u(4, 0.7, 0.95, fr))) if fr >= L[4][0] else 0
        p.location = home[i] + out_dir[i] * ex + out_dir[i].normalized() * hop
        p.keyframe_insert("location", frame=fr)
        s = 1 + 0.25 * math.sin(math.pi * u); p.scale = (s, s, s) if i != 1 else (0.4 * s, 0.4 * s, 0.3 * s)
        p.keyframe_insert("scale", frame=fr)
    # 고양이: 갸웃 · 쪼개질 때 펄쩍
    tilt = 0.35 * math.sin(fr / 14) if fr < L[2][0] else 0.1 * math.sin(fr / 10)
    jump = math.sin(math.pi * T.u(5, 0.05, 0.3, fr)) * 0.35 if fr >= L[5][0] else 0
    cat[0].location.z = jump; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (tilt, -0.45, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
