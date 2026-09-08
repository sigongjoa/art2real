# -*- coding: utf-8 -*-
"""파트를 **하나씩 따로** 찍는다. 자리 추정으로 이름 붙이면 틀린다 — 보고 정한다.

    blender -b --python shot_parts.py -- out/omega.blend out/pt

전체 카메라를 고정해두고 파트만 바꿔 켠다. 그래야 어디에 있던 조각인지 같이 보인다.
"""
import bpy, os, sys, math
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
SRC, TAG = os.path.abspath(A[0]), A[1]
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.open_mainfile(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
co = np.vstack([np.array([v.co[:] for v in o.data.vertices]) for o in obs])
lo, hi = co.min(0), co.max(0)
ctr, size = (lo+hi)/2, float((hi-lo).max())

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.62, 0.62, 0.66)
sc.display.shading.show_cavity = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.view_settings.view_transform = 'Standard'

cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = size*1.2
c = bpy.data.objects.new("c", cd)
c.location = (ctr[0], ctr[1] - 3*size, ctr[2])
c.rotation_euler = (math.radians(90), 0, 0)
sc.collection.objects.link(c); sc.camera = c

for o in obs:
    for x in obs:
        x.hide_render = x is not o
    sc.render.filepath = os.path.join(HERE, "%s_%s.png" % (TAG, o.name))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s" % o.name)
