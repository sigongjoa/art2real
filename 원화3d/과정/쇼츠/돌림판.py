# -*- coding: utf-8 -*-
"""glb/stl 하나 → 한 바퀴 도는 회색 렌더(PNG 연번) + 뒤에서 본 한 장. 쇼츠 그림 띠(1000×860)용.

    blender -b --python 돌림판.py -- <모델.glb> <출력폴더> [프레임수=90] [z위로]

워크벤치(빠름) · 직교 아님(원근 35mm) · 모델은 높이 2 로 맞추고 바닥 중심을 원점에.
뒤 = 정면(-Y 를 보는 쪽)의 반대 · 정면 판정은 입력 모델 그대로(생성 모델은 보통 +Y 앞이 아니라 -Y 앞).
"""
import bpy, sys, os, math
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]
n = int(a[2]) if len(a) > 2 else 90
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
if src.lower().endswith(".glb"): bpy.ops.import_scene.gltf(filepath=src)
else: bpy.ops.wm.stl_import(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in bpy.context.scene.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1: bpy.ops.object.join()
m = bpy.context.view_layer.objects.active
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(a) > 3 and a[3] == "z위로":  # trimesh 가 쓴 glb 는 Z-up 그대로라 들어오면 눕는다
    m.rotation_euler = (math.radians(90), 0, 0); bpy.ops.object.transform_apply(rotation=True)
vs = [v.co for v in m.data.vertices]
lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
s = 2.0 / (hi.z - lo.z)
for v in m.data.vertices: v.co = Vector(((v.co.x - (lo.x + hi.x) / 2) * s, (v.co.y - (lo.y + hi.y) / 2) * s, (v.co.z - lo.z) * s))
turn = bpy.data.objects.new("turn", None); bpy.context.scene.collection.objects.link(turn); m.parent = turn

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "SINGLE"
sc.display.shading.single_color = (0.82, 0.82, 0.85); sc.display.shading.show_cavity = True
sc.display.shading.show_object_outline = True
sc.render.resolution_x, sc.render.resolution_y = 1000, 860
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (1, 1, 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35
cam.location = (0, -3.2, 1.0); cam.rotation_euler = (math.radians(90), 0, 0)

for i in range(n):
    turn.rotation_euler = (0, 0, 2 * math.pi * i / n)
    sc.render.filepath = os.path.join(out, f"t{i:03d}.png"); bpy.ops.render.render(write_still=True)
turn.rotation_euler = (0, 0, math.pi)
sc.render.filepath = os.path.join(out, "back.png"); bpy.ops.render.render(write_still=True)
turn.rotation_euler = (0, 0, 0)
sc.render.filepath = os.path.join(out, "front.png"); bpy.ops.render.render(write_still=True)
print("TURNTABLE", out, n)
