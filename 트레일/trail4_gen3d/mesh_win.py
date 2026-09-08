# -*- coding: utf-8 -*-
"""생성 메시를 art_regions.py 와 **같은 좌표창**으로 3면 렌더한다.

    blender -b --python mesh_win.py -- <glb> <out_prefix>

창: u in [-0.6,0.6], z in [-0.1,1.1], 1024^2, 직교.
카메라 규약은 parts/CONTRACT.md 와 같다 (-y = 앞):
    front az0   화면 x = +x      side az90  화면 x = +y      back az180 화면 x = -x
"""
import math
import os
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, PRE = os.path.abspath(argv[0]), os.path.abspath(argv[1])
RES, SPAN, ZC = 1024, 1.2, 0.5

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in obs:
    o.select_set(True)
bpy.context.view_layer.objects.active = obs[0]
if len(obs) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active

co = [ob.matrix_world @ v.co for v in ob.data.vertices]
lo = mathutils.Vector([min(c[i] for c in co) for i in range(3)])
hi = mathutils.Vector([max(c[i] for c in co) for i in range(3)])
s = 1.0 / (hi.z - lo.z)
ob.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
lo, hi = lo * s, hi * s
ob.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
bpy.ops.object.transform_apply(location=True)
bpy.ops.wm.save_as_mainfile(filepath=PRE + "_norm.blend")

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (1, 1, 1)
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = RES
sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new("c")
cd.type = 'ORTHO'
cd.ortho_scale = SPAN
cam = bpy.data.objects.new("c", cd)
sc.collection.objects.link(cam)
sc.camera = cam
for az, tag in ((0, "front"), (90, "side"), (180, "back")):
    a = math.radians(az)
    cam.location = (math.sin(a) * 6, -math.cos(a) * 6, ZC)
    cam.rotation_euler = (math.radians(90), 0, a)
    sc.render.filepath = f"{PRE}_{tag}.png"
    bpy.ops.render.render(write_still=True)
print("WINRENDER OK")
