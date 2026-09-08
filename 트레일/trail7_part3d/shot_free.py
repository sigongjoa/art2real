# -*- coding: utf-8 -*-
"""GLB 를 **제 bbox 에 맞춰** 한 재질로 돌려 찍는다. 판정용 정렬(shot_glb.py)과 별개다.

    blender -b --python shot_free.py -- out/pc_front.glb out/pc_free [parts]

shot_glb 는 견갑 실측 상자에 맞춰 자르기 때문에 물체가 상자 밖에 있으면 안 보인다.
"물건이 제대로 만들어졌나"를 보려면 이쪽이다. parts 를 주면 파트마다 색을 달리 칠한다.
"""
import bpy, os, sys, math
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
GLB, TAG = A[0], A[1]
PARTS = "parts" in A[2:]
ZOOM = "zoom" in A[2:]     # 상반신만 — 디테일이 어느 단계에서 잘렸는지 보려면 이쪽
HEAD = "head" in A[2:]     # 머리만
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(GLB))
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in obs:                       # 부모 회전까지 메시에 굽는다
    o.data.transform(o.matrix_world)
    o.matrix_world.identity()

co = np.vstack([np.array([v.co[:] for v in o.data.vertices]) for o in obs])
lo, hi = co.min(0), co.max(0)
if ZOOM or HEAD:            # 위에서 35% (머리·가슴) 또는 15% (머리만)
    f = 0.15 if HEAD else 0.35
    lo = lo.copy(); lo[2] = hi[2] - (hi[2]-lo[2])*f
    if HEAD:
        c = (lo[0]+hi[0])/2; w = (hi[0]-lo[0])*0.16
        lo = lo.copy(); hi = hi.copy(); lo[0], hi[0] = c-w, c+w
ctr, size = (lo+hi)/2, float((hi-lo).max())
print("파트 %d개 · bbox %s · 최대변 %.3f" % (len(obs), np.round(hi-lo, 3), size))

rs = np.random.RandomState(5)
for i, o in enumerate(obs):
    m = bpy.data.materials.new("m%d" % i)
    m.diffuse_color = (tuple(rs.uniform(0.15, 0.9, 3)) + (1,)) if PARTS else (0.62, 0.62, 0.66, 1)
    o.data.materials.clear(); o.data.materials.append(m)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.view_settings.view_transform = 'Standard'

for n, ang in (("a000", 0.0), ("a090", 90.0), ("a180", 180.0), ("a270", 270.0)):
    r = math.radians(ang)
    cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = size*1.25
    c = bpy.data.objects.new(n, cd)
    c.location = (ctr[0] + 3*size*math.sin(r), ctr[1] - 3*size*math.cos(r), ctr[2])
    c.rotation_euler = (math.radians(90), 0, r)
    sc.collection.objects.link(c); sc.camera = c
    sc.render.filepath = os.path.join(HERE, "%s_%s.png" % (TAG, n))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s_%s" % (TAG, n))
