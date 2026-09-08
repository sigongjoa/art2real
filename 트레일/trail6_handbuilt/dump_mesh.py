# -*- coding: utf-8 -*-
"""tri_paint.blend 에서 정점·면·면색을 꺼낸다 — xatlas 는 블렌더 밖에서 돈다."""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "tri_paint.blend"))
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
me.calc_loop_triangles()
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
tri = me.loop_triangles
F = np.empty(len(tri) * 3, np.int32); tri.foreach_get("vertices", F); F = F.reshape(-1, 3)
pidx = np.empty(len(tri), np.int32); tri.foreach_get("polygon_index", pidx)
np.savez(os.path.join(OUT, "tri_mesh.npz"), V=V.astype(np.float32), F=F, poly=pidx)
print("정점 %d · 삼각형 %d · 원본면 %d" % (len(V), len(F), len(me.polygons)))
