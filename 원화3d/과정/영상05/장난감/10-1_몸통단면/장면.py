"""10-1 몸통 단면 — 덩어리 몸통을 높이마다 빛 고리로 자르고, 몸통이 투명해진 뒤 고리들이 한 높이로 내려와 위에서 겹친다 → 다시 쌓여 몸통(Vanderpoel Plate XXII)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
Z0 = 0.5
KEY = [(0.0, 0.3, 0.2), (0.3, 0.25, 0.17), (0.6, 0.31, 0.22), (0.85, 0.36, 0.2), (1.0, 0.3, 0.15)]   # (높이, 반폭, 반두께): 엉덩이 · 허리 · 가슴 · 어깨 · 목밑
def ab(z):
    for (z0, a0, b0), (z1, a1, b1) in zip(KEY, KEY[1:]):
        if z <= z1: u = ease((z - z0) / (z1 - z0)); return a0 + (a1 - a0) * u, b0 + (b1 - b0) * u
    return KEY[-1][1:]
NA, NZ = 48, 40
me = bpy.data.meshes.new("몸통"); bm = bmesh.new(); rows = []
for j in range(NZ + 1):
    z = j / NZ; a, b = ab(z)
    rows.append([bm.verts.new((a * math.cos(2 * math.pi * i / NA), b * math.sin(2 * math.pi * i / NA), Z0 + z)) for i in range(NA)])
for j in range(NZ):
    for i in range(NA): bm.faces.new([rows[j][i], rows[j][(i + 1) % NA], rows[j + 1][(i + 1) % NA], rows[j + 1][i]])
bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1]); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
torso_m = mat("몸통", (0.98, 0.78, 0.62), 0.6, alpha=True); ta = alpha_of(torso_m); torso_m.show_transparent_back = False
torso = bpy.data.objects.new("몸통", me); bpy.context.scene.collection.objects.link(torso); me.materials.append(torso_m)
stand = mat("받침", (0.6, 0.45, 0.32), 0.8); cyl(0.04, Z0, stand, loc=(0, 0, Z0 / 2)); cyl(0.25, 0.04, stand, loc=(0, 0, 0.02), bevel=0.015)

COLS = [(1.0, 0.45, 0.45), (1.0, 0.75, 0.3), (0.55, 0.9, 0.45), (0.35, 0.75, 1.0), (0.75, 0.5, 1.0)]
HS = [0.04, 0.3, 0.6, 0.85, 0.97]
rings = []
for k, h in enumerate(HS):
    a, b = ab(h)
    bpy.ops.curve.primitive_bezier_circle_add(radius=1); r = bpy.context.object
    r.data.bevel_depth = 0.022; r.data.bevel_resolution = 3; r.scale = (a + 0.012, b + 0.012, 1)
    put(r, mat("고리%d" % k, COLS[k], 0.4, emit=0.7), loc=(0, 0, Z0 + h)); rings.append((r, Z0 + h))
FLAT = Z0 + 0.55
paper_m = mat("종이", (1, 1, 1), 1.0, emit=1.3); paper = box((1.1, 0.8, 0.006), paper_m, loc=(0, 0, FLAT - 0.03))

cat = 고양이("고양이", (-0.8, -0.55, 0)); cat[0].rotation_euler.z = 0.4
cams = {"front": camera("front", (0, -3.0, 0.9), (0, 0, 0.95), 40),
        "close": camera("close", (0.5, -1.8, 1.4), (0, 0, 1.0), 36),
        "side": camera("side", (1.5, -2.0, 1.2), (0, 0, 0.95), 36),
        "top": camera("top", (0, -0.4, 2.9), (0, 0, 1.05), 40),
        "topclose": camera("topclose", (0.1, -0.2, 2.3), (0, 0, 1.05), 48),
        "wide": camera("wide", (0, -3.4, 0.5), (0, 0, 0.9), 32)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    torso.rotation_euler.z = 0.35 * math.sin(fr / 30); torso.keyframe_insert("rotation_euler", frame=fr)
    ta.default_value = 1 - 0.85 * g(2, 0.2, 0.7) + 0.85 * g(6, 0.4, 0.9); ta.keyframe_insert("default_value", frame=fr)
    flat = g(3, 0.1, 0.7) * (1 - g(6, 0.0, 0.45))
    for k, (r, z) in enumerate(rings):
        u = g(1, 0.05 + 0.17 * k, 0.2 + 0.17 * k); s = max(1e-3, u * (1 + 0.3 * math.sin(math.pi * u)))
        r.location = (0, 0, z + (FLAT - z) * flat); r.rotation_euler.z = torso.rotation_euler.z
        r.keyframe_insert("location", frame=fr); r.keyframe_insert("rotation_euler", frame=fr)
        r.delta_scale = (s, s, 1); r.keyframe_insert("delta_scale", frame=fr)
    pp = max(1e-3, g(3, 0.4, 0.8) * (1 - g(6, 0.0, 0.3))); paper.scale = (1.1 * pp, 0.8 * pp, 0.006); paper.keyframe_insert("scale", frame=fr)
    walk = g(4, 0.0, 0.9); ang = 0.4 + 2.2 * walk
    cat[0].location = (0.85 * math.cos(math.pi + 0.6 * walk * math.pi) , -0.55 - 0.3 * math.sin(math.pi * walk), 0)
    cat[0].rotation_euler.z = 0.4 - 1.2 * walk
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.6, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < walk < 1)
끝(T, cams)
