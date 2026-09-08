# -*- coding: utf-8 -*-
"""구운 텍스처를 메시에 도로 입혀 찍는다 — 원화 / 3D / UV 를 나란히 보려고.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python check3.py

Workbench 의 TEXTURE + FLAT 이라 조명이 안 얹힌다. 평면 알베도를 그대로 본다
(셀 셰이더가 렌더 때 음영을 다시 얹을 것이므로 여기선 재질만 봐야 한다).
"""
import bpy, os, math, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

ARG = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
BLEND, TEX, PRE = (ARG + ["panel_q800.blend", "panel_col.png", "shot"])[:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, BLEND))
objs = [x for x in bpy.context.scene.objects if x.type == 'MESH']
if len(objs) > 1:
    bpy.context.view_layer.objects.active = objs[0]
    for x in objs: x.select_set(True)
    bpy.ops.object.join()
o = bpy.context.view_layer.objects.active or objs[0]

m = bpy.data.materials.new("tex"); m.use_nodes = True
nt = m.node_tree
bsdf = nt.nodes["Principled BSDF"]
img = nt.nodes.new("ShaderNodeTexImage")
img.image = bpy.data.images.load(os.path.join(OUT, TEX))
img.interpolation = 'Closest'
nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
o.data.materials.clear(); o.data.materials.append(m)

co = np.array([v.co[:] for v in o.data.vertices])
cx, cy, cz = co.mean(0)
span = max(co.max(0) - co.min(0)) * 1.25

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'TEXTURE'
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.view_settings.view_transform = 'Standard'

for n, ang in (("front", 0.0), ("q", 40.0), ("back", 180.0)):
    a = math.radians(ang)
    cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = span
    c = bpy.data.objects.new(n, cd)
    c.location = (cx + 2*math.sin(a), cy - 2*math.cos(a), cz)
    c.rotation_euler = (math.radians(90), 0, a)
    sc.collection.objects.link(c); sc.camera = c
    sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (PRE, n))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s" % n)
