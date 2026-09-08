# -*- coding: utf-8 -*-
"""잡음을 걷은 곡률이 UV 왜곡을 예측하는지 본다.

    blender -b --python curv_predict.py -- out/named2.blend

앞 시도가 실패한 이유 둘:
  1) 마칭큐브 계단면의 각 결손이 잡음. ∫|K| 가 구의 248배였다.
  2) **자른 뒤에** 쟀다. 잘린 가장자리는 곡률이 아닌데 경계항(pi - sum)으로
     들어간다 — 닫힌 메시 3,119 vs 자른 파츠 36,798.

그래서 이번엔 (a) 평활하고 (b) **자르기 전 닫힌 메시에서** K 를 재서 정점에
저장한 뒤, 자르고 펴고 나서 섬별로 합산한다.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
TWO_PI = 2.0 * math.pi
SMOOTH, RATIO = 30, 0.10

bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = src
d = src.modifiers.new("d", 'DECIMATE'); d.ratio = RATIO
bpy.ops.object.modifier_apply(modifier="d")
s = src.modifiers.new("s", 'SMOOTH'); s.iterations = SMOOTH; s.factor = 0.7
bpy.ops.object.modifier_apply(modifier="s")
me = src.data
nv = len(me.vertices)

# --- 닫힌 상태에서 K 를 재서 정점에 저장 ---
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
ang = np.zeros(nv)
for f in bm.faces:
    vs = [l.vert for l in f.loops]
    n = len(vs)
    for i, v in enumerate(vs):
        e1 = vs[(i - 1) % n].co - v.co; e2 = vs[(i + 1) % n].co - v.co
        if e1.length > 1e-12 and e2.length > 1e-12:
            ang[v.index] += e1.angle(e2)
bnd = np.array([any(len(e.link_edges) if False else len(e.link_faces) < 2
                    for e in v.link_edges) for v in bm.verts])
bm.free()
K = np.where(bnd, math.pi - ang, TWO_PI - ang)
print(f"닫힌 메시: 정점 {nv:,}  sum K {K.sum():.1f}  ∫|K| {np.abs(K).sum():.1f} "
      f"({np.abs(K).sum()/(4*math.pi):.0f}x 구)")
at = me.attributes.new("gauss", 'FLOAT', 'POINT')
at.data.foreach_set("value", K.astype(np.float32))

lab = np.empty(len(me.polygons), np.int32)
me.attributes["part_id"].data.foreach_get("value", lab)
uniq, cnt = np.unique(lab, return_counts=True)

rows = []
for pid, c in zip(uniq, cnt):
    if c < 200:
        continue
    sel = set(np.nonzero(lab == pid)[0].tolist())
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in sel], context='FACES')
    m2 = bpy.data.meshes.new("t"); bm.to_mesh(m2); bm.free()
    o = bpy.data.objects.new("t", m2)
    bpy.context.scene.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(89), island_margin=0.012)
    bpy.ops.object.mode_set(mode='OBJECT')

    g = np.empty(len(m2.vertices)); m2.attributes["gauss"].data.foreach_get("value", g)
    bm = bmesh.new(); bm.from_mesh(m2)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    isl = np.full(len(bm.faces), -1); cur = 0
    for f in bm.faces:
        if isl[f.index] >= 0:
            continue
        st = [f]; isl[f.index] = cur
        while st:
            cc = st.pop()
            for l in cc.loops:
                lr = l.link_loop_radial_next; gg = lr.face
                if isl[gg.index] >= 0:
                    continue
                if (l[uvl].uv - lr.link_loop_next[uvl].uv).length < 1e-5 and \
                   (l.link_loop_next[uvl].uv - lr[uvl].uv).length < 1e-5:
                    isl[gg.index] = cur; st.append(gg)
        cur += 1
    vis = np.full(len(bm.verts), -1)
    fa3, fa2 = [], []
    for f in bm.faces:
        fa3.append(f.calc_area())
        p = [l[uvl].uv for l in f.loops]
        fa2.append(0.5 * abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[i].y * p[(i + 1) % len(p)].x
                                 for i in range(len(p)))))
        for l in f.loops:
            if vis[l.vert.index] < 0:
                vis[l.vert.index] = isl[f.index]
    fa3 = np.array(fa3); fa2 = np.array(fa2)
    bm.free()
    for i in range(cur):
        fm = isl == i
        if fm.sum() < 40:
            continue
        ok = (fa3[fm] > 1e-12) & (fa2[fm] > 1e-14)
        if ok.sum() < 40:
            continue
        sc = np.sqrt(fa2[fm][ok] / fa3[fm][ok])
        dist = float(np.percentile(sc, 95) / max(np.percentile(sc, 5), 1e-12))
        om = float(np.abs(g[vis == i]).sum())
        rows.append((om, dist, int(fm.sum())))
    bpy.data.objects.remove(o, do_unlink=True)

R = np.array(rows)
om, dist = R[:, 0], R[:, 1]
print(f"섬 {len(R)}개")
print(f"{'∫|K| 구간(sr)':>16s} {'섬수':>5s} {'왜곡중앙':>8s} {'왜곡p90':>8s}")
edges = [0, 1, 3, 8, 20, 50, 1e9]
for a, b in zip(edges, edges[1:]):
    m = (om >= a) & (om < b)
    if m.sum() < 3:
        continue
    print(f"{a:7.0f} ~ {b:7.0f} {int(m.sum()):5d} {np.median(dist[m]):8.2f} "
          f"{np.percentile(dist[m],90):8.2f}")
print(f"\n상관 corr(∫|K|, log 왜곡) = {np.corrcoef(om, np.log(dist))[0,1]:+.3f}")
print(f"     corr(면수,   log 왜곡) = {np.corrcoef(R[:,2], np.log(dist))[0,1]:+.3f}")
