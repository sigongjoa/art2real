# -*- coding: utf-8 -*-
"""발만 떼서 원화 3판과 좌표·크기를 맞춰본다.

    blender -b --python foot_align.py -- out/named2.blend out/fa

전신 실루엣 IoU 로 잡은 정렬(FIT)이 발에서도 맞는지는 별개다. 발 구간만
같은 좌표창으로 렌더해서 원화 판과 겹친다.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, PRE = os.path.abspath(argv[0]), os.path.abspath(argv[1])
RES, SPAN = 1024, 1.2
ZC = 0.5

bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
cen = np.empty(len(me.polygons) * 3); me.polygons.foreach_get("center", cen)
cen = cen.reshape(-1, 3)

# z 로 자르면 검 끝(x -0.35)까지 딸려온다. 이름 붙은 파츠로 발만 고른다.
import json
names = json.load(open(os.path.join(os.path.dirname(SRC), "..", "named_parts.json")))
pid = np.empty(len(me.polygons), np.int32)
me.attributes["part_id"].data.foreach_get("value", pid)
want = {i + 1 for i, n in enumerate(names)
        if n in ("c_foot", "c_foot_M", "c_claw0", "c_claw1", "c_claw2", "c_footband")}
keep = set(np.nonzero(np.isin(pid, list(want)))[0].tolist())
print("발 파츠:", sorted(names[i - 1] for i in want if i - 1 < len(names)))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
m2 = bpy.data.meshes.new("foot"); bm.to_mesh(m2); bm.free()
fo = bpy.data.objects.new("foot", m2)
bpy.context.scene.collection.objects.link(fo)
bpy.data.objects.remove(o, do_unlink=True)

v = np.empty(len(m2.vertices) * 3); m2.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
print(f"생성 발: 면 {len(m2.polygons):,}")
print(f"  x [{v[:,0].min():+.4f}, {v[:,0].max():+.4f}]  폭 {v[:,0].max()-v[:,0].min():.4f}")
print(f"  y [{v[:,1].min():+.4f}, {v[:,1].max():+.4f}]  깊이 {v[:,1].max()-v[:,1].min():.4f}")
print(f"  z [{v[:,2].min():+.4f}, {v[:,2].max():+.4f}]")
r = v[v[:, 0] > 0.02]
print(f"  오른발만: x [{r[:,0].min():+.4f}, {r[:,0].max():+.4f}]  "
      f"y [{r[:,1].min():+.4f}, {r[:,1].max():+.4f}]")

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (1, 1, 1)
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = RES
sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = SPAN
cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for az, tag in ((0, "front"), (90, "side"), (180, "back")):
    a = math.radians(az)
    cam.location = (math.sin(a) * 6, -math.cos(a) * 6, ZC)
    cam.rotation_euler = (math.radians(90), 0, a)
    sc.render.filepath = f"{PRE}_{tag}.png"
    bpy.ops.render.render(write_still=True)
print("FOOTALIGN OK")
