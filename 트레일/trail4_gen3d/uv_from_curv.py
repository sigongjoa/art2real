# -*- coding: utf-8 -*-
"""곡률 분할 경계를 UV 시임으로 써서 편다. Smart UV 대조군과 비교.

    blender -b --python uv_from_curv.py -- out/curvseg.blend

가설: 곡률 분할은 형태 전환에서 자르므로 조각이 전개가능면에 가깝다.
그렇다면 그 경계를 시임으로 삼으면 Smart UV 보다 섬이 적고 왜곡도 낮아야 한다.
앞선 최고 기록은 파츠별 방법 자동선택으로 **섬 1,800 / 왜곡 <=1.8** (면 99,428).
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])


def measure(o):
    m = o.data
    bm = bmesh.new(); bm.from_mesh(m)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    seen, n = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        n += 1; st = [f]; seen.add(f.index)
        while st:
            c = st.pop()
            for l in c.loops:
                lr = l.link_loop_radial_next; g = lr.face
                if g.index in seen:
                    continue
                if (l[uvl].uv - lr.link_loop_next[uvl].uv).length < 1e-5 and \
                   (l.link_loop_next[uvl].uv - lr[uvl].uv).length < 1e-5:
                    seen.add(g.index); st.append(g)
    bm.free()
    nf = len(m.polygons)
    uv = np.empty(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(nf, np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); m.polygons.foreach_get("loop_total", lt)
    a3 = np.empty(nf); m.polygons.foreach_get("area", a3)
    a2 = np.array([0.5 * abs(np.dot(uv[s:s + t, 0], np.roll(uv[s:s + t, 1], -1)) -
                             np.dot(uv[s:s + t, 1], np.roll(uv[s:s + t, 0], -1)))
                   for s, t in zip(ls, lt)])
    ok = (a3 > 1e-12) & (a2 > 1e-14)
    sc = np.sqrt(a2[ok] / a3[ok])
    return n, float(np.percentile(sc, 95) / max(np.percentile(sc, 5), 1e-12)), float(a2.sum())


bpy.ops.wm.open_mainfile(filepath=SRC)
src = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
nf = len(src.data.polygons)
lab = np.empty(nf, np.int32); src.data.attributes["part_id"].data.foreach_get("value", lab)
print(f"면 {nf:,}  곡률조각 {len(np.unique(lab))}")

print(f"{'방법':32s} {'섬':>7s} {'왜곡':>6s} {'UV채움':>7s}")
for tag in ("곡률경계 시임 + 각도기반", "곡률경계+샤프40 시임 + 각도기반", "Smart UV 89 (대조군)"):
    o = src.copy(); o.data = src.data.copy()
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(o.data)
    bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    for e in bm.edges:
        e.seam = False
    if tag.startswith("곡률"):
        for e in bm.edges:
            if len(e.link_faces) == 2 and lab[e.link_faces[0].index] != lab[e.link_faces[1].index]:
                e.seam = True
        bmesh.update_edit_mesh(o.data)
    bpy.ops.mesh.select_all(action='SELECT')
    if "샤프40" in tag:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.edges_select_sharp(sharpness=math.radians(40))
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.select_all(action='SELECT')
    if tag.startswith("Smart"):
        bpy.ops.uv.smart_project(angle_limit=math.radians(89), island_margin=0.003)
    else:
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.003)
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    isl, dist, fill = measure(o)
    print(f"{tag:32s} {isl:7,} {dist:6.2f} {fill:7.3f}")
    if tag.startswith("곡률경계 시임"):
        o.name = "uv_curv"
    else:
        bpy.data.objects.remove(o, do_unlink=True)
print("앞선 최고: 파츠별 자동선택  섬 1,800  왜곡 <=1.8  (면 99,428)")
bpy.data.objects.remove(src, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=SRC.replace("curvseg", "uvcurv"))
print("SAVED")
