# -*- coding: utf-8 -*-
"""리토폴로지한 메시에 **v4 판 라벨 색을 굽는다.**

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python retopo_paint.py

130 번은 "생성 메시는 못 펴니 손으로 지은 것에 굽자"였다. 그런데 못 편 이유가
언랩기가 아니라 **리토폴로지를 안 한 것**이었다 (retopo_uv.py). 그러면 생성 형태를
버리지 않고도 펼 수 있다 — 여기서 정말 그런지 색까지 구워 확인한다.

라벨 이전은 **면 중심 + 꼭짓점 다수결**이다. 리토폴로지 쿼드 하나가 원본 면 200여 개를
덮으니 중심 한 점만 찍으면 얇은 데서 틀린다.
"""
import bpy, os, sys
import numpy as np
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tri_uv                                    # rasterize()/save()/PROVCOL 재사용

OUT = os.path.join(HERE, "out")
TAGS = ["q800"]

d = np.load(os.path.join(OUT, "tri_mesh.npz"))
V, F = d["V"].astype(float), d["F"]
cen = V[F].mean(1)                               # 원본 면 중심
col = np.load(os.path.join(OUT, "tri_col.npy")).astype(float)
lid = np.load(os.path.join(OUT, "tri_lid.npy"))          # 판 라벨 18종 (알베도 분할)
prov = np.load(os.path.join(OUT, "tri_prov.npy"))
poly = d["poly"]                                 # 삼각형 -> 원본 폴리곤 인덱스
kd = KDTree(len(cen))
for i, c in enumerate(cen):
    kd.insert(c, i)
kd.balance()
print("원본 면 %d · 색 %d 종" % (len(cen), len(np.unique(col[poly], axis=0))))


def transfer(me):
    """면마다 중심+꼭짓점을 쏘고 라벨 다수결. 색은 그 라벨의 평면색."""
    vs = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", vs); vs = vs.reshape(-1, 3)
    out_c = np.zeros((len(me.polygons), 3))
    out_p = np.zeros(len(me.polygons), int)
    out_l = np.zeros(len(me.polygons), int)
    for i, p in enumerate(me.polygons):
        pts = [np.array(p.center)] + [vs[v] for v in p.vertices]
        hits = [kd.find(tuple(q))[1] for q in pts]
        lab = [poly[h] for h in hits]
        win = max(set(lab), key=lab.count)       # 다수결. 동률이면 먼저 나온 것
        out_c[i] = col[win]
        out_p[i] = prov[win]
        out_l[i] = lid[win]
    return out_c, out_p, out_l


if __name__ == "__main__":
  for tag in TAGS:
      bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "retopo_%s.blend" % tag))
      o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
      me = o.data
      c, pr, _ = transfer(me)
      img, hit = tri_uv.rasterize(me, c, tri_uv.ATLAS)
      tri_uv.save(img, hit, "retopo_%s_col.png" % tag)
      img2, _ = tri_uv.rasterize(me, tri_uv.PROVCOL[pr], tri_uv.ATLAS)
      tri_uv.save(img2, hit, "retopo_%s_prov.png" % tag)
      n = len(me.polygons)
      print("PAINT %-7s 면 %5d  색 %3d 종  직접 %.1f%% 전파 %.1f%% 뿔계급 %.1f%% 못받음 %.1f%%  채운텍셀 %.1f%%"
            % (tag, n, len(np.unique(c, axis=0)),
               (pr == 0).mean()*100, (pr == 1).mean()*100, (pr == 2).mean()*100, (pr == 3).mean()*100,
               hit.mean()*100))
