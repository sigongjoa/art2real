# -*- coding: utf-8 -*-
"""영상05 1 편(콜드 오픈 + 이유 1) 움직이는 장면 프레임 (10-02).
    blender -b -P ep1_렌더.py -- [캐릭터 파일(.blend/.glb/.fbx)]
캐릭터를 안 주면 out/영상05/B1/head60k.blend(TripoSG 오메가몬 머리 · 자리표시). 사용자가 캐릭터를 넣으면 그 파일로 바꿔 돈다.
→ out/영상05/ep1/프레임/<장면>/0000.png"""
import bpy, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\ep1\프레임"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CHAR = argv[0] if argv else r"G:\art2real\out\영상05\B1\head60k.blend"

def wb(res):
    sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.film_transparent = True; sc.render.image_settings.color_mode = "RGBA"
    sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.85, 0.85, 0.88); sh.show_cavity = True
    if sc.camera is None:
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); cam.data.type = "ORTHO"; cam.data.clip_end = 5000; sc.camera = cam
    return sc

def load_char():
    """캐릭터 한 덩어리를 원점 · 최대 변 100 으로 맞춘다. 정면 = -Y."""
    if CHAR.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=CHAR)
    else:
        H.scene(res=(600, 600))
        (bpy.ops.import_scene.gltf if CHAR.lower().endswith((".glb", ".gltf")) else bpy.ops.import_scene.fbx)(filepath=CHAR)
    ms = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in bpy.context.scene.objects: o.select_set(o in ms)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    lo = mathutils.Vector([min(v[i] for v in bb) for i in range(3)]); hi = mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
    s = 100 / max(hi - lo); o.location = -(lo + hi) / 2 * s; o.scale = (s, s, s); bpy.ops.object.transform_apply(location=True, scale=True)
    for p in o.data.polygons: p.use_smooth = True
    return o

def seq(name, yaw0, yaw1, n, ortho, pitch=0):
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    for i in range(n):
        t = i / (n - 1); t = t * t * (3 - 2 * t)          # 천천히 출발 · 천천히 멈춤
        H.look((0, 0, 0), yaw0 + (yaw1 - yaw0) * t, pitch, ortho=ortho); H.shot(os.path.join(d, "%04d.png" % i))

o = load_char(); wb(720)
seq("ai_turn", 0, 360, 96, 120, pitch=8)                    # 콜드 오픈: AI 결과 한 바퀴
for lam in (0.5, 1.0, 1.5):                                 # 이유 1: 깊이만 다른 셋 — 정면 → 옆
    o.scale = (1, lam, 1); sh = bpy.context.scene.display.shading
    sh.light = "FLAT"; sh.show_cavity = False; H.look((0, 0, 0), 0, 0, ortho=120); os.makedirs(os.path.join(OUT, "b1_sil"), exist_ok=True); H.shot(os.path.join(OUT, "b1_sil", "%.1f.png" % lam))
    sh.light = "STUDIO"; sh.show_cavity = True; os.makedirs(os.path.join(OUT, "b1_shade"), exist_ok=True); H.shot(os.path.join(OUT, "b1_shade", "%.1f.png" % lam))
    seq("b1_turn_%.1f" % lam, 0, 90, 60, 175)
o.scale = (1, 1, 1)

# 선화 철사 셋: 같은 정육면체 선화 → 돌리면 셋 다 다름 (교재3D_1 과 같은 구성)
import random
H.scene(res=(720, 720)); wb(720); random.seed(3)
V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
E = [(a, b) for a in range(8) for b in range(a + 1, 8) if sum(V[a][i] != V[b][i] for i in range(3)) == 1]
yaw, pit = math.radians(30), math.radians(25); D = mathutils.Vector((math.sin(yaw) * math.cos(pit), -math.cos(yaw) * math.cos(pit), math.sin(pit)))
shapes = [V] + [[tuple(mathutils.Vector(p) + D * random.uniform(-1.6, 1.6)) for p in V] for _ in range(2)]
cols = [(0.9, 0.9, 0.92), (0.95, 0.55, 0.3), (0.35, 0.65, 0.95)]
for k, (pts, c) in enumerate(zip(shapes, cols)):
    for x in list(bpy.context.scene.objects):
        if x.type != "CAMERA": bpy.data.objects.remove(x)
    me = bpy.data.meshes.new("w"); me.from_pydata(pts, E, []); me.update(); w = bpy.data.objects.new("w", me); bpy.context.scene.collection.objects.link(w)
    bpy.context.view_layer.objects.active = w; w.select_set(True); bpy.ops.object.convert(target="CURVE"); w.data.bevel_depth = 0.06
    for p in pts: bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=p)
    sh = bpy.context.scene.display.shading; sh.color_type = "SINGLE"; sh.single_color = c
    H.look((0, 0, 0), 30, 25, ortho=6); os.makedirs(os.path.join(OUT, "wire_still"), exist_ok=True); H.shot(os.path.join(OUT, "wire_still", "%d.png" % k))
    d = os.path.join(OUT, "wire_turn_%d" % k); os.makedirs(d, exist_ok=True)
    for i in range(60):
        t = i / 59; t = t * t * (3 - 2 * t); H.look((0, 0, 0), 30 + 75 * t, 25 - 20 * t, ortho=6 + 2 * t); H.shot(os.path.join(d, "%04d.png" % i))
print("EP1 프레임 끝", CHAR)
