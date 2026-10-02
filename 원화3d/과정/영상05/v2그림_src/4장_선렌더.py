# -*- coding: utf-8 -*-
"""4-1 … 4-4 · 4-7 바탕: 단순 물체 6 개(손전등 · 컵 · 와인잔 · 물뿌리개 · 가위 · 의자)를 Freestyle 선만 렌더.
blender -b -P 4장_선렌더.py  → src/_raw/선_<이름>.png (투명 바탕 · 검은 선)"""
import bpy, math, os
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_raw")

def new_scene(res=900):
    bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "OBJECT"; sh.show_cavity = False
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"
    sc.world = bpy.data.worlds.new("w"); sc.render.use_freestyle = True; sc.render.line_thickness = 3.0
    fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(110)
    ls = fs.linesets[0]; ls.select_by_visibility = True
    for k in ("silhouette", "border", "crease", "external_contour", "contour"): setattr(ls, "select_" + k, True)
    ls.linestyle = ls.linestyle or bpy.data.linestyles.new("ln"); ls.linestyle.color = (0, 0, 0); ls.linestyle.caps = "ROUND"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"
    return sc

def look(center, yaw, pitch, ortho, dist=40):
    import mathutils
    cam = bpy.context.scene.camera; y, p = math.radians(yaw), math.radians(pitch)
    d = mathutils.Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = mathutils.Vector(center) + d * dist; cam.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); cam.data.ortho_scale = ortho

def fin(o, smooth=True):
    o.color = (1, 1, 1, 1)
    if smooth:
        for pg in o.data.polygons: pg.use_smooth = True
    return o

def lathe(name, prof, steps=96, loc=(0, 0, 0)):
    """prof = [(r, z)] 바깥 → 안. z 축 돌려 깎기."""
    vs, fs = [], []; n = len(prof)
    for j in range(steps):
        a = 2 * math.pi * j / steps
        for r, z in prof: vs.append((r * math.cos(a) + loc[0], r * math.sin(a) + loc[1], z + loc[2]))
    for j in range(steps):
        for i in range(n - 1):
            p = j * n + i; q = ((j + 1) % steps) * n + i; fs.append((p, q, q + 1, p + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return fin(o)

def prim(kind, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**kw); return fin(bpy.context.object)

def torus_part(R, r, loc, rot, arc=360, seg=64):
    """토러스(필요하면 일부 호만)."""
    prim("torus", major_radius=R, minor_radius=r, major_segments=seg, minor_segments=24, location=loc, rotation=rot); return bpy.context.object

def shot(name):
    bpy.context.scene.render.filepath = os.path.join(RAW, "선_%s.png" % name); bpy.ops.render.render(write_still=True)

# 손전등 (교재3D_2 와 같은 꼴)
sc = new_scene()
prim("cylinder", vertices=64, radius=0.55, depth=4.0, rotation=(0, math.pi / 2, 0), location=(0, 0, 0))
prim("cone", vertices=64, radius1=0.55, radius2=1.0, depth=1.3, rotation=(0, math.pi / 2, 0), location=(2.65, 0, 0))
prim("cylinder", vertices=64, radius=1.0, depth=0.35, rotation=(0, math.pi / 2, 0), location=(3.47, 0, 0))
b = prim("cube", size=1, location=(0.6, 0, 0.6)); b.scale = (0.6, 0.3, 0.18)
prim("cylinder", vertices=64, radius=0.62, depth=0.4, rotation=(0, math.pi / 2, 0), location=(-2.15, 0, 0))
look((0.6, 0, 0), 25, 20, ortho=7.0); shot("손전등")

# 컵: 두께 있는 몸통 + 받침 + 손잡이
sc = new_scene()
lathe("cup", [(0.0, 0.0), (0.55, 0.0), (0.62, 0.08), (0.75, 0.25), (1.0, 0.9), (1.12, 1.5), (1.06, 1.5), (0.94, 0.95), (0.7, 0.3), (0.0, 0.3)])
torus_part(0.38, 0.06, (1.12, 0, 0.95), (math.pi / 2, 0, 0))
look((0.2, 0, 0.75), 12, 22, ortho=3.0); shot("컵")

# 와인잔
sc = new_scene()
lathe("glass", [(0.0, 0.0), (0.55, 0.0), (0.55, 0.05), (0.08, 0.12), (0.06, 1.0), (0.2, 1.15), (0.55, 1.5), (0.6, 2.0), (0.55, 2.5), (0.5, 2.5), (0.55, 2.0), (0.5, 1.55), (0.0, 1.4)])
look((0, 0, 1.25), 0, 18, ortho=3.0); shot("와인잔")

# 물뿌리개
sc = new_scene()
lathe("can", [(0.0, 0.0), (0.8, 0.0), (0.8, 1.3), (0.76, 1.3), (0.76, 0.05), (0.0, 0.05)])
prim("cylinder", vertices=48, radius=0.09, depth=1.6, rotation=(0, math.radians(55), 0), location=(1.25, 0, 0.75))
prim("cone", vertices=48, radius1=0.09, radius2=0.25, depth=0.25, rotation=(0, math.radians(55), 0), location=(1.9, 0, 1.22))
prim("cylinder", vertices=48, radius=0.25, depth=0.04, rotation=(0, math.radians(55), 0), location=(2.0, 0, 1.29))
torus_part(0.75, 0.06, (-0.05, 0, 1.3), (math.pi / 2, 0, 0))
look((0.5, 0, 0.9), 0, 12, ortho=3.6); shot("물뿌리개")

# 가위: 날 두 개 + 고리 두 개 (위에서 본 X)
sc = new_scene()
for s in (1, -1):
    bl = prim("cube", size=1, location=(0, 0, 0)); bl.scale = (2.4, 0.16, 0.04)
    bl.data.vertices.foreach_set("co", [c for v in bl.data.vertices for c in (v.co.x, v.co.y * (0.15 if v.co.x > 0 else 1.0), v.co.z)])
    bl.location = (0.9 * math.cos(math.radians(s * 20)), 0.9 * math.sin(math.radians(s * 20)), 0.05 * s); bl.rotation_euler = (0, 0, math.radians(s * 20))
    sh = prim("cube", size=1, location=(-0.75 * math.cos(math.radians(s * -20)), -0.75 * math.sin(math.radians(s * -20)), 0.05 * s)); sh.scale = (1.2, 0.12, 0.04); sh.rotation_euler = (0, 0, math.radians(-s * 20))
    torus_part(0.32, 0.07, (-1.55 * math.cos(math.radians(-s * 20)), -1.55 * math.sin(math.radians(-s * 20)), 0.05 * s), (0, 0, 0))
look((0.3, 0, 0), 0, 90, ortho=4.4); shot("가위")

# 의자(등받이 없는 스툴)
sc = new_scene()
prim("cylinder", vertices=64, radius=0.75, depth=0.14, location=(0, 0, 1.6))
for i in range(4):
    a = math.radians(45 + 90 * i); x, y = 0.55 * math.cos(a), 0.55 * math.sin(a)
    lg = prim("cylinder", vertices=16, radius=0.05, depth=1.62, location=(x * 1.15, y * 1.15, 0.8)); lg.rotation_euler = (math.radians(-6) * math.sin(a), math.radians(6) * math.cos(a), 0)
for i in range(4):
    a1, a2 = math.radians(45 + 90 * i), math.radians(135 + 90 * i)
    mx, my = 0.6 * (math.cos(a1) + math.cos(a2)) / 2, 0.6 * (math.sin(a1) + math.sin(a2)) / 2
    rg = prim("cylinder", vertices=12, radius=0.035, depth=0.86, location=(mx, my, 0.55)); rg.rotation_euler = (math.pi / 2, 0, (a1 + a2) / 2)
look((0, 0, 0.85), 20, 15, ortho=2.6); shot("의자")
