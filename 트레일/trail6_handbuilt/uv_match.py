# -*- coding: utf-8 -*-
"""**알베도 분할(판 라벨 18종)과 UV 섬이 맞물리나.** 순도로 답한다.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python uv_match.py

맞물리면 섬 하나 = 판 하나 = 평면색 하나라 채우기가 끝난다.
어긋나면 섬이 판 경계를 가로질러 굽는 순간 번진다 (v2 가 그랬다).

    match_island.png   UV, 섬마다 색 하나
    match_panel.png    UV, 판 라벨마다 색 하나
    두 장이 같은 모양이면 맞물린 것이다.
"""
import bpy, os, sys, json
import numpy as np
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tri_uv

OUT = os.path.join(HERE, "out")
TAG = "q800"

d = np.load(os.path.join(OUT, "tri_mesh.npz"))
V, F, poly = d["V"].astype(float), d["F"], d["poly"]
lid = np.load(os.path.join(OUT, "tri_lid.npy"))          # 판 라벨 18종 (알베도 분할)
col = np.load(os.path.join(OUT, "tri_col.npy")).astype(float)
cen = V[F].mean(1)
kd = KDTree(len(cen))
for i, c in enumerate(cen):
    kd.insert(c, i)
kd.balance()

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "retopo_%s.blend" % TAG))
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nf = len(me.polygons)
vs = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", vs); vs = vs.reshape(-1, 3)
area = np.empty(nf); me.polygons.foreach_get("area", area)

# 1) 면마다 판 라벨 (중심+꼭짓점 다수결)
lab = np.zeros(nf, int); fcol = np.zeros((nf, 3))
for i, p in enumerate(me.polygons):
    hits = [kd.find(tuple(q))[1] for q in [np.array(p.center)] + [vs[v] for v in p.vertices]]
    ids = [poly[h] for h in hits]
    win = max(set(ids), key=ids.count)
    lab[i] = lid[win]; fcol[i] = col[win]

# 2) 면마다 UV 섬 (UV 정점을 좌표로 용접)
uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
_, inv = np.unique(np.round(uv * 20000).astype(np.int64), axis=0, return_inverse=True)
par = np.arange(inv.max() + 1)
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for i in range(nf):
    r = find(inv[ls[i]])
    for k in range(1, lt[i]):
        t = find(inv[ls[i] + k])
        if r != t: par[t] = r
isl_raw = np.array([find(inv[ls[i]]) for i in range(nf)])
_, isl = np.unique(isl_raw, return_inverse=True)
nisl = isl.max() + 1
npan = len(np.unique(lab))
print("면 %d · UV 섬 %d · 판 라벨 %d" % (nf, nisl, npan))

# 3) 교차표 — 섬의 순도 (면적 가중)
pure_w = 0.0
mixed = 0
for s in range(nisl):
    m = isl == s
    tot = area[m].sum()
    shares = np.array([area[m & (lab == L)].sum() for L in np.unique(lab[m])])
    top = shares.max() / tot
    pure_w += shares.max()
    if top < 0.999:
        mixed += 1
print("섬 순도(면적가중 평균)  %.1f%%   판을 두 개 이상 물고 있는 섬 %d/%d" % (pure_w/area.sum()*100, mixed, nisl))

# 4) 반대 방향 — 판 하나가 몇 섬에 흩어졌나
print("\n%-8s %8s %8s %8s" % ("판", "면적%", "섬 수", "최대섬%"))
for L in np.unique(lab):
    m = lab == L
    ss = np.unique(isl[m])
    big = max(area[m & (isl == s)].sum() for s in ss) / area[m].sum()
    print("%-8d %7.1f%% %8d %7.0f%%" % (L, area[m].sum()/area.sum()*100, len(ss), big*100))

# 5) 그림 두 장
rs = np.random.RandomState(3)
img, hit = tri_uv.rasterize(me, rs.uniform(60, 235, (nisl, 3))[isl], tri_uv.ATLAS)
tri_uv.save(img, hit, "match_island.png")
pc = rs.uniform(60, 235, (lab.max() + 1, 3))
img2, _ = tri_uv.rasterize(me, pc[lab], tri_uv.ATLAS)
tri_uv.save(img2, hit, "match_panel.png")
