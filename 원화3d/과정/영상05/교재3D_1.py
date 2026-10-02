# -*- coding: utf-8 -*-
"""교재 그림을 3D 로 다시 짓기 1 차 (10-02): ①-1 지온 만들기(Biederman Fig 7) · ②-5 벌레(Tse Fig 11) · ②-2 한 선화 여러 입체(Malik Fig 31 의 뜻).
blender -b -P 교재3D_1.py  →  out/영상05/3D/*.png"""
import bpy, bmesh, sys, os, math, random, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\3D"
def wb(res):
    sc = H.scene(res=res); sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True; return sc
def smooth(o):
    for p in o.data.polygons: p.use_smooth = True
# ---------- ①-1 지온 만들기: 원통 → 단면 · 굵기 · 축만 바꾼다 ----------
sc = wb((2400, 600)); C = (0.85, 0.85, 0.88, 1); X = [-9, -4.5, 0, 4.5, 9]
def cyl(x, verts=48, r1=1, r2=1, bend=0, barrel=0, color=C):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=4, location=(x, 0, 0), end_fill_type="NGON")
    o = bpy.context.object; o.color = color
    if barrel or bend:
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.subdivide(number_cuts=24); bpy.ops.object.mode_set(mode="OBJECT")
    if barrel:
        for v in o.data.vertices:
            z = v.co.z / 2; k = 1 + barrel * (1 - z * z); v.co.x *= k; v.co.y *= k
    if bend:
        m = o.modifiers.new("b", "SIMPLE_DEFORM"); m.deform_method = "BEND"; m.angle = math.radians(bend); m.deform_axis = "Y"
    if verts > 8: smooth(o)
    return o
cyl(X[0])                                   # 기준: 원통
cyl(X[1], verts=4)                          # 단면 모서리 곧게 → 각기둥
cyl(X[2], r1=1.2, r2=0.05)                  # 굵기 작아짐 → 뿔
cyl(X[3], bend=90)                          # 축 굽힘 → 휜 관
cyl(X[4], barrel=0.6)                       # 커졌다 작아짐 → 통
H.look((0, 0, 0), 20, 15, ortho=24); H.shot(os.path.join(OUT, "g1_지온만들기.png"))
# ---------- ②-5 Tse 벌레: 앞에 세로선 둘, 선 없는 검은 S ----------
sc = wb((900, 1500))
cu = bpy.data.curves.new("worm", "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("BEZIER"); pts = [(0.6, 0, 2.6), (1.0, 0, 1.0), (-0.9, 0, -0.6), (-0.4, 0, -2.4)]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
cu.bevel_depth = 0.9; cu.bevel_resolution = 8; cu.resolution_u = 24
w = bpy.data.objects.new("worm", cu); sc.collection.objects.link(w); w.color = (0, 0, 0, 1)
posts = []
for x in (-0.55, 0.55):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=9, location=(x, -2.5, 0)); p = bpy.context.object; p.color = (0.95, 0.95, 0.95, 1); posts.append(p)
sh = sc.display.shading; sh.light = "FLAT"; sh.show_cavity = False; sc.render.film_transparent = False; sc.world.color = (1, 1, 1)
H.look((0, 0, 0), 0, 0, ortho=7.5); H.shot(os.path.join(OUT, "g2_벌레_그림.png"))
for p in posts: p.color = (0.1, 0.1, 0.1, 1)
w.color = (0.85, 0.85, 0.88, 1); sh.light = "STUDIO"; sh.show_cavity = True; sc.world.color = H.BG
H.look((0, 0, 0), 60, 15, ortho=7.5); H.shot(os.path.join(OUT, "g2_벌레_3D.png"))
# ---------- ②-2 한 선화, 여러 입체: 상자 꼭짓점을 시선 방향으로만 밀기 ----------
sc = wb((2400, 1300)); random.seed(3)
V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
E = [(a, b) for a in range(8) for b in range(a + 1, 8) if sum(V[a][i] != V[b][i] for i in range(3)) == 1]
# 시선 방향 = 카메라 (yaw 30, pitch 25) 쪽. 꼭짓점을 그 축으로만 옮기면 그 카메라에서 선화는 똑같다
yaw, pit = math.radians(30), math.radians(25)
D = mathutils.Vector((math.sin(yaw) * math.cos(pit), -math.cos(yaw) * math.cos(pit), math.sin(pit)))
def wire(name, pts, x0, color):
    me = bpy.data.meshes.new(name); me.from_pydata([mathutils.Vector(p) + mathutils.Vector((x0, 0, 0)) for p in pts], E, []); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); bpy.context.view_layer.objects.active = o
    for x in sc.objects: x.select_set(x == o)
    bpy.ops.object.convert(target="CURVE"); o.data.bevel_depth = 0.06; o.color = color
    for i, p in enumerate(pts):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=mathutils.Vector(p) + mathutils.Vector((x0, 0, 0))); s = bpy.context.object; s.color = color
cols = [(0.9, 0.9, 0.92, 1), (0.95, 0.55, 0.3, 1), (0.35, 0.65, 0.95, 1)]
shapes = [V] + [[tuple(mathutils.Vector(p) + D * random.uniform(-1.6, 1.6)) for p in V] for _ in range(2)]
# 세 개를 화면에서 옆으로 놓되, 옮긴 축이 시선과 같아야 하므로 x0 를 시선에 수직인 화면 가로축으로 둔다
objs = []
for k, (pts, c) in enumerate(zip(shapes, cols)):
    n0 = len(sc.objects); wire("w%d" % k, pts, 0, c); objs.append(list(sc.objects)[n0:])
for k, grp in enumerate(objs):
    for j, g in enumerate(objs):
        for o in g: o.hide_render = (j != k)
    H.look((0, 0, 0), 30, 25, ortho=6); H.shot(os.path.join(OUT, "g3_선화_그시점_%d.png" % k))
    H.look((0, 0, 0), 30 + 75, 5, ortho=8); H.shot(os.path.join(OUT, "g3_선화_돌림_%d.png" % k))
