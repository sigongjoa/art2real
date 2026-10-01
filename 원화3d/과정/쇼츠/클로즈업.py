# -*- coding: utf-8 -*-
"""glb 의 위쪽 일부(머리)를 가까이서 렌더 — 「디테일이 있나」를 보는 컷(10-01 TripoSG 쇼츠).
    blender -b --factory-startup -P 클로즈업.py -- <모델.glb> <출력폴더> [위쪽비율=0.16] [z위로]
-> 정면.png · 3-4.png · 옆.png (워크벤치 점토 · 1000×860). 정면 = −Y 쪽(돌림판.py 와 같다)."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; src, out = a[0], a[1]; 비율 = float(a[2]) if len(a) > 2 else 0.16; os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in bpy.context.scene.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1: bpy.ops.object.join()
m = bpy.context.view_layer.objects.active; bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if "z위로" in a: m.rotation_euler = (math.radians(90), 0, 0); bpy.ops.object.transform_apply(rotation=True)
vs = [m.matrix_world @ v.co for v in m.data.vertices]; zmax = max(v.z for v in vs); zmin = min(v.z for v in vs); 높이 = zmax - zmin
윗 = [v for v in vs if v.z > zmax - 비율 * 높이]
lo = Vector([min(v[i] for v in 윗) for i in range(3)]); hi = Vector([max(v[i] for v in 윗) for i in range(3)]); c = (lo + hi) / 2; r = max((hi - lo).x, (hi - lo).z) * 0.62
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "MATCAP"; sh.color_type = "SINGLE"; sh.single_color = (0.86, 0.83, 0.78); sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1000, 860; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.02, 0.02, 0.025)
for o in bpy.data.objects:
    if o.type == "MESH": o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 85
for 이름, 각 in (("정면", 0.0), ("3-4", 0.6), ("옆", 1.5), ("뒤", math.pi)):
    p = c + Vector((math.sin(각), -math.cos(각), 0.05)) * r * 4.2; cam.location = p; cam.rotation_euler = (c - p).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, 이름 + ".png"); bpy.ops.render.render(write_still=True)
print("머리 상자", [round(x, 3) for x in lo], [round(x, 3) for x in hi])
