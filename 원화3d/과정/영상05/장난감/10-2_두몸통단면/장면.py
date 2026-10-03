"""10-2 두 몸통 단면 — 몸통 둘(Plate XXII · XXIII 비교)을 나란히 세우고 높이마다 빛 고리로 자른 뒤, 고리를 각자의 종이 위로 내려 겹쳐 위에서 비교한다(Vanderpoel p.89 · p.91)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
Z0 = 0.5
KEYS = [[(0.0, 0.29, 0.2), (0.3, 0.25, 0.17), (0.6, 0.31, 0.22), (0.85, 0.36, 0.2), (1.0, 0.3, 0.15)],
        [(0.0, 0.33, 0.21), (0.3, 0.21, 0.155), (0.6, 0.27, 0.21), (0.85, 0.3, 0.17), (1.0, 0.25, 0.14)]]
XS = [-0.5, 0.5]
def ab(KEY, z):
    for (z0, a0, b0), (z1, a1, b1) in zip(KEY, KEY[1:]):
        if z <= z1: u = ease((z - z0) / (z1 - z0)); return a0 + (a1 - a0) * u, b0 + (b1 - b0) * u
    return KEY[-1][1:]
NA, NZ = 48, 40
COLS = [(1.0, 0.45, 0.45), (1.0, 0.7, 0.25), (0.45, 0.85, 0.4), (0.3, 0.7, 1.0), (0.7, 0.45, 1.0)]
HS = [0.04, 0.3, 0.6, 0.85, 0.97]
FLAT = Z0 + 0.55
stand = mat("받침", (0.6, 0.45, 0.32), 0.8)
ring_m = [mat("고리%d" % k, c, 0.4, emit=0.7) for k, c in enumerate(COLS)]
paper_m = mat("종이", (1, 1, 1), 1.0, emit=1.3)
torsos, rings, papers, alphas = [], [], [], []
for t, (KEY, x) in enumerate(zip(KEYS, XS)):
    me = bpy.data.meshes.new("몸통"); bm = bmesh.new(); rows = []
    for j in range(NZ + 1):
        z = j / NZ; a, b = ab(KEY, z)
        rows.append([bm.verts.new((a * math.cos(2 * math.pi * i / NA), b * math.sin(2 * math.pi * i / NA), Z0 + z)) for i in range(NA)])
    for j in range(NZ):
        for i in range(NA): bm.faces.new([rows[j][i], rows[j][(i + 1) % NA], rows[j + 1][(i + 1) % NA], rows[j + 1][i]])
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1]); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    m = mat("몸통%d" % t, (0.98, 0.78, 0.62) if t == 0 else (0.98, 0.72, 0.7), 0.6, alpha=True); m.show_transparent_back = False; alphas.append(alpha_of(m))
    o = bpy.data.objects.new("몸통", me); bpy.context.scene.collection.objects.link(o); me.materials.append(m); o.location.x = x; torsos.append(o)
    cyl(0.04, Z0, stand, loc=(x, 0, Z0 / 2)); cyl(0.22, 0.04, stand, loc=(x, 0, 0.02), bevel=0.015)
    for k, h in enumerate(HS):
        a, b = ab(KEY, h)
        bpy.ops.curve.primitive_bezier_circle_add(radius=1); r = bpy.context.object
        r.data.bevel_depth = 0.02; r.data.bevel_resolution = 3; r.scale = (a + 0.012, b + 0.012, 1)
        put(r, ring_m[k], loc=(x, 0, Z0 + h)); rings.append((r, Z0 + h, k))
    papers.append(box((0.85, 0.6, 0.006), paper_m, loc=(x, 0, FLAT - 0.03)))

cat = 고양이("고양이", (-1.3, -0.6, 0))
cams = {"front": camera("front", (0, -3.3, 0.9), (0, 0, 0.95), 32),
        "close": camera("close", (0.3, -2.1, 1.5), (0, 0, 1.0), 30),
        "left": camera("left", (-0.9, -1.7, 1.3), (-0.5, 0, 0.95), 34),
        "right": camera("right", (0.9, -1.7, 1.3), (0.5, 0, 0.95), 34),
        "top": camera("top", (0, -0.3, 4.2), (0, 0, 1.05), 30),
        "topclose": camera("topclose", (-0.5, -0.2, 2.7), (-0.5, 0, 1.05), 36),
        "wide": camera("wide", (0, -3.7, 0.45), (0, 0, 0.9), 30)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    for o in torsos: o.rotation_euler.z = 0.3 * math.sin(fr / 30); o.keyframe_insert("rotation_euler", frame=fr)
    for a in alphas: a.default_value = 1 - 0.85 * g(2, 0.2, 0.7) + 0.85 * g(6, 0.4, 0.9); a.keyframe_insert("default_value", frame=fr)
    flat = g(3, 0.1, 0.7) * (1 - g(6, 0.0, 0.45))
    for r, z, k in rings:
        u = g(1, 0.05 + 0.17 * k, 0.2 + 0.17 * k); s = max(1e-3, u * (1 + 0.3 * math.sin(math.pi * u)))
        r.location.z = z + (FLAT - z) * flat; r.rotation_euler.z = torsos[0].rotation_euler.z
        r.delta_scale = (s, s, 1)
        r.keyframe_insert("location", frame=fr); r.keyframe_insert("rotation_euler", frame=fr); r.keyframe_insert("delta_scale", frame=fr)
    pp = max(1e-3, g(3, 0.4, 0.8) * (1 - g(6, 0.0, 0.3)))
    for p in papers: p.scale = (0.85 * pp, 0.6 * pp, 0.006); p.keyframe_insert("scale", frame=fr)
    walk = g(5, 0.0, 0.9) if fr >= L[5][0] else 0
    w0 = g(1, 0.0, 0.6)
    x = -1.3 + 1.3 * w0 + 1.2 * walk; y = -0.6
    cat[0].location = (x, y, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.6, 0.5 * math.sin(fr / 20)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, (0 < w0 < 1) or (0 < walk < 1))
끝(T, cams)
