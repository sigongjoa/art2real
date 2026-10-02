# -*- coding: utf-8 -*-
"""교재 3D 3 차: ⑦ 이어지는 막대(Kellman Fig 23) · ⑧ 단순 vs 대칭 채움(Sekuler · Thielen Fig 2) · ⑨ 점토 개 → 상자 → 자세(Princeton p35) · ⑩ 단면으로 몸통(Vanderpoel Plate XXII).
blender -b -P 교재3D_3.py"""
import bpy, bmesh, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\3D"; GR = (0.85, 0.85, 0.88, 1); BL = (0.25, 0.45, 0.85, 1)
def wb(res):
    sc = H.scene(res=res); sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True; return sc
def tube(name, pts, r=0.18, color=GR):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); o.color = color; return o
def plate(loc, sx, sz, color=BL):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); p = bpy.context.object; p.scale = (sx, 0.15, sz); p.color = color; return p
# ---------- ⑦ Kellman: 판 뒤 막대 — 이어짐(매끈한 굽음) vs 안 이어짐(어긋남) ----------
sc = wb((1600, 800))
def rod_pts(x0, z0, ang, L=3):
    a = math.radians(ang); return [(x0 + s * math.cos(a), 0, z0 + s * math.sin(a)) for s in (0, L)]
# 이어짐: 가운데에서 30° 로 휘는 한 막대(판 뒤에서 이어짐)
pts = []
for i in range(61):
    t = i / 60 * 6 - 3
    if t < -0.6: pts.append((t - 3.5, 0, -0.6))
    elif t > 0.6: pts.append((-3.5 + 0.6 + (t - 0.6) * math.cos(0.5) + 0.0, 0, -0.6 + (t - 0.6) * math.sin(0.5) + 0.3))
    else: pts.append((t - 3.5, 0, -0.6 + 0.25 * ((t + 0.6) / 1.2) ** 2))
A = tube("이어짐", pts)
# 안 이어짐: 두 토막이 높이가 어긋나고 서로 엇갈려 지나침
B1 = tube("왼토막", [(1.0, 0, -0.9), (4.0, 0, -0.9)]); B2 = tube("오른토막", [(3.4, 0, 0.5), (6.6, 0, 0.5)])
P1 = plate((-3.5, -1.0, -0.3), 1.4, 2.4); P2 = plate((3.7, -1.0, -0.2), 1.4, 2.4)
H.look((0.0, 0, 0), 0, 0, ortho=14); H.shot(os.path.join(OUT, "g7_막대_가림.png"))
P1.hide_render = P2.hide_render = True; H.look((0.0, 0, 0), 0, 0, ortho=14); H.shot(os.path.join(OUT, "g7_막대_걷음.png"))
# ---------- ⑧ Sekuler: 원 / 꽃잎판을 네모가 가린다 → 단순 채움 vs 대칭 채움 ----------
def disc2d(name, f, loc, color=GR, n=256):
    vs = [(f(2 * math.pi * k / n) * math.cos(2 * math.pi * k / n), f(2 * math.pi * k / n) * math.sin(2 * math.pi * k / n)) for k in range(n)]
    bm = bmesh.new(); vv = [bm.verts.new((x, 0, z)) for x, z in vs]; fc = bm.faces.new(vv)
    r = bmesh.ops.extrude_face_region(bm, geom=[fc]); bmesh.ops.translate(bm, verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0.3, 0))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = loc; o.color = color; return o
sc = wb((2000, 900))
flower = lambda a: 1.0 + 0.28 * max(0, math.cos(4 * a)) ** 3      # 꽃잎 넷(대칭)
local = lambda a: 1.0 if math.cos(a) > 0.75 else flower(a)   # 가린 쪽(오른쪽 꽃잎)만 둥근 원으로
cases = [("원_가림", lambda a: 1.0, -7.5), ("꽃_가림", flower, -2.5), ("원_단순", lambda a: 1.0, 1.5), ("꽃_단순", local, 4.5), ("꽃_대칭", flower, 7.5)]
for name, f, x in cases: disc2d(name, f, (x, 0, 0))
for x in (-7.5, -2.5): bpy.ops.mesh.primitive_cube_add(size=1, location=(x + 1.05, -0.6, 0)); c = bpy.context.object; c.scale = (1.0, 0.2, 1.0); c.color = BL
H.look((0, 0, 0), 0, 0, ortho=19); H.shot(os.path.join(OUT, "g8_채움.png"))
# ---------- ⑨ 점토 개 → 상자 템플릿 → 자세 ----------
def dog(kind, pose=0.0, x0=0):
    parts = {"몸": ((0, 0, 1.4), (1.6, 0.55, 0.5), 0), "목": ((1.45, 0, 1.95), (0.3, 0.28, 0.55), -35), "머리": ((1.9, 0, 2.45), (0.55, 0.3, 0.3), 0),
             "다리앞1": ((1.1, 0.35, 0.6), (0.17, 0.17, 0.6), 0), "다리앞2": ((1.1, -0.35, 0.6), (0.17, 0.17, 0.6), 0),
             "다리뒤1": ((-1.1, 0.35, 0.6), (0.17, 0.17, 0.6), 0), "다리뒤2": ((-1.1, -0.35, 0.6), (0.17, 0.17, 0.6), 0), "꼬리": ((-1.85, 0, 1.75), (0.35, 0.1, 0.1), 35)}
    cols = {"몸": (0.9, 0.3, 0.3, 1), "목": (0.95, 0.8, 0.2, 1), "머리": (0.95, 0.8, 0.2, 1), "꼬리": (0.6, 0.4, 0.9, 1)}
    obs = []
    for n, (loc, s, ry) in parts.items():
        loc = mathutils.Vector(loc); rot = ry
        if pose and n.startswith("다리앞"): rot += -40 * pose; loc += mathutils.Vector((0.35 * pose, 0, 0.12 * pose))
        if pose and n.startswith("다리뒤"): rot += 30 * pose; loc += mathutils.Vector((-0.3 * pose, 0, 0.1 * pose))
        if pose and n in ("목", "머리"): loc += mathutils.Vector((0, 0, 0.35 * pose))
        loc += mathutils.Vector((x0, 0, 0))
        if kind == "점토":
            bpy.ops.object.metaball_add(type="ELLIPSOID", location=loc); m = bpy.context.object; el = m.data.elements[0]; el.size_x, el.size_y, el.size_z = s[0] * 1.1, s[1] * 1.1, s[2] * 1.1
            m.rotation_euler = (0, math.radians(rot), 0); m.data.resolution = 0.08; m.data.render_resolution = 0.06; m.color = (0.35, 0.55, 0.85, 1)
        else:
            bpy.ops.mesh.primitive_cube_add(size=2, location=loc, rotation=(0, math.radians(rot), 0)); m = bpy.context.object; m.scale = s
            m.color = cols.get(n, (0.4, 0.85, 0.45, 1))
        obs.append(m)
    return obs
sc = wb((2100, 900))
dog("점토", x0=-6); dog("상자", x0=0); dog("상자", pose=1.0, x0=6)
H.look((0, 0, 1.4), 25, 12, ortho=16); H.shot(os.path.join(OUT, "g9_개.png"))
# ---------- ⑩ Vanderpoel: 높이마다 단면 → 이어 붙이면 몸통 ----------
sc = wb((1200, 1200))
def sect(z, w, d, sq=2.6, bump=0.0, n=96):     # 초타원 단면 + 앞 가슴 굴곡
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n; c, s = math.cos(a), math.sin(a)
        x = w * math.copysign(abs(c) ** (2 / sq), c); y = d * math.copysign(abs(s) ** (2 / sq), s)
        if y < 0: y *= 1 + bump * abs(math.sin(2 * a))
        out.append((x, y, z))
    return out
S = [("목", 6.2, 0.55, 0.55, 2.2, 0), ("어깨", 5.5, 2.3, 0.85, 3.2, 0), ("가슴", 4.6, 1.75, 1.0, 2.6, 0.25), ("허리", 2.6, 1.35, 0.85, 2.3, 0), ("골반", 1.0, 1.65, 1.0, 2.6, 0.1), ("엉덩이", 0.0, 1.75, 1.05, 2.4, 0)]
rings = [sect(z, w, d, sq, b) for _, z, w, d, sq, b in S]
vs = [v for r in rings for v in r]; n = 96; fs = [(i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k) for i in range(len(rings) - 1) for k in range(n)]
me = bpy.data.meshes.new("몸통"); me.from_pydata(vs, [], fs); me.update(); tor = bpy.data.objects.new("몸통", me); sc.collection.objects.link(tor); tor.color = (0.85, 0.85, 0.88, 1)
mod = tor.modifiers.new("s", "SUBSURF"); mod.levels = mod.render_levels = 2
for p in me.polygons: p.use_smooth = True
rs = []
for i, r in enumerate(rings):
    o = tube("단면%d" % i, r + [r[0]], r=0.05); c = mathutils.Color(); c.hsv = (0.66 * i / (len(rings) - 1), 0.85, 1); o.color = (c.r, c.g, c.b, 1); rs.append(o)
tor.hide_render = True; H.look((0, 0, 3.1), 30, 30, ortho=9.5); H.shot(os.path.join(OUT, "g10_단면만.png"))
H.look((0, 0, 3), 0, 89, ortho=7); H.shot(os.path.join(OUT, "g10_단면_위.png"))
tor.hide_render = False
for o in rs: o.hide_render = True
H.look((0, 0, 3.1), 30, 15, ortho=9.5); H.shot(os.path.join(OUT, "g10_몸통.png"))
