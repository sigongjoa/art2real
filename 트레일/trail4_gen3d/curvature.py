# -*- coding: utf-8 -*-
"""가우스 곡률을 재서 UV 왜곡을 **예측**한다. 스윕 대신 계산.

    blender -b --python curvature.py -- out/uv3.blend

이산 가우스 곡률 = 각 결손.
    내부 정점  K_v = 2*pi - sum(인접 삼각형의 v 에서의 각)
    경계 정점  K_v =   pi - sum(...)
가우스-보네: 닫힌 genus-0 표면이면 sum(K_v) = 4*pi. 이걸로 계산을 검증한다.

Theorema Egregium: K 는 등거리 변환의 불변량이다. 그래서 K != 0 인 조각은
등거리로 펼 수 없고, **펴려면 sum(K_v) 만큼의 각을 왜곡이나 자름으로 흡수해야 한다.**
즉 섬 하나의 총곡률 Omega = sum(K_v) 가 그 섬의 최소 왜곡을 결정한다.

그러면 스윕할 필요가 없다 —
    필요한 섬 수 >= (표면 전체의 |K| 적분) / (섬당 허용 Omega)
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
TWO_PI = 2.0 * math.pi


def defects(bm):
    """정점별 각 결손. 반환 (K[nv], 경계여부[nv], 정점면적[nv])"""
    nv = len(bm.verts)
    ang = np.zeros(nv)
    area = np.zeros(nv)
    bm.verts.ensure_lookup_table()
    for f in bm.faces:
        vs = [l.vert for l in f.loops]
        n = len(vs)
        a = f.calc_area() / n
        for i, v in enumerate(vs):
            p, q = vs[(i - 1) % n], vs[(i + 1) % n]
            e1 = (p.co - v.co); e2 = (q.co - v.co)
            if e1.length < 1e-12 or e2.length < 1e-12:
                continue
            ang[v.index] += e1.angle(e2)
            area[v.index] += a
    bnd = np.array([any(len(e.link_faces) < 2 for e in v.link_edges) for v in bm.verts])
    K = np.where(bnd, math.pi - ang, TWO_PI - ang)
    return K, bnd, area


def uv_islands(bm, uvl):
    bm.faces.ensure_lookup_table()
    lab = np.full(len(bm.faces), -1)
    cur = 0
    for f in bm.faces:
        if lab[f.index] >= 0:
            continue
        st = [f]; lab[f.index] = cur
        while st:
            c = st.pop()
            for l in c.loops:
                lr = l.link_loop_radial_next
                g = lr.face
                if lab[g.index] >= 0:
                    continue
                if (l[uvl].uv - lr.link_loop_next[uvl].uv).length < 1e-5 and \
                   (l.link_loop_next[uvl].uv - lr[uvl].uv).length < 1e-5:
                    lab[g.index] = cur; st.append(g)
        cur += 1
    return lab, cur


bpy.ops.wm.open_mainfile(filepath=SRC)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.uv_layers]

# --- 가우스-보네 검증: 전체 메시(닫힌 면)에서 sum(K) 가 4*pi 인가 ---
tot_K, tot_absK, tot_area = 0.0, 0.0, 0.0
rows = []
for o in objs:
    bm = bmesh.new(); bm.from_mesh(o.data)
    uvl = bm.loops.layers.uv.active
    K, bnd, varea = defects(bm)
    lab, n = uv_islands(bm, uvl)
    tot_K += K.sum(); tot_absK += np.abs(K).sum()
    tot_area += sum(f.calc_area() for f in bm.faces)

    # 섬별 총곡률과 실측 왜곡
    f_uv = []
    for f in bm.faces:
        a3 = f.calc_area()
        p = [l[uvl].uv for l in f.loops]
        a2 = 0.5 * abs(sum(p[i].x * p[(i + 1) % len(p)].y - p[i].y * p[(i + 1) % len(p)].x
                           for i in range(len(p))))
        f_uv.append((a3, a2))
    f_uv = np.array(f_uv)
    vlab = np.full(len(bm.verts), -1)
    for f in bm.faces:
        for l in f.loops:
            if vlab[l.vert.index] < 0:
                vlab[l.vert.index] = lab[f.index]
    for i in range(n):
        fm = lab == i
        if fm.sum() < 20:
            continue
        a3, a2 = f_uv[fm, 0], f_uv[fm, 1]
        ok = (a3 > 1e-12) & (a2 > 1e-14)
        if ok.sum() < 20:
            continue
        sc = np.sqrt(a2[ok] / a3[ok])
        dist = np.percentile(sc, 95) / max(np.percentile(sc, 5), 1e-12)
        om = float(K[vlab == i].sum())
        rows.append((o.name, int(fm.sum()), om, float(np.abs(K[vlab == i]).sum()), float(dist)))
    bm.free()

print(f"가우스-보네 검증: sum(K) = {tot_K:.2f}   (닫힌 genus-0 이면 4pi = {4*math.pi:.2f})")
print(f"  파츠로 잘린 열린 셸이라 경계항이 들어가 정확히 4pi 는 아니다")
print(f"전체 |K| 적분 = {tot_absK:.1f} sr,  표면적 {tot_area:.3f}")
print(f"섬 {len(rows)}개 분석")

R = np.array([(r[2], r[3], r[4]) for r in rows])
om, absom, dist = R[:, 0], R[:, 1], R[:, 2]
print()
print(f"{'|Omega| 구간':>16s} {'섬수':>5s} {'왜곡중앙':>8s} {'왜곡p90':>8s}")
edges = [0, 0.2, 0.5, 1.0, 2.0, 4.0, 100]
for a, b in zip(edges, edges[1:]):
    m = (np.abs(om) >= a) & (np.abs(om) < b)
    if m.sum() < 3:
        continue
    print(f"{a:6.1f} ~ {b:6.1f} {int(m.sum()):5d} {np.median(dist[m]):8.2f} "
          f"{np.percentile(dist[m],90):8.2f}")
c = np.corrcoef(np.abs(om), np.log(dist))[0, 1]
print(f"\n상관 corr(|Omega|, log 왜곡) = {c:+.3f}")

for cap in (1.5, 2.0, 3.0):
    ok = dist <= cap
    if ok.sum() < 5:
        continue
    thr = np.percentile(np.abs(om[ok]), 90)
    print(f"왜곡 <= {cap:.1f} 인 섬의 |Omega| p90 = {thr:.2f} sr"
          f"  -> 필요 섬 수 >= {tot_absK/max(thr,1e-6):.0f}")
