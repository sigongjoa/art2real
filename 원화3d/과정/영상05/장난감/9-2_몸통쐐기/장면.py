"""9-2 몸통 쐐기 — Vanderpoel 1907 p161. 마네킹 받침 위 몸통이 삼각 면 조각으로 솟아 짜이고 · 가슴 쐐기(위가 넓음) · 골반 쐐기(아래로 좁음)에 색 · 해가 돌며 면마다 밝기 · 매끈한 살이 반투명으로 덮인다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def color(m, c, fr):
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Base Color"].default_value = (*c, 1)
    p.inputs["Base Color"].keyframe_insert("default_value", frame=fr)
lerp = lambda a, b, k: tuple(x + (y - x) * k for x, y in zip(a, b))

# 몸통 단면 고리: (높이, 반폭, 반깊이) — 위에서 아래로
RINGS = [(1.55, 0.11, 0.09), (1.45, 0.34, 0.14), (1.25, 0.3, 0.17), (1.05, 0.24, 0.15), (0.92, 0.2, 0.12), (0.78, 0.27, 0.15), (0.62, 0.13, 0.1)]
NS = 8
def loft(name, scale=1.0):
    bm = bmesh.new(); rings = []
    for z, a, b in RINGS:
        rings.append([bm.verts.new((a * scale * math.cos(2 * math.pi * (k + 0.5) / NS), b * scale * math.sin(2 * math.pi * (k + 0.5) / NS), z)) for k in range(NS)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(NS): bm.faces.new((r0[k], r0[(k + 1) % NS], r1[(k + 1) % NS], r1[k]))
    bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

BASE, CH, PE = (0.93, 0.86, 0.74), (1.0, 0.55, 0.45), (0.45, 0.62, 0.95)
mch, mmid, mpe = mat("가슴쐐기", BASE, 0.6), mat("허리", BASE, 0.6), mat("골반쐐기", BASE, 0.6)
# 조각: 사각 면을 삼각 둘로 쪼개 따로 둔다(솟아 날아와 짜인다)
src = loft("틀"); bm = bmesh.new(); bm.from_mesh(src.data); bmesh.ops.triangulate(bm, faces=bm.faces)
pieces = []
for f in bm.faces:
    pts = [v.co.copy() for v in f.verts]; c = sum(pts, Vector()) / len(pts)
    me = bpy.data.meshes.new("면"); me.from_pydata([p - c for p in pts], [], [list(range(len(pts)))]); me.update()
    o = bpy.data.objects.new("면", me); bpy.context.scene.collection.objects.link(o)
    put(o, mch if c.z > 1.08 else (mpe if c.z < 0.9 else mmid), None, c); o.modifiers.new("t", "SOLIDIFY").thickness = 0.012
    o["home"] = list(c); n = f.normal.copy(); o["n"] = list(n); pieces.append(o)
bm.free(); bpy.data.objects.remove(src)
T0 = empty("돌림", loc=(0, 0, 0))
for o in pieces: o.parent = T0
# 살: 같은 틀을 매끈하게 · 조금 크게 · 반투명
skin = mat("살", (0.98, 0.76, 0.62), 0.55, alpha=True); skin.show_transparent_back = False; skin.shadow_method = "HASHED"; sa = alpha_of(skin)
flesh = loft("살", 1.13); flesh.data.materials.append(skin); flesh.parent = T0
flesh.modifiers.new("s", "SUBSURF").levels = 2
for p in flesh.data.polygons: p.use_smooth = True
stand = mat("받침", (0.45, 0.38, 0.35), 0.5)
cyl(0.03, 0.62, stand, loc=(0, 0, 0.31)); cyl(0.3, 0.04, stand, loc=(0, 0, 0.02), bevel=0.015)
sun = next(o for o in bpy.data.objects if o.type == "LIGHT")

cams = {"front": camera("front", (0, -2.6, 1.15), (0, 0, 1.05), 32),
        "close": camera("close", (0.35, -1.6, 1.25), (0, 0, 1.12), 32),
        "side": camera("side", (2.0, -1.4, 1.2), (0, 0, 1.05), 32),
        "low": camera("low", (0.5, -1.7, 0.45), (0, 0, 0.95), 28),
        "orbit": camera("orbit", (0, -2.2, 1.3), (0, 0, 1.1), 32)}

for fr in range(1, T.end + 1):
    t = fr / 24
    T0.rotation_euler.z = 0.5 * math.sin(t * 0.6) + 0.6 * T.u(4, 0, 1, fr); key(T0, fr, "rotation_euler")
    for i, o in enumerate(pieces):
        h = Vector(o["home"]); n = Vector(o["n"])
        k = T.u(0, 0.0 + 0.3 * (1.55 - h.z) / 0.93, 0.25 + 0.3 * (1.55 - h.z) / 0.93, fr) if fr < T.lines[1][0] else 1.0
        k = max(k, T.u(1, 0, 0.3, fr))
        o.location = h + n * 0.6 * (1 - k) + Vector((0, 0, 0.4 * (1 - k)))
        o.scale = (max(0.001, k),) * 3; o.rotation_euler = (2 * (1 - k), 1.5 * (1 - k), 0); key(o, fr, "location", "scale", "rotation_euler")
    color(mch, lerp(BASE, CH, T.u(2, 0.05, 0.4, fr)), fr); color(mpe, lerp(BASE, PE, T.u(3, 0.05, 0.4, fr)), fr)
    a = T.u(4, 0.05, 0.95, fr) * (1 - T.u(5, 0, 0.5, fr))
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30 + 120 * a)); key(sun, fr, "rotation_euler")
    sa.default_value = 0.92 * T.u(5, 0.15, 0.7, fr) * (1 - 0.45 * T.u(6, 0.3, 0.7, fr)); sa.keyframe_insert("default_value", frame=fr)
    flesh.hide_render = fr < T.lines[5][0]; key(flesh, fr, "hide_render")
    oc, _ = cams["orbit"]; b = math.radians(-90 + 50 * math.sin(t * 0.5)); oc.location = (2.2 * math.cos(b), 2.2 * math.sin(b), 1.3); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.35 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
