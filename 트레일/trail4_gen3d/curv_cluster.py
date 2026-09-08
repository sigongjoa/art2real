# -*- coding: utf-8 -*-
"""곡률 클러스터링으로 분할이 되나. K 단독 vs (K,H) 주곡률.

    blender -b --python curv_cluster.py -- out/named2.blend out/kseg.blend

가우스 곡률 K = k1*k2 는 **전개가능면에서 전부 0** 이다 — 평면도, 원기둥도, 원뿔도.
갑주는 전개가능한 판이 능선에서 만나는 구조라 K 만으로는 판과 팔뚝이 안 갈린다.
평균곡률 H = (k1+k2)/2 는 원기둥에서 0 이 아니다. 그래서 둘을 같이 봐야 한다.

    k1,k2 = H +- sqrt(H^2 - K)
    shape index s = (2/pi) * atan((k2+k1)/(k2-k1))   in [-1,1]
       -1 컵  -0.5 홈  0 안장  +0.5 능선  +1 돔

K 는 각결손/면적, H 는 코탄젠트 라플라시안의 평균곡률 법선으로 잰다.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
TWO_PI = 2 * math.pi

bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
bpy.context.view_layer.objects.active = o
d = o.modifiers.new("d", 'DECIMATE'); d.ratio = 0.10
bpy.ops.object.modifier_apply(modifier="d")
s = o.modifiers.new("s", 'SMOOTH'); s.iterations = 30; s.factor = 0.7
bpy.ops.object.modifier_apply(modifier="s")
me = o.data
nv, nf = len(me.vertices), len(me.polygons)
co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
vn = np.empty(nv * 3); me.vertices.foreach_get("normal", vn); vn = vn.reshape(-1, 3)
print(f"정점 {nv:,} 면 {nf:,}")

bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
ang = np.zeros(nv); area = np.zeros(nv)
lap = np.zeros((nv, 3)); wsum = np.zeros(nv)
for f in bm.faces:
    vs = [l.vert for l in f.loops]
    n = len(vs)
    fa = f.calc_area()
    for i, v in enumerate(vs):
        p, q = vs[(i - 1) % n], vs[(i + 1) % n]
        e1, e2 = p.co - v.co, q.co - v.co
        if e1.length < 1e-12 or e2.length < 1e-12:
            continue
        a = e1.angle(e2)
        ang[v.index] += a
        area[v.index] += fa / n
        # 이 각의 반대편 에지 (p,q) 에 cot(a) 를 실어 준다
        # 각을 [1도,179도] 로 자른 뒤 cot. 안 자르면 데시메이트가 만든
        # 가늘고 긴 삼각형에서 cot 이 폭주해 |H| 가 1e5 대로 튄다
        # (그러면 k2~0 이 되어 shape index 가 전부 원기둥으로 나온다).
        aa = min(max(a, math.radians(1.0)), math.radians(179.0))
        c = 1.0 / math.tan(aa)
        dpq = np.array((q.co - p.co)[:])   # mathutils Vector 슬라이스는 tuple 이다
        lap[p.index] += c * dpq
        lap[q.index] -= c * dpq
        wsum[p.index] += c; wsum[q.index] += c
bnd = np.array([any(len(e.link_faces) < 2 for e in v.link_edges) for v in bm.verts])
bm.free()

area = np.maximum(area, 1e-12)
K = np.where(bnd, math.pi - ang, TWO_PI - ang) / area          # 1/길이^2
Hv = lap / (2 * area[:, None])
H = 0.5 * np.linalg.norm(Hv, axis=1) * np.sign(np.einsum('ij,ij->i', Hv, vn))
disc = np.maximum(H ** 2 - K, 0.0)
k1 = H + np.sqrt(disc); k2 = H - np.sqrt(disc)
den = (k2 - k1)
si = np.where(np.abs(den) > 1e-9, (2 / math.pi) * np.arctan((k2 + k1) / den), 0.0)
curvedness = np.sqrt((k1 ** 2 + k2 ** 2) / 2)

print("\n(1) K 단독으로 갈릴 수 있나 — |K| 가 작으면 전개가능(평면·원기둥·원뿔)")
kk = np.abs(K)
for t in (1, 3, 10, 30, 100):
    print(f"   |K| < {t:4d}  : {(kk<t).mean()*100:5.1f}% 의 정점")
print(f"   |K| 분위: p50 {np.percentile(kk,50):.1f}  p90 {np.percentile(kk,90):.1f} "
      f"p99 {np.percentile(kk,99):.1f}")
print(f"   |H| 분위: p50 {np.percentile(np.abs(H),50):.1f}  p90 {np.percentile(np.abs(H),90):.1f}")
print(f"   -> K 는 곡률반경 {1/math.sqrt(max(np.percentile(kk,50),1e-9))*1000:.0f}mm 수준,"
      f" H 는 {1/max(np.percentile(np.abs(H),50),1e-9)*1000:.0f}mm")

print("\n(2) shape index 분포 (-1 컵 / 0 안장 / +1 돔)")
h, e = np.histogram(si, bins=8, range=(-1, 1))
for a, b, c in zip(e, e[1:], h):
    print(f"   {a:+.2f} ~ {b:+.2f} : {c/nv*100:5.1f}%")
np.save(os.path.join(os.path.dirname(OUT), "..", "curv_si.npy"), si)
np.save(os.path.join(os.path.dirname(OUT), "..", "curv_K.npy"), K)
np.save(os.path.join(os.path.dirname(OUT), "..", "curv_H.npy"), H)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
