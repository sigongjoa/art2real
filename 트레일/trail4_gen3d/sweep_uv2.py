# -*- coding: utf-8 -*-
"""Smart UV vs 샤프시임+각도기반 언랩. 어느 쪽이 섬을 덜 부수나.

    blender -b --python sweep_uv2.py -- out/named2.blend

3D 연결성분은 35파츠에 90개뿐이다(파츠는 이어져 있다). 그러니 섬 3,255개는
Smart UV 가 법선 군집으로 평면을 잡으면서 표면을 잘게 끊은 결과다.
production 표준은 샤프 에지에 시임을 찍고 각도기반으로 펴는 것이다.
"""
import json
import math
import os
import sys

import bpy
import bmesh
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])


def islands(me):
    bm = bmesh.new(); bm.from_mesh(me)
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
    bm.free(); return n


def stretch(o):
    m = o.data
    uv = np.empty(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_total", lt)
    a3 = np.empty(len(m.polygons)); m.polygons.foreach_get("area", a3)
    a2 = np.array([0.5 * abs(np.dot(uv[s:s + t, 0], np.roll(uv[s:s + t, 1], -1)) -
                             np.dot(uv[s:s + t, 1], np.roll(uv[s:s + t, 0], -1)))
                   for s, t in zip(ls, lt)])
    sc = np.sqrt(np.divide(a2, a3, out=np.zeros_like(a2), where=a3 > 1e-12))
    sc = sc[sc > 0]
    return float(np.percentile(sc, 95) / max(np.percentile(sc, 5), 1e-9))


bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = src.data
nf = len(me.polygons)
lab = np.empty(nf, np.int32); me.attributes["part_id"].data.foreach_get("value", lab)
names = json.load(open(os.path.join(os.path.dirname(SRC), "..", "named_parts.json")))
n2p = {names[i]: i + 1 for i in range(len(names))}

print(f"{'파츠':14s} {'방법':30s} {'면':>6s} {'섬':>6s} {'면/섬':>7s} {'왜곡':>6s}")
for pname in ("r_wolf_cannon", "c_foot", "c_shin", "a_cuirass"):
    sel = np.nonzero(lab == n2p[pname])[0]
    for tag, smooth, mode, sharp in (
            ("smart66 (현재)", 0, "smart", None),
            ("smooth10 + smart89", 10, "smart", None),
            ("sharp30 seam + angle", 0, "unwrap", 30),
            ("smooth10 + sharp40 + angle", 10, "unwrap", 40),
            ("smooth10 + sharp55 + angle", 10, "unwrap", 55)):
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        ks = set(sel.tolist())
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context='FACES')
        m2 = bpy.data.meshes.new("t"); bm.to_mesh(m2); bm.free()
        o = bpy.data.objects.new("t", m2); bpy.context.scene.collection.objects.link(o)
        d = o.modifiers.new("d", 'DECIMATE'); d.ratio = 0.10
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="d")
        if smooth:
            s = o.modifiers.new("s", 'SMOOTH'); s.iterations = smooth; s.factor = 0.7
            bpy.ops.object.modifier_apply(modifier="s")
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        if mode == "smart":
            bpy.ops.uv.smart_project(angle_limit=math.radians(66 if not smooth else 89),
                                     island_margin=0.012)
        else:
            bpy.ops.mesh.mark_seam(clear=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.edges_select_sharp(sharpness=math.radians(sharp))
            bpy.ops.mesh.mark_seam(clear=False)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.012)
            bpy.ops.uv.pack_islands(margin=0.012)
        bpy.ops.object.mode_set(mode='OBJECT')
        f, i = len(o.data.polygons), islands(o.data)
        print(f"{pname:14s} {tag:30s} {f:6,} {i:6,} {f/max(i,1):7.1f} {stretch(o):6.1f}")
        bpy.data.objects.remove(o, do_unlink=True)
