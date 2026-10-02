# -*- coding: utf-8 -*-
"""10-5 StdGEN 생각: 입은 캐릭터 → 몸 · 옷 · 머리카락 따로 → 옷을 반으로 자르면 속이 빈 껍질(몸은 그 안에). 얼굴은 그리지 않는다."""
import bpy, bmesh, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
D = os.path.dirname(os.path.abspath(__file__)); V = mathutils.Vector
SKIN = (0.95, 0.8, 0.7, 1); CL = (0.3, 0.38, 0.65, 1); HR = (0.5, 0.33, 0.62, 1)
sc = H.scene(res=(2600, 1100)); sc.render.film_transparent = True; sc.display.shading.show_cavity = True
sc.display.shading.show_backface_culling = False
def meta(fam, parts, col):
    first = None
    for i, (loc, s, ry) in enumerate(parts):
        bpy.ops.object.metaball_add(type="ELLIPSOID", location=loc); m = bpy.context.object; m.name = fam if i == 0 else "%s.%03d" % (fam, i)
        el = m.data.elements[0]; el.size_x, el.size_y, el.size_z = s; m.rotation_euler = (0, math.radians(ry), 0); m.data.resolution = 0.012; m.data.render_resolution = 0.012
        first = first or m
    for o in sc.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = first; first.select_set(True); bpy.ops.object.convert(target="MESH")
    o = bpy.context.object; o.color = col
    for x in [x for x in sc.objects if x.type == "META"]: bpy.data.objects.remove(x)
    for f in o.data.polygons: f.use_smooth = True
    return o
BODY = [((0, 0, 1.58), (0.1, 0.11, 0.12), 0), ((0, 0, 1.44), (0.05, 0.05, 0.08), 0), ((0, 0, 1.25), (0.17, 0.11, 0.17), 0), ((0, 0, 1.03), (0.13, 0.09, 0.12), 0), ((0, 0, 0.89), (0.17, 0.11, 0.1), 0)]
for s in (-1, 1):
    BODY += [((s * 0.09, 0, 0.62), (0.075, 0.075, 0.27), 0), ((s * 0.09, 0, 0.22), (0.055, 0.055, 0.25), 0), ((s * 0.09, -0.04, 0.02), (0.05, 0.09, 0.03), 0),
             ((s * 0.25, 0, 1.22), (0.05, 0.05, 0.15), -s * 35), ((s * 0.37, 0, 1.0), (0.04, 0.04, 0.14), -s * 30)]
HAIR = [((0, 0.025, 1.61), (0.125, 0.125, 0.135), 0), ((0, 0.07, 1.42), (0.12, 0.06, 0.2), 0)]
def dress():
    prof = [(1.42, 0.075), (1.37, 0.17), (1.25, 0.205), (1.03, 0.165), (0.9, 0.215), (0.78, 0.27), (0.62, 0.34)]
    rings = []
    for k in range(40):
        z = 1.42 - (1.42 - 0.62) * k / 39
        for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
            if z1 <= z <= z0: r = r0 + (r1 - r0) * (z0 - z) / (z0 - z1); break
        rings.append([(r * math.cos(2 * math.pi * j / 64), 0.72 * r * math.sin(2 * math.pi * j / 64), z) for j in range(64)])
    vs = [v for r in rings for v in r]; fs = [(i * 64 + j, i * 64 + (j + 1) % 64, (i + 1) * 64 + (j + 1) % 64, (i + 1) * 64 + j) for i in range(39) for j in range(64)]
    me = bpy.data.meshes.new("옷"); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new("옷", me); sc.collection.objects.link(o); o.color = CL
    for f in me.polygons: f.use_smooth = True
    m = o.modifiers.new("두께", "SOLIDIFY"); m.thickness = 0.018; bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="두께")
    return o
def cut_front(o, sx=1):                  # 앞(-y) 의 한쪽 4 분의 1 을 도려낸다(속이 보이게)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < 0 and v.co.x * sx > 0], context="VERTS")
    bm.to_mesh(o.data); bm.free()
def place(o, x): o.location.x += x
X = [-3.6, -1.95, -1.05, -0.15, 1.6, 3.1]
b = meta("몸", BODY, SKIN); place(b, X[0]); d = dress(); place(d, X[0]); h = meta("머리", HAIR, HR); place(h, X[0])
b = meta("몸", BODY, SKIN); place(b, X[1]); d = dress(); place(d, X[2]); h = meta("머리", HAIR, HR); place(h, X[3])
d = dress(); cut_front(d); place(d, X[4])
b = meta("몸", BODY, SKIN); place(b, X[5]); d = dress(); cut_front(d); place(d, X[5]); h = meta("머리", HAIR, HR); place(h, X[5])
H.look((-0.25, 0, 0.85), 0, 22, ortho=8.3)
for o in sc.objects:          # 물체마다 30° 돌려 안쪽이 보이게 (카메라는 yaw 0 · 줄이 기울지 않게)
    if o.type == "MESH":
        cx = round(o.location.x, 2); o.location.x = 0; bpy.context.view_layer.update()
        o.rotation_euler.z = math.radians(-30); o.location.x = cx
H.shot(os.path.join(D, "_r", "10-5.png"))
