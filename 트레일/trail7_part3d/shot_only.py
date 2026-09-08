# -*- coding: utf-8 -*-
"""고른 오브젝트만 켜고 그것에 맞춰 찍는다.

    blender -b --python shot_only.py -- out/omega.blend out/tag helmet faceplate fins
"""
import bpy, os, sys, math
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
SRC, TAG, NAMES = os.path.abspath(A[0]), A[1], A[2:]
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.open_mainfile(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
sel = [o for o in obs if o.name in NAMES]
for o in obs:
    o.hide_render = o not in sel

co = np.vstack([np.array(o.matrix_world @ v.co)[:] for o in sel for v in o.data.vertices])
lo, hi = co.min(0), co.max(0)
ctr, size = (lo+hi)/2, float((hi-lo).max())

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.62, 0.62, 0.66)
sc.display.shading.show_cavity = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 640
sc.view_settings.view_transform = 'Standard'

for n, ang in (("a000", 0.0), ("a040", 40.0), ("a090", 90.0)):
    r = math.radians(ang)
    cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = size*1.15
    c = bpy.data.objects.new(n, cd)
    c.location = (ctr[0] + 3*size*math.sin(r), ctr[1] - 3*size*math.cos(r), ctr[2])
    c.rotation_euler = (math.radians(90), 0, r)
    sc.collection.objects.link(c); sc.camera = c
    sc.render.filepath = os.path.join(HERE, "%s_%s.png" % (TAG, n))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s_%s" % (TAG, n))
