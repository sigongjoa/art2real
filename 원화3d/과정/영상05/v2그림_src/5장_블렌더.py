# -*- coding: utf-8 -*-
"""5 장 입체 그림 바탕(Workbench 면 + Freestyle 윤곽선) — 5-2 · 5-3 · 5-4 · 5-5 · 5-7 · 5-11 · 5-13.
blender -b -P 5장_블렌더.py  → src/_raw/5_<이름>.png (투명 바탕). 합치기는 5장_합치기.py"""
import bpy, bmesh, math, os, mathutils, random
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_raw")
WHITE, LG, MG, DG, BLK = (1, 1, 1, 1), (0.86, 0.86, 0.87, 1), (0.66, 0.66, 0.68, 1), (0.42, 0.42, 0.44, 1), (0.0, 0.0, 0.0, 1)

def new_scene(res=(1000, 1000), light="FLAT", thick=2.6):
    bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading; sh.light = light; sh.color_type = "OBJECT"; sh.show_cavity = False
    if light == "STUDIO": sh.studio_light = "basic.sl" if "basic.sl" in [s.name for s in bpy.context.preferences.studio_lights] else sh.studio_light
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"
    sc.world = bpy.data.worlds.new("w"); sc.render.use_freestyle = True; sc.render.line_thickness = thick
    fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(120)
    ls = fs.linesets[0]; ls.select_by_visibility = True
    for k in ("silhouette", "border", "crease", "external_contour", "contour"): setattr(ls, "select_" + k, True)
    ls.linestyle = ls.linestyle or bpy.data.linestyles.new("ln"); ls.linestyle.color = (0, 0, 0); ls.linestyle.caps = "ROUND"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.clip_end = 500
    return sc

def look(center, yaw, pitch, ortho, dist=60, persp=None):
    cam = bpy.context.scene.camera; y, p = math.radians(yaw), math.radians(pitch)
    d = mathutils.Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = mathutils.Vector(center) + d * dist; cam.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); cam.data.ortho_scale = ortho
    if persp: cam.data.type = "PERSP"; cam.data.lens = persp

def fin(o, color, smooth=True):
    o.color = color
    if smooth and o.type == "MESH":
        for pg in o.data.polygons: pg.use_smooth = True
    return o

def prim(kind, color=WHITE, smooth=True, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**kw); return fin(bpy.context.object, color, smooth)

def boxo(loc, size, color=WHITE, rot=(0, 0, 0)):
    o = prim("cube", color, False, size=1, location=loc, rotation=rot); o.scale = size; return o

def mesh(name, vs, fs, color):
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return fin(o, color)

def sweep(name, path, radius, color, seg=32, flat=1.0, radial=False):
    """경로 path(점 목록)를 따라 반지름 radius(t) 원을 쓸어 만든 관. flat<1 이면 단면이 납작(띠). 끝은 반지름 0 으로 닫는다."""
    vs, fs = [], []; n = len(path)
    for i, p in enumerate(path):
        p = mathutils.Vector(p); t = i / (n - 1)
        tg = (mathutils.Vector(path[min(i + 1, n - 1)]) - mathutils.Vector(path[max(i - 1, 0)])).normalized()
        up = mathutils.Vector((0, 0, 1)) if abs(tg.z) < 0.7 else mathutils.Vector((0, 1, 0)); nx = tg.cross(up).normalized(); ny = nx.cross(tg).normalized()
        r = radius(t)
        for j in range(seg):
            a = 2 * math.pi * j / seg; fx, fy = (flat, 1.0) if radial else (1.0, flat); vs.append(tuple(p + nx * (r * fx * math.cos(a)) + ny * (r * fy * math.sin(a))))
    for i in range(n - 1):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg; fs.append((a, b, b + seg, a + seg))
    return mesh(name, vs, fs, color)

def lathe(name, prof, color, steps=96, axis_rot=None, loc=(0, 0, 0)):
    vs, fs = [], []; n = len(prof)
    for j in range(steps):
        a = 2 * math.pi * j / steps
        for r, z in prof: vs.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(steps):
        for i in range(n - 1):
            p = j * n + i; q = ((j + 1) % steps) * n + i; fs.append((p, q, q + 1, p + 1))
    o = mesh(name, vs, fs, color); o.location = loc
    if axis_rot: o.rotation_euler = axis_rot
    return o

def arc_path(R, a0, a1, z0, z1=None, n=60, wob=0.0, cx=0.0, cy=0.0):
    z1 = z0 if z1 is None else z1; out = []
    for i in range(n):
        t = i / (n - 1); a = math.radians(a0 + (a1 - a0) * t)
        out.append((cx + R * math.cos(a), cy + R * math.sin(a), z0 + (z1 - z0) * t + wob * math.sin(3 * math.pi * t)))
    return out

def shot(name):
    bpy.context.scene.render.filepath = os.path.join(RAW, "5_%s.png" % name); bpy.ops.render.render(write_still=True)

# 각 화면: 카메라 -y 쪽(앞)에서 본다. 원기둥 뒤 = +y.
# ---------- 5-2 a: 원기둥을 휘감은 덩어리 ----------
sc = new_scene((900, 1100))
prim("cylinder", WHITE, True, vertices=96, radius=1.0, depth=7.0, location=(0, 0, 0))
pa = arc_path(1.9, -75, 255, 1.4, -1.4, wob=0.35)
sweep("blob", pa, lambda t: 0.1 + 1.0 * math.sin(math.pi * t) ** 0.45 * (1 + 0.3 * math.sin(9 * t)), WHITE, flat=0.8)
look((0, 0, 0), 0, 14, ortho=8.4); shot("2a")
# ---------- 5-2 b: 다리 둘 달린 덩어리(다리 안쪽 선이 몸 뒤에서 나온다) ----------
sc = new_scene((900, 1100))
body = prim("uv_sphere", WHITE, True, segments=64, ring_count=32, radius=1.0, location=(0, 0, 0.4)); body.scale = (1.5, 0.9, 1.6)
neck = prim("cone", WHITE, True, vertices=64, radius1=0.7, radius2=0.25, depth=1.4, location=(0.1, 0.1, 2.3))
for sx in (-1, 1):
    lg = sweep("leg", [(sx * 0.45, -0.2, 0.2), (sx * 0.65, -0.55, -0.9), (sx * 0.85, -0.6, -2.4), (sx * 1.0, -0.6, -3.4)], lambda t: 0.62 * (1 - t) + 0.08, WHITE)
belly = prim("uv_sphere", WHITE, True, segments=64, ring_count=32, radius=1.0, location=(0, -0.75, -0.55)); belly.scale = (1.0, 0.45, 0.75)   # 앞으로 처진 배 — 다리 안쪽 선이 이 뒤에서 끝난다
sc.view_layers[0].freestyle_settings.linesets[0].select_border = False
look((0, 0, -0.3), 0, 6, ortho=7.6); shot("2b")
# ---------- 5-3: 원기둥에 감긴 팔 넷(위 셋 두께 · 맨 아래 납작 띠) ----------
sc = new_scene((800, 1200))
prim("cylinder", WHITE, True, vertices=128, radius=1.25, depth=9.0, location=(0, 0, 0))
top = prim("cylinder", DG, True, vertices=128, radius=1.249, depth=0.02, location=(0, 0, 4.5))
for z, R, r, flat in ((2.9, 1.85, 0.75, 0.8), (1.0, 1.85, 0.7, 0.8), (-0.6, 1.9, 0.8, 0.8), (-2.9, 1.32, 0.8, 0.05)):
    p = arc_path(R, -55, 235, z, z - 0.4, n=110)   # 앞에서 시작해 뒤로 돌아 다시 앞으로
    sweep("arm", p, (lambda r: (lambda t: r * (math.sin(math.pi * t) ** 0.3)))(r), MG, flat=flat, radial=(flat < 0.5))
look((0, 0, 0), 0, 16, ortho=11.5); shot("3")
# ---------- 5-4: 판 양쪽 윤곽은 이어 그을 수 있지만 3D 로는 어긋남 ----------
# a: 앞 판 + 왼쪽 상자(가까움) + 오른쪽 기울어진 판(먼 곳, 다른 방향)
sc = new_scene((1100, 800))
boxo((0, -1.0, 0.0), (2.4, 0.25, 3.0), LG)
boxo((-2.0, 0.6, -0.2), (1.6, 1.6, 2.6), MG)
boxo((2.2, 2.4, 0.1), (3.2, 2.6, 0.5), WHITE, rot=(0, 0, math.radians(-20)))
boxo((1.2, 1.1, -1.0), (0.5, 0.6, 0.6), WHITE)
look((0.2, 0, 0), -20, 18, ortho=7.6); shot("4a")
# b: 기둥 + 뒤의 두꺼운 ㄷ자 + 오른쪽 얇은 기운 판
sc = new_scene((1100, 900))
boxo((0, -1.0, 0.0), (1.4, 0.3, 4.8), LG)
for loc, size in (((-1.6, 0.6, 1.0), (1.4, 0.9, 0.6)), ((-1.6, 0.6, -1.0), (1.4, 0.9, 0.6)), ((-2.0, 0.6, 0.0), (0.6, 0.9, 2.6))):
    boxo(loc, size, DG)
boxo((1.9, 1.5, -0.2), (2.4, 2.0, 0.12), BLK, rot=(math.radians(12), 0, math.radians(15)))
look((0, 0, 0), -10, 16, ortho=7.0); shot("4b")
# c: 기둥 + 뒤의 긴 상자 둘(같은 높이로 보이나 깊이 · 방향이 다름)
sc = new_scene((1300, 900))
boxo((0, -1.5, 0.3), (1.0, 0.3, 4.6), MG)
boxo((-2.6, 0.0, -1.1), (4.0, 1.6, 0.9), LG, rot=(0, 0, math.radians(-12)))
boxo((2.6, 3.5, 0.6), (4.0, 1.6, 0.9), LG, rot=(0, 0, math.radians(-12)))
look((0, 0, 0), -12, 14, ortho=9.6); shot("4c")
# ---------- 5-5: 판 양쪽 상자 둘 — 면은 같은 평면인데 두 상자로 보인다 ----------
# a: 같은 높이 · 같은 앞면 평면. 왼쪽 상자는 판 바로 왼쪽에서 끝(옆면이 보임)
sc = new_scene((1300, 800))
boxo((0.0, -1.2, 0.0), (0.7, 0.2, 3.4), LG)
boxo((-2.2, 0.0, -0.5), (2.6, 2.0, 1.6), MG)
boxo((2.4, 0.0, -0.5), (3.6, 2.0, 1.6), MG)
look((0, 0, 0), 22, 18, ortho=9.0); shot("5a")
# b: 보이는 앞면 둘이 같은 깊이 — 왼쪽은 낮고 넓게, 오른쪽은 높고 좁게
sc = new_scene((1300, 900))
boxo((0.0, -1.6, 0.0), (0.9, 0.3, 4.0), DG)
boxo((-2.3, 0.0, -0.9), (2.6, 2.0, 1.4), WHITE)
boxo((2.3, 0.9, 0.2), (2.8, 3.8, 1.4), LG)
look((0, 0, 0), 22, 18, ortho=9.0); shot("5b")
# ---------- 5-7: 판을 뚫고 지나는 원기둥 두 토막(방향이 어긋남) ----------
sc = new_scene((1200, 950))
boxo((0, 0, 0), (6.0, 3.6, 1.4), LG)
c1 = prim("cylinder", MG, True, vertices=96, radius=0.75, depth=3.0, location=(0.6, 0.3, 1.6)); c1.rotation_euler = (math.radians(-12), math.radians(-14), 0)
c2 = prim("cylinder", MG, True, vertices=96, radius=1.15, depth=3.4, location=(-0.4, -0.2, -1.8)); c2.rotation_euler = (math.radians(14), math.radians(17), 0)
look((0, 0, -0.3), -12, 22, ortho=10.5); shot("7")
def striped_face(p0, u, v, nu, nv, color):
    """p0 에서 u · v 로 펼친 면. 나눈 모서리에 Freestyle 표시 → 줄무늬(nu=1 이면 가로줄만)."""
    bm = bmesh.new(); P = [[bm.verts.new(mathutils.Vector(p0) + mathutils.Vector(u) * (i / nu) + mathutils.Vector(v) * (j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv): bm.faces.new((P[i][j], P[i + 1][j], P[i + 1][j + 1], P[i][j + 1]))
    me = bpy.data.meshes.new("f"); bm.to_mesh(me)
    for e in me.edges: e.use_freestyle_mark = True
    o = bpy.data.objects.new("f", me); bpy.context.scene.collection.objects.link(o); o.color = color; return o
# ---------- 5-11: 검은 판 위로 솟은 두 면 (a) 상자 / (b) 접힌 판만 ----------
for tag, wall in (("11a", True), ("11b", False)):
    sc = new_scene((1100, 800))
    sc.view_layers[0].freestyle_settings.linesets[0].select_edge_mark = True
    striped_face((-1.7, -1.2, -1.0), (2.4, 0, 0), (0, 0, 3.0), 1, 14, WHITE)        # 앞면: 가로줄
    striped_face((0.7, -1.2, -1.0), (0, 2.4, 0), (0, 0, 3.0), 8, 14, LG)           # 옆면: 격자
    if wall:
        boxo((-0.5, 0.0, 0.5), (2.38, 2.38, 2.98), WHITE)                              # 속이 찬 상자(뒤쪽)
        boxo((-0.6, -2.6, -0.6), (6.5, 0.2, 2.4), BLK, rot=(0, 0, math.radians(32)))   # 카메라를 마주 보는 검은 판
    look((0, 0, 1.6), 32, 0, ortho=8.0, dist=13, persp=40); shot(tag)
