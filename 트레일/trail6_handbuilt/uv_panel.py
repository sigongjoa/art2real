# -*- coding: utf-8 -*-
"""**판 경계를 이음선으로 박고 편다.** 각도 언랩을 버린다.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python uv_panel.py

uv_match 가 잰 것: smart_project 의 섬 72개는 판 15개와 직교한다 (섬 순도 72.1%,
판 18 하나가 47섬으로 흩어짐). 각도로 자르니 재질 경계와 맞을 이유가 없다.

그러면 자를 곳을 바꾼다 — **알베도 분할이 준 판 경계가 곧 이음선**이다.
그러면 섬 = 판이 되고 순도는 지어서 100% 다. 남는 질문은 채움과 밀도편차뿐이다.

예전에 "능선을 이음선으로"가 진 이유 둘은 여기 없다: 능선이 모자랐던 것(이음선이
재질 경계라 정확히 있다) · 71,842면 계단(723 쿼드다).
"""
import bpy, bmesh, os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tri_uv
import mask2d
import retopo_paint as rp                          # transfer() 재사용

OUT = os.path.join(HERE, "out")
TAG = "q800"


def uv_stats(me):
    nf = len(me.polygons)
    uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    ar3 = np.empty(nf); me.polygons.foreach_get("area", ar3)
    ar2 = np.array([0.5 * abs(np.dot(uv[ls[i]:ls[i]+lt[i], 0], np.roll(uv[ls[i]:ls[i]+lt[i], 1], -1))
                              - np.dot(uv[ls[i]:ls[i]+lt[i], 1], np.roll(uv[ls[i]:ls[i]+lt[i], 0], -1)))
                    for i in range(nf)])
    ok = (ar3 > 1e-12) & (ar2 > 1e-14)
    s = np.sqrt(ar2[ok] / ar3[ok]); s /= np.median(s)
    dev = float(np.percentile(s, 95) / max(np.percentile(s, 5), 1e-9))
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
    _, isl = np.unique(np.array([find(inv[ls[i]]) for i in range(nf)]), return_inverse=True)
    return uv, ls, lt, ar3, isl, isl.max() + 1, dev, float(ar2.sum())


def purity(isl, nisl, lab, ar3):
    tot = sum(max(ar3[(isl == s) & (lab == L)].sum() for L in np.unique(lab[isl == s]))
              for s in range(nisl))
    mixed = sum(1 for s in range(nisl) if len(np.unique(lab[isl == s])) > 1)
    return tot / ar3.sum() * 100, mixed


bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "retopo_%s.blend" % TAG))
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
bpy.context.view_layer.objects.active = o
for x in bpy.context.scene.objects: x.select_set(x is o)
me = o.data
# 라벨은 remap_all.py 가 세 판(front 18 + side 16 + back 23)으로 배정해 메시에 박았다.
# 예전 판(front 18 + side 1 뭉뚱그림)은 라벨 하나가 아틀라스 55.8% 를 먹었다.
nf = len(me.polygons)
lab = np.load(os.path.join(OUT, "remap_lab.npy"))   # 면 순서는 retopo_q800 과 같다
assert len(lab) == nf, (len(lab), nf)
col = np.load(os.path.join(OUT, "remap_col.npy"))
src = np.load(os.path.join(OUT, "remap_src.npy"))
prov = np.where(src >= 0, 0, 1).astype(int)          # 직접 읽음 / 전파
print("라벨 %d개 · 직접 %d면 (%.1f%%)" % (len(np.unique(lab)), (src >= 0).sum(), (src >= 0).mean()*100))

*_, isl0, n0, dev0, s0 = uv_stats(me)
p0, m0 = purity(isl0, n0, lab, np.array([p.area for p in me.polygons]))
print("각도 언랩 (전)   섬 %3d  순도 %.1f%%  섞인섬 %2d  밀도편차 %.2f  채움 %.1f%%" % (n0, p0, m0, dev0, s0*100))

# 판 경계 = 이음선
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
for e in bm.edges:
    lf = e.link_faces
    e.seam = (len(lf) != 2) or (lab[lf[0].index] != lab[lf[1].index])
nseam = sum(1 for e in bm.edges if e.seam)
bm.to_mesh(me); bm.free()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')

uv, ls, lt, ar3, isl, nisl, dev, ssum = uv_stats(me)
p1, m1 = purity(isl, nisl, lab, ar3)
print("판 이음선 (후)   섬 %3d  순도 %.1f%%  섞인섬 %2d  밀도편차 %.2f  채움 %.1f%%  이음선 %d"
      % (nisl, p1, m1, dev, ssum*100, nseam))

# 라벨을 메시에 박는다 — 후면 보정까지 반영된 진실은 여기 하나뿐이다
at = me.attributes.get("panel") or me.attributes.new("panel", 'INT', 'FACE')
at.data.foreach_set("value", lab.astype(np.int32).tolist())

np.savez(os.path.join(OUT, "panel_%s.npz" % TAG), uv=uv, ls=ls, lt=lt)
img, hit = tri_uv.rasterize(me, col, tri_uv.ATLAS);            tri_uv.save(img, hit, "panel_col.png")
img2, _ = tri_uv.rasterize(me, tri_uv.PROVCOL[prov], tri_uv.ATLAS); tri_uv.save(img2, hit, "panel_prov.png")
rs = np.random.RandomState(3)
img3, _ = tri_uv.rasterize(me, rs.uniform(60, 235, (nisl, 3))[isl], tri_uv.ATLAS)
tri_uv.save(img3, hit, "panel_island.png")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "panel_%s.blend" % TAG))
