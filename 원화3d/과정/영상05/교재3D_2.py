# -*- coding: utf-8 -*-
"""교재 3D 2 차: ④ 얼굴-술잔(Hoffman Fig 12) — 얼굴 옆선을 돌려 깎은 꽃병 · ⑤ 손전등 지움 vs 가림(Biederman Fig 25–26) 선 렌더 · ⑥ 수잔 윤곽 vs +suggestive(DeCarlo Fig 1).
blender -b -P 교재3D_2.py"""
import bpy, sys, os, math, json, mathutils
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\3D"
def wb(res):
    sc = H.scene(res=res); sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True; return sc
def lathe(name, prof, steps=96, color=(0.9, 0.9, 0.92, 1)):
    """prof = [(r, z)] 위→아래. z 축으로 돌려 깎기."""
    vs, fs = [], []; n = len(prof)
    for j in range(steps):
        a = 2 * math.pi * j / steps
        for r, z in prof: vs.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(steps):
        for i in range(n - 1):
            p = j * n + i; q = ((j + 1) % steps) * n + i; fs.append((p, q, q + 1, p + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.color = color
    for pg in me.polygons: pg.use_smooth = True
    return o
# ---------- ④ 얼굴 옆선 = 꽃병 반지름 ----------
# 위(이마)→아래(목). r 이 크면 꽃병이 바깥으로 = 얼굴이 안쪽으로 들어감(코가 r 최소)
face = [(1.55, 4.0), (1.45, 3.6), (1.20, 3.2), (1.05, 2.8), (1.00, 2.5), (1.12, 2.25), (0.62, 1.85), (0.55, 1.65), (0.92, 1.45),
        (0.70, 1.25), (0.78, 1.05), (0.66, 0.85), (0.70, 0.55), (1.02, 0.25), (0.95, -0.1), (0.62, -0.4), (0.58, -1.0), (0.80, -1.4), (1.40, -1.6)]
# 매끈하게 — 점 사이 캣멀롬
def cr(pts, k=8):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [mathutils.Vector(v) for v in P[i - 1:i + 3]]
        for t in [s / k for s in range(k)]:
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    return out + [pts[-1]]
prof = [(-0.0, 4.0)] + cr(face) + [(0.0, -1.6)]
sc = wb((900, 1000)); v = lathe("vase", prof)
sh = sc.display.shading; sh.light = "FLAT"; sh.show_cavity = False; sc.render.film_transparent = False; sc.world.color = (0, 0, 0); v.color = (1, 1, 1, 1)
H.look((0, 0, 1.2), 0, 0, ortho=6.4); H.shot(os.path.join(OUT, "g4_술잔_정면.png"))
sh.light = "STUDIO"; sh.show_cavity = True; sc.world.color = H.BG; v.color = (0.85, 0.85, 0.88, 1)
H.look((0, 0, 1.2), 30, 25, ortho=6.4); H.shot(os.path.join(OUT, "g4_술잔_3D.png"))
# ---------- ⑤ 손전등: Freestyle 선 렌더 + 오목부 화면 좌표 ----------
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 1200, 800
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0, 0, 0); sc.render.film_transparent = False
sc.render.use_freestyle = True; sc.render.line_thickness = 2.2
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"
mat = bpy.data.materials.new("blk"); mat.diffuse_color = (0, 0, 0, 1)
def add(o):
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o
# 몸통(x 축) + 넓어지는 머리 + 렌즈 테 + 버튼 + 끝마개
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.55, depth=4.0, rotation=(0, math.pi / 2, 0), location=(0, 0, 0)); add(bpy.context.object)
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.55, radius2=1.0, depth=1.3, rotation=(0, math.pi / 2, 0), location=(2.65, 0, 0)); add(bpy.context.object)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.0, depth=0.35, rotation=(0, math.pi / 2, 0), location=(3.47, 0, 0)); add(bpy.context.object)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.6, 0, 0.6)); b = bpy.context.object; b.scale = (0.6, 0.3, 0.18); add(b)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.62, depth=0.4, rotation=(0, math.pi / 2, 0), location=(-2.15, 0, 0)); add(bpy.context.object)
H.look((0.6, 0, 0), 25, 20, ortho=8.5, dist=30)
ls = sc.view_layers[0].freestyle_settings.linesets[0]; ls.select_by_visibility = True
for k in ("silhouette", "border", "crease", "external_contour", "contour"): setattr(ls, "select_" + k, True)
ls.linestyle = ls.linestyle or bpy.data.linestyles.new("ln"); ls.linestyle.color = (1, 1, 1)
sc.render.filepath = os.path.join(OUT, "g5_손전등_선.png"); bpy.ops.render.render(write_still=True)
# 오목부(덩어리 이음매) 3D 점 → 화면 좌표
J = {"몸통-머리 위": (2.0, 0, 0.55), "몸통-머리 아래": (2.0, 0, -0.55), "머리-테": (3.3, 0, 1.0), "버튼": (0.6, 0, 0.42), "끝마개": (-1.95, 0, 0.6), "끝마개 아래": (-1.95, 0, -0.6)}
px = {}
for k, p in J.items():
    c = world_to_camera_view(sc, cam, mathutils.Vector(p)); px[k] = (c.x * 1200, (1 - c.y) * 800)
json.dump(px, open(os.path.join(OUT, "g5_오목부.json"), "w", encoding="utf-8"), ensure_ascii=False)
# ---------- ⑥ 수잔: 윤곽만 vs + suggestive ----------
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 900, 900
sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1); sc.render.use_freestyle = True; sc.render.line_thickness = 2.0
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"
bpy.ops.mesh.primitive_monkey_add(); m = bpy.context.object; md = m.modifiers.new("s", "SUBSURF"); md.levels = md.render_levels = 3; bpy.ops.object.shade_smooth()
wm = bpy.data.materials.new("w"); wm.diffuse_color = (1, 1, 1, 1); m.data.materials.append(wm)
# 흰 면이 흰 배경 위에 보이도록 Emission 흰색
wm.use_nodes = True; nt = wm.node_tree; nt.nodes.clear(); e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (1, 1, 1, 1); o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
H.look((0, 0, 0), 35, 10, ortho=2.6, dist=20)
fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(120)
ls = fs.linesets[0]; ls.select_by_visibility = True; ls.linestyle = ls.linestyle or bpy.data.linestyles.new("ln2"); ls.linestyle.color = (0, 0, 0)
for k in ("silhouette", "border", "crease", "external_contour", "contour", "suggestive_contour", "ridge_valley"): setattr(ls, "select_" + k, k in ("silhouette", "border", "external_contour", "contour"))
sc.render.filepath = os.path.join(OUT, "g6_수잔_윤곽만.png"); bpy.ops.render.render(write_still=True)
fs.use_smoothness = True; ls.select_suggestive_contour = True; fs.kr_derivative_epsilon = 0.0
sc.render.filepath = os.path.join(OUT, "g6_수잔_암시.png"); bpy.ops.render.render(write_still=True)
