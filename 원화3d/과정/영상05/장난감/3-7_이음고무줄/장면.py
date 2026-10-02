"""3-7 이음 고무줄 — 큰 공 위에 작은 공이 파고든 덩어리 · 고무줄을 위에 걸든 아래에 걸든 잘록한 오목 골(이음)로 미끄러져 멈춘다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
mint = mat("덩어리", (0.5, 0.82, 0.75), 0.45)
cyl(0.35, 0.25, mat("받침대", (0.85, 0.82, 0.78), 0.8), loc=(0, 0, 0.125), bevel=0.03)
zA, rA, zB, rB = 0.75, 0.55, 1.5, 0.45
ball(rA, mint, loc=(0, 0, zA)); ball(rB, mint, loc=(0, 0, zB))
d = zB - zA; zc = zA + (d * d + rA * rA - rB * rB) / (2 * d)
surf = lambda z: max(math.sqrt(max(rA * rA - (z - zA) ** 2, 0)), math.sqrt(max(rB * rB - (z - zB) ** 2, 0)))
def 줄(rgb):
    m = mat("줄", rgb, 0.4, emit=0.0); p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Emission Color"].default_value = (*rgb, 1)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.028, major_segments=64, minor_segments=12); o = bpy.context.object
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); return o, p
b1, p1 = 줄((0.95, 0.25, 0.3)); b2, p2 = 줄((0.2, 0.45, 0.95))
cat = 고양이("고양이", (-1.0, -0.75, 0)); cat[0].rotation_euler.z = 0.6

cams = {"front": camera("front", (0, -3.8, 1.1), (0, 0, 1.05), 35),
        "close": camera("close", (0.3, -2.2, 1.35), (0, 0, 1.2), 32),
        "low": camera("low", (-0.6, -1.7, 0.5), (0, 0, 1.15), 26),
        "side": camera("side", (2.2, -2.0, 1.6), (0, 0, 1.0), 30),
        "top": camera("top", (0.3, -1.3, 3.0), (0, 0, 1.2), 30)}

def 놓기(b, z, r, fr):
    b.location = (0, 0, z); s = r / 0.4; b.scale = (s, s, 1)
    b.keyframe_insert("location", frame=fr); b.keyframe_insert("scale", frame=fr)
for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    # 빨간 줄: 위에서 내려와(느슨) → 걸림 → 미끄러짐 → 골에서 멈춤(흔들)
    z0 = zB - 0.06
    if fr < T.lines[2][0]:
        u = on(1, 0, 0.9); z = 2.3 + (z0 - 2.3) * u; r = surf(z0) + 0.12 * (1 - on(1, 0.8, 1)) + 0.03 + (0.25 * (1 - u) if fr >= T.lines[1][0] else 0.4)
        if fr < T.lines[1][0]: z = 2.3
    else:
        u = on(2, 0, 1) ** 1.6; z = z0 + (zc + 0.015 - z0) * u
        z += 0.025 * math.sin(math.pi * 3 * on(3, 0, 0.6)) * (1 - on(3, 0, 0.6)); r = surf(z) + 0.02
    놓기(b1, z, r, fr)
    # 파란 줄: 아래 덩어리 허리에서 → 위로 골까지
    if fr < T.lines[4][0]: 놓기(b2, -0.5, 0.01, fr)
    else:
        u = on(4, 0, 0.25); z = zA + 0.12; rr = surf(z) + 0.02 + 0.3 * (1 - u)
        v = on(4, 0.3, 0.95); z = z + (zc - 0.015 - z) * v; rr = rr if v == 0 else surf(z) + 0.02
        놓기(b2, z, rr, fr)
    g = 2.5 * on(5, 0.1, 0.4) * (1 + 0.3 * math.sin(fr / 3))
    for p in (p1, p2): p.inputs["Emission Strength"].default_value = g; p.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    look = (b1.location.z if fr < T.lines[4][0] else b2.location.z)
    cat[1].rotation_euler = (0, -0.3 - 0.25 * (look - 0.8), 0.15 * math.sin(fr / 10)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.x = -1.4 + 0.4 * on(0, 0.1, 0.9); cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.1, 0.9) < 1)
끝(T, cams)
