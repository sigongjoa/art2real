# -*- coding: utf-8 -*-
"""11-5 툴시아니: 회색 원래 모양 옆에 색 상자 묶음. 같은 색 = 같은 부품(좌판은 어느 의자에서나 노랑). 물체마다 빈(empty)에 붙여 돌리고 카메라는 yaw 0."""
import bpy, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
D = os.path.dirname(os.path.abspath(__file__))
GR = (0.78, 0.78, 0.8, 1); CY = (0.45, 0.85, 0.8, 1); YE = (0.9, 0.78, 0.15, 1); BL = (0.15, 0.4, 0.9, 1); OR = (0.95, 0.55, 0.15, 1); RD = (0.8, 0.2, 0.15, 1); TB = (0.25, 0.55, 0.95, 1)
sc = H.scene(res=(2400, 1100)); sc.render.film_transparent = True; sc.display.shading.show_cavity = True
def holder(loc, yaw=35):
    e = bpy.data.objects.new("e", None); sc.collection.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, math.radians(yaw)); return e
def box(p, c, s, col, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=[math.radians(a) for a in rot]); o = bpy.context.object; o.scale = s; o.color = col
    if bevel: m = o.modifiers.new("b", "BEVEL"); m.width = bevel; m.segments = 3
    o.parent = p; return o
def rod(p, a, b, r, col):
    a, b = mathutils.Vector(a), mathutils.Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=24); o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); o.color = col; o.parent = p
    for f in o.data.polygons: f.use_smooth = True
    return o
def blob(p, parts, col):
    for loc, s, ry in parts:
        bpy.ops.object.metaball_add(type="ELLIPSOID", location=loc); m = bpy.context.object; el = m.data.elements[0]
        el.size_x, el.size_y, el.size_z = s; m.rotation_euler = (0, math.radians(ry), 0); m.data.resolution = 0.06; m.data.render_resolution = 0.04; m.color = col; m.parent = p
L4 = [(-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4)]
LC = {(-0.4, -0.4): BL, (0.4, -0.4): RD, (-0.4, 0.4): TB, (0.4, 0.4): OR}
# --- 의자 1: 판 등받이 · 회색 / 상자
p = holder((-9, 0, 2.6))
box(p, (0, 0, 0), (1.0, 1.0, 0.12), GR, bevel=0.03); box(p, (0, 0.45, 1.0), (0.95, 0.1, 1.9), GR, rot=(-6, 0, 0), bevel=0.04)
for x, y in L4: rod(p, (x, y, -0.05), (x * 1.05, y * 1.05, -1.25), 0.05, GR)
p = holder((-6.2, 0, 2.6))
box(p, (0, -0.05, 0), (1.0, 0.95, 0.4), YE); box(p, (0, 0.5, 1.0), (1.0, 0.15, 2.0), CY)
for x, y in L4: box(p, (x * 0.95, y * 0.95, -0.75), (0.18, 0.18, 1.1), LC[(x, y)])
# --- 의자 2: 살 등받이 · 회색 / 상자
p = holder((-0.6, 0, 2.6))
box(p, (0, 0, 0), (0.95, 0.9, 0.08), GR, bevel=0.03)
for x in (-0.42, -0.14, 0.14, 0.42): rod(p, (x, 0.4, 0.05), (x, 0.42, 1.75), 0.035, GR)
box(p, (0, 0.42, 1.8), (1.0, 0.1, 0.18), GR, bevel=0.03)
for x, y in L4: rod(p, (x * 0.95, y * 0.95, -0.05), (x, y, -1.3), 0.045, GR)
p = holder((2.3, 0, 2.6))
box(p, (0, -0.05, 0), (0.9, 0.85, 0.3), YE); box(p, (0, 0.45, 1.0), (0.95, 0.12, 1.8), CY)
for x, y in L4: box(p, (x * 0.9, y * 0.9, -0.75), (0.15, 0.15, 1.15), LC[(x, y)])
# --- 사슴형 네발짐승 / 상자
p = holder((-7.3, 0, -1.6), yaw=-25)
blob(p, [((0, 0, 0.3), (1.0, 0.38, 0.4), 0), ((0.95, 0, 0.85), (0.18, 0.16, 0.5), -30), ((1.25, 0, 1.25), (0.35, 0.16, 0.17), 0)] +
     [((x, y, -0.55), (0.1, 0.1, 0.6), 0) for x in (-0.7, 0.75) for y in (-0.22, 0.22)] + [((-1.05, 0, 0.45), (0.2, 0.08, 0.1), 30)], GR)
p = holder((-3.8, 0, -1.6), yaw=-25)
box(p, (0, 0, 0.35), (2.0, 0.8, 0.85), YE); box(p, (1.15, 0, 1.15), (0.6, 0.55, 0.55), RD, rot=(0, 15, 0))
for x in (-0.7, 0.7): box(p, (x, 0, -0.55), (0.45, 0.65, 1.0), BL)
# --- 꼬리 든 고양이 / 상자
p = holder((0.2, 0, -1.6), yaw=-25)
blob(p, [((0, 0, 0.1), (0.85, 0.3, 0.3), 0), ((0.95, 0, 0.55), (0.25, 0.22, 0.22), 0), ((1.0, 0.1, 0.82), (0.07, 0.05, 0.12), 0), ((1.0, -0.1, 0.82), (0.07, 0.05, 0.12), 0),
         ((-0.9, 0, 0.6), (0.09, 0.09, 0.55), 20)] + [((x, y, -0.55), (0.08, 0.08, 0.45), 0) for x in (-0.6, 0.6) for y in (-0.15, 0.15)], GR)
p = holder((3.6, 0, -1.6), yaw=-25)
box(p, (0, 0, 0.15), (1.8, 0.65, 0.6), YE); box(p, (0.95, 0, 0.6), (0.55, 0.55, 0.55), RD, rot=(0, 10, 0)); box(p, (-0.95, 0, 0.85), (0.2, 0.2, 1.2), RD, rot=(0, -20, 0))
for x in (-0.6, 0.6): box(p, (x, 0, -0.5), (0.35, 0.5, 0.85), BL)
H.look((-2.6, 0, 1.1), 0, 18, ortho=17.5); H.shot(os.path.join(D, "_r", "11-5.png"))
