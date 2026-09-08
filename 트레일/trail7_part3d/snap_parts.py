# -*- coding: utf-8 -*-
"""떠 있는 파트를 몸에 붙인다. **재고 나서 옮긴다.**

    blender -b --python snap_parts.py -- out/omega.blend            # 재기만
    blender -b --python snap_parts.py -- out/omega.blend --apply    # 옮기고 저장

PartCrafter 는 파트를 서로 안 붙여놓는다(견갑 때부터 관찰). 각 조각에서 몸(body+legs)
까지 **최근접 점 쌍**을 찾아 그 벡터만큼 민다 — 방향을 손으로 정하지 않는다.

ponytail: 정점 부분표본 + kd트리. 면 수십만이라 전수는 느리다. 표본이 모자라면
STEP 을 줄일 것.
"""
import bpy, os, sys
import numpy as np
from mathutils.kdtree import KDTree

A = sys.argv[sys.argv.index("--")+1:]
SRC = os.path.abspath(A[0])
APPLY = "--apply" in A

ANCHOR = ("body", "legs")          # 안 움직이는 것
MOVE = ("shoulder", "cannon", "forearm", "sword")
STEP = 7                            # 정점 표본 간격 (노브)

bpy.ops.wm.open_mainfile(filepath=SRC)
obs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}

anchor_v = np.vstack([np.array([v.co[:] for v in obs[n].data.vertices])[::STEP] for n in ANCHOR if n in obs])
kd = KDTree(len(anchor_v))
for i, p in enumerate(anchor_v):
    kd.insert(p.tolist(), i)
kd.balance()
print("기준 정점 %d개 (%s)" % (len(anchor_v), ", ".join(ANCHOR)))

for name in MOVE:
    o = obs.get(name)
    if o is None:
        continue
    v = np.array([x.co[:] for x in o.data.vertices])[::STEP]
    best = None
    for p in v:
        q, idx, d = kd.find(p.tolist())
        if best is None or d < best[0]:
            best = (d, np.array(q) - p)
    d, vec = best
    print("%-9s 간격 %.4f  이동 %s" % (name, d, np.round(vec, 4)))
    if APPLY and d > 1e-4:
        o.location = tuple(np.array(o.location) + vec)

if APPLY:
    bpy.ops.wm.save_mainfile(filepath=SRC)
    print("저장 %s" % SRC)
