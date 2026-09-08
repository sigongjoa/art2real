# -*- coding: utf-8 -*-
"""생성 GLB 를 **판정기와 같은 정렬**로 찍는다. 파트마다 색 하나.

    blender -b --python shot_glb.py -- out/pc_front.glb out/pc_front

정렬 규약은 judge_part3d.fit 과 같아야 한다 — 정면 bbox 를 견갑 실측 상자에
한 배율로 맞춘다 (tri_shot.py 72번 규약).
"""
import bpy, os, sys, math
import numpy as np

U0, U1, Z0, Z1 = 0.112, 0.245, 0.788, 0.990
A = sys.argv[sys.argv.index("--")+1:]
GLB, TAG = A[0], A[1]
SOLID = "solid" in A[2:]   # 파트 색을 끄고 한 재질로 — 합친 형태만 본다
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(GLB))
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
print("임포트 파트 %d개" % len(obs))
for o in obs:
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
# glTF 임포터는 메시를 **회전된 부모 밑에** 붙인다(Y-up -> Z-up). 자식 변환만 적용하면
# 90도 누운 채로 찍힌다. 월드행렬을 메시에 굽고 오브젝트 변환을 비운다.
for o in obs:
    o.data.transform(o.matrix_world)
    o.matrix_world.identity()

allco = np.vstack([np.array([v.co[:] for v in o.data.vertices]) for o in obs])
lo, hi = allco.min(0), allco.max(0)
s = min((U1-U0)/max(hi[0]-lo[0], 1e-9), (Z1-Z0)/max(hi[2]-lo[2], 1e-9))
off = np.array([(U0+U1)/2-(lo[0]+hi[0])/2*s, 0.027-(lo[1]+hi[1])/2*s, (Z0+Z1)/2-(lo[2]+hi[2])/2*s])
rs = np.random.RandomState(5)
for i, o in enumerate(obs):
    o.scale = (s, s, s)
    bpy.context.view_layer.objects.active = o
    for x in obs: x.select_set(x is o)
    bpy.ops.object.transform_apply(scale=True)
    o.location = tuple(off)
    m = bpy.data.materials.new("p%d" % i)
    m.diffuse_color = (0.62, 0.62, 0.66, 1) if SOLID else tuple(rs.uniform(0.15, 0.9, 3)) + (1,)
    o.data.materials.clear(); o.data.materials.append(m)
    print("  파트 %d 면 %d" % (i, len(o.data.polygons)))

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_cavity = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 512
sc.view_settings.view_transform = 'Standard'
cx, cz = (U0+U1)/2, (Z0+Z1)/2
for n, ang in (("front", 0.0), ("q", 40.0), ("side", 90.0)):
    a = math.radians(ang)
    cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = 0.30
    c = bpy.data.objects.new(n, cd)
    c.location = (cx + 2*math.sin(a), 0.027 - 2*math.cos(a), cz)
    c.rotation_euler = (math.radians(90), 0, a)
    sc.collection.objects.link(c); sc.camera = c
    sc.render.filepath = os.path.join(HERE, "%s_%s.png" % (TAG, n))
    bpy.ops.render.render(write_still=True)
    print("찍음 %s_%s" % (TAG, n))
