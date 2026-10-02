"""9-4 살 · 면 · 뼈 — Vanderpoel 1907 Plate XVII. 받침 위 매끈한 몸통이 옆으로 돈다 · 살이 비치고 면 나눔 선(각진 껍질 + 테두리선)이 드러나고 · 그 안에 등뼈 · 갈비 띠 · 골반이 솟는다 · 끝에 세 겹이 옆으로 갈라져 나란히 선다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def clean(m):
    m.show_transparent_back = False; m.use_backface_culling = True; m.shadow_method = "HASHED"; return m

RINGS = [(1.55, 0.11, 0.09), (1.45, 0.34, 0.14), (1.25, 0.3, 0.17), (1.05, 0.24, 0.15), (0.92, 0.2, 0.12), (0.78, 0.27, 0.15), (0.62, 0.13, 0.1)]
def loft(name, NS, scale=1.0):
    bm = bmesh.new(); rings = []
    for z, a, b in RINGS:
        rings.append([bm.verts.new((a * scale * math.cos(2 * math.pi * (k + 0.5) / NS), b * scale * math.sin(2 * math.pi * (k + 0.5) / NS), z)) for k in range(NS)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(NS): bm.faces.new((r0[k], r0[(k + 1) % NS], r1[(k + 1) % NS], r1[k]))
    bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o

Lf, Lp, Lb = empty("살층"), empty("면층"), empty("뼈층")
fm = clean(mat("살", (0.98, 0.76, 0.62), 0.5, alpha=True)); fa = alpha_of(fm)
flesh = loft("살", 8, 1.05); flesh.data.materials.append(fm); flesh.parent = Lf; flesh.modifiers.new("s", "SUBSURF").levels = 2
for p in flesh.data.polygons: p.use_smooth = True
pm = clean(mat("면", (0.85, 0.88, 1.0), 0.6, alpha=True)); pa = alpha_of(pm)
planes = loft("면", 8, 1.0); planes.data.materials.append(pm); planes.parent = Lp
lines = loft("선", 8, 1.005); lines.data.materials.append(mat("선", (0.15, 0.2, 0.6), 0.5, emit=0.6)); lines.parent = Lp
w = lines.modifiers.new("w", "WIREFRAME"); w.thickness = 0.012
bone = mat("뼈", (0.97, 0.93, 0.82), 0.6)
spine = []
for i in range(14):                              # 등뼈: 등쪽으로 휜 S 곡선
    z = 0.68 + i * 0.065; y = 0.06 + 0.03 * math.sin((z - 0.68) / 0.9 * 2 * math.pi)
    spine.append(cyl(0.028, 0.045, bone, Lb, (0, y, z), bevel=0.01))
ribs = []
for i, zf in enumerate((1.4, 1.33, 1.26, 1.19, 1.12, 1.05)):
    s = 1 - abs(zf - 1.25) * 0.9
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.012, major_segments=64, minor_segments=6)
    r = put(bpy.context.object, bone, Lb, (0, 0.0, zf)); r.scale = (0.24 * s, 0.13 * s, 1); r.rotation_euler.x = -0.25; r["s"] = (0.24 * s, 0.13 * s); ribs.append(r)
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.05, major_segments=48, minor_segments=8)
pelvis = put(bpy.context.object, bone, Lb, (0, 0.02, 0.78)); pelvis.scale = (0.2, 0.12, 1.4); pelvis.rotation_euler.x = 0.3
sternum = box((0.04, 0.03, 0.2), bone, Lb, (0, -0.12, 1.3), bevel=0.01)
bones = spine + ribs + [pelvis, sternum]
for o in bones: o["s0"] = list(o.scale)
stand = mat("받침", (0.45, 0.38, 0.35), 0.5)
cyl(0.03, 0.62, stand, loc=(0, 0, 0.31)); cyl(0.3, 0.04, stand, loc=(0, 0, 0.02), bevel=0.015)
extra = []
for dx in (-0.75, 0.75):
    E_ = empty("받침%d" % dx, loc=(dx, 0, 0)); cyl(0.03, 0.62, stand, E_, (0, 0, 0.31)); cyl(0.3, 0.04, stand, E_, (0, 0, 0.02), bevel=0.015); extra.append(E_)
sun = next(o for o in bpy.data.objects if o.type == "LIGHT")

cams = {"front": camera("front", (0, -2.6, 1.15), (0, 0, 1.05), 32),
        "close": camera("close", (0.3, -1.55, 1.25), (0, 0, 1.12), 32),
        "side": camera("side", (0.7, -2.2, 1.2), (0, 0, 1.08), 32),
        "low": camera("low", (0.5, -1.7, 0.45), (0, 0, 0.95), 28),
        "wide": camera("wide", (0, -3.3, 1.1), (0, 0, 1.0), 28),
        "orbit": camera("orbit", (0, -2.2, 1.3), (0, 0, 1.1), 32)}

for fr in range(1, T.end + 1):
    t = fr / 24
    prof = T.u(1, 0, 0.6, fr)                     # 옆모습으로 돈다
    rz = (0.6 * math.sin(t * 0.8)) * (1 - prof) + (math.pi / 2 + 0.25 * math.sin(t * 0.5)) * prof
    split = T.u(6, 0.05, 0.5, fr)
    for L, dx in ((Lf, -0.75), (Lp, 0.0), (Lb, 0.75)):
        L.rotation_euler.z = rz; L.location.x = dx * split; key(L, fr, "rotation_euler", "location")
    for E_ in extra: E_.scale = (max(0.001, split),) * 3; key(E_, fr, "scale")
    fa.default_value = 1 - 0.85 * T.u(3, 0.0, 0.4, fr) + 0.85 * split; fa.keyframe_insert("default_value", frame=fr)
    show_p = T.u(3, 0.0, 0.4, fr); planes.hide_render = lines.hide_render = show_p < 0.02
    pa.default_value = 0.9 - 0.65 * T.u(4, 0.0, 0.3, fr) + 0.1 * split; pa.keyframe_insert("default_value", frame=fr)
    lines.scale = (max(0.001, show_p),) * 3; key(lines, fr, "scale", "hide_render"); key(planes, fr, "hide_render")
    for i, o in enumerate(bones):
        k = T.u(4, 0.05 + 0.6 * i / len(bones), 0.25 + 0.6 * i / len(bones), fr)
        o.scale = Vector(o["s0"]) * max(0.001, k); o.hide_render = k < 0.02; key(o, fr, "scale", "hide_render")
    a = T.u(2, 0.05, 0.9, fr)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30 + 70 * math.sin(math.pi * a))); key(sun, fr, "rotation_euler")
    oc, _ = cams["orbit"]; b = math.radians(-90 + 50 * math.sin(t * 0.5)); oc.location = (2.2 * math.cos(b), 2.2 * math.sin(b), 1.3); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.3 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
