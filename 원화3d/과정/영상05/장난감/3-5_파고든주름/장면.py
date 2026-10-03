"""3-5 파고든 주름(횡단성) — 큰 공에 작은 공이 파고들어 한 덩어리 · 이음에 빛나는 고리 · 작은 공이 표면을 돌아다녀도 고리는 늘 오목한 골에 · 큰 고양이 머리가 목 골에서 톡 떨어졌다 붙음."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
lav = mat("덩어리", (0.72, 0.56, 0.92), 0.45)
cyl(0.45, 0.3, mat("받침대", (0.85, 0.82, 0.78), 0.8), loc=(-0.3, 0, 0.15), bevel=0.04)
A, rA, rB = Vector((-0.3, 0, 0.8)), 0.55, 0.42
ball(rA, lav, loc=A)
bpy.ops.mesh.primitive_uv_sphere_add(radius=rB, segments=48, ring_count=24); B = bpy.context.object; bpy.ops.object.shade_smooth(); B.data.materials.append(lav)
glow = mat("골", (1.0, 0.45, 0.1), 0.4, emit=1.4)
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.09, major_segments=64, minor_segments=12); ring = bpy.context.object
bpy.ops.object.shade_smooth(); ring.data.materials.append(glow); ring.rotation_mode = "QUATERNION"
big = 고양이("큰고양이", (4.2, -0.2, 0)); big[0].scale = (2.6, 2.6, 2.6); big[0].rotation_euler.z = math.pi
cat = 고양이("고양이", (-1.6, -0.9, 0)); cat[0].rotation_euler.z = 0.3

cams = {"front": camera("front", (0, -3.6, 0.95), (0, 0, 0.95), 35),
        "close": camera("close", (0.3, -2.2, 1.2), (0.05, 0, 0.95), 30),
        "low": camera("low", (-0.6, -1.9, 0.35), (0, 0, 0.9), 26),
        "side": camera("side", (2.0, -2.2, 1.6), (0, 0, 0.9), 30),
        "top": camera("top", (-0.2, -1.2, 3.3), (0, 0, 0.8), 28),
        "cat": camera("cat", (2.4, -3.2, 0.9), (2.4, 0, 0.6), 30),
        "catclose": camera("catclose", (1.9, -1.6, 1.0), (2.05, 0, 0.75), 30)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    phi = 0.23 + 0.9 * math.sin(math.pi * on(3, 0, 1)) - 0.5 * math.sin(2 * math.pi * on(3, 0, 1))
    th = 0.6 * math.sin(2 * math.pi * on(3, 0, 1))
    d = 0.68 - 0.1 * math.sin(math.pi * on(3, 0, 1))
    pull = math.sin(math.pi * on(4, 0.1, 0.8)); d += 0.75 * pull
    dirv = Vector((math.cos(phi) * math.cos(th), -math.cos(phi) * math.sin(th), math.sin(phi)))
    jig = 1 + 0.04 * math.sin(fr / 2.2) * (fr < T.lines[2][0])
    B.location = A + dirv * d; B.scale = (jig, jig, 2 - jig)
    B.keyframe_insert("location", frame=fr); B.keyframe_insert("scale", frame=fr)
    a = (d * d + rA * rA - rB * rB) / (2 * d); h = math.sqrt(max(rA * rA - a * a, 0)) if d < rA + rB else 0
    vis = on(2, 0.1, 0.35) * (1 + 0.08 * math.sin(fr / 2.5))
    ring.location = A + dirv * a; ring.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
    ring.scale = [max(h * vis, 1e-3)] * 3
    ring.keyframe_insert("location", frame=fr); ring.keyframe_insert("rotation_quaternion", frame=fr); ring.keyframe_insert("scale", frame=fr)
    # 큰 고양이: 5 줄에 걸어 들어와 머리가 목 골에서 톡
    w = on(5, 0, 0.45); big[0].location.x = 4.2 - 1.6 * w; big[0].keyframe_insert("location", frame=fr)
    pop = math.sin(math.pi * on(5, 0.5, 0.95)); big[1].location = (0.2 + 0.1 * pop, 0, 0.3 + 0.12 * pop)
    big[1].rotation_euler = (0, -0.2 - 0.4 * pop, 0); big[1].keyframe_insert("location", frame=fr); big[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(big, fr, 0 < w < 1)
    cat[1].rotation_euler = (0, -0.5, 0.35 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.x = -1.9 + 0.5 * on(0, 0.1, 0.9); cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.1, 0.9) < 1)
끝(T, cams)
