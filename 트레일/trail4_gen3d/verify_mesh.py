# -*- coding: utf-8 -*-
"""생성 메시를 4각도로 찍고 원화 실루엣과 IoU 를 잰다. Blender 헤드리스.

    blender -b --python verify_mesh.py -- out/turn_front.glb out/turn_front_verify.png

판정 기준을 먼저 고정해 두는 게 목적이다. 안 그러면 눈으로 보고 "괜찮네" 하다가
발에서 했던 짓(임계값 계속 손보기)을 24파츠에서 반복한다.
"""
import os
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])  # blender 는 상대경로를 .blend 기준으로 푼다
RES = 512

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not obs:
    raise SystemExit("메시 없음")

# 전체를 하나로 묶어 원점 정렬 + 높이 1.0 정규화 — 원화 프레임과 같은 규약
bpy.ops.object.select_all(action='DESELECT')
for o in obs:
    o.select_set(True)
bpy.context.view_layer.objects.active = obs[0]
if len(obs) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active

lo = mathutils.Vector((min((ob.matrix_world @ v.co)[i] for v in ob.data.vertices)
                       for i in range(3)))
hi = mathutils.Vector((max((ob.matrix_world @ v.co)[i] for v in ob.data.vertices)
                       for i in range(3)))
size = hi - lo
s = 1.0 / max(size.z, 1e-6)
ob.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
lo, hi = lo * s, hi * s
ob.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
bpy.ops.object.transform_apply(location=True)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
# 실루엣만으로는 형태를 판정할 수 없다(LESSONS 20). 매트캡으로 면을 보고,
# 실루엣은 알파에서 따로 뽑는다.
sc.display.shading.light = 'MATCAP'
sc.display.shading.studio_light = 'basic_1.exr'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.8, 0.8, 0.82)
sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = 'BOTH'
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = RES
sc.view_settings.view_transform = 'Standard'

cam_d = bpy.data.cameras.new("c")
cam_d.type = 'ORTHO'
cam_d.ortho_scale = 1.25
cam = bpy.data.objects.new("c", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

import math
tiles = []
for name, az in (("front", 0), ("side", 90), ("back", 180), ("3/4", 45)):
    a = math.radians(az)
    cam.location = (math.sin(a) * 6, -math.cos(a) * 6, 0.5)
    cam.rotation_euler = (math.radians(90), 0, a)
    sc.render.filepath = OUT.replace(".png", f"_{az}.png")
    bpy.ops.render.render(write_still=True)
    tiles.append((name, sc.render.filepath))
print("RENDERED " + "|".join(f"{n}:{p}" for n, p in tiles))
