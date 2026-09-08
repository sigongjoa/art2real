# -*- coding: utf-8 -*-
"""작업 중인 .blend 를 찍는다. 모디파이어가 걸린 상태 그대로 본다.

    blender -b --python shot_blend.py -- out/omega.blend out/wb [parts]
"""
import bpy, os, sys, math
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
SRC, TAG = os.path.abspath(A[0]), A[1]
PARTS = "parts" in A[2:]
HEAD = "head" in A[2:]
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.open_mainfile(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
co = np.vstack([np.array(o.matrix_world @ v.co)[:] for o in obs for v in o.data.vertices])
lo, hi = co.min(0), co.max(0)
if HEAD:
    lo = lo.copy(); lo[2] = hi[2] - (hi[2]-lo[2])*0.20
    c0 = (lo[0]+hi[0])/2; w = (hi[0]-lo[0])*0.18
    lo[0], hi[0] = c0-w, c0+w
ctr, size = (lo+hi)/2, float((hi-lo).max())

rs = np.random.RandomState(5)
for i, o in enumerate(obs):
    m = o.data.materials[0] if o.data.materials else None
    if m:
        m.diffuse_color = (tuple(rs.uniform(0.2, 0.9, 3)) + (1,)) if PARTS else (0.62, 0.62, 0.66, 1)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.view_settings.view_transform = 'Standard'

for n, ang in (("a000", 0.0), ("a090", 90.0)):
    r = math.radians(ang)
    cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = size*1.2
    c = bpy.data.objects.new(n, cd)
    c.location = (ctr[0] + 3*size*math.sin(r), ctr[1] - 3*size*math.cos(r), ctr[2])
    c.rotation_euler = (math.radians(90), 0, r)
    sc.collection.objects.link(c); sc.camera = c
    sc.render.filepath = os.path.join(HERE, "%s_%s.png" % (TAG, n))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s_%s" % (TAG, n))
