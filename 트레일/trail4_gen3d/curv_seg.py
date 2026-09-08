# -*- coding: utf-8 -*-
"""곡률 클러스터링 분할을 실제로 해보고, 이름 붙은 프록시 분할과 비교한다.

    blender -b --python curv_seg.py -- out/kseg.blend out/curvseg.blend

shape index 로 면을 5종(컵/홈/안장/능선/돔)으로 나누고 각 종의 연결성분을 조각으로.
비교 지표:
    조각 수 / 400면 이상 수 / 최대 조각 비율
    경계 일치도 = 곡률분할 경계 에지 중 프록시분할 경계와 겹치는 비율
"""
import math
import os
import sys
from collections import defaultdict

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
MIN_FACES = 400

bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nf = len(me.polygons)
si = np.load(os.path.join(HERE, "curv_si.npy"))
K = np.load(os.path.join(HERE, "curv_K.npy"))
H = np.load(os.path.join(HERE, "curv_H.npy"))
pid = np.empty(nf, np.int32)
me.attributes["part_id"].data.foreach_get("value", pid)          # 프록시 분할(비교군)

fsi = np.array([np.mean([si[v] for v in p.vertices]) for p in me.polygons])
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
adj = [[] for _ in range(nf)]
for e in bm.edges:
    if len(e.link_faces) == 2:
        a, b = e.link_faces[0].index, e.link_faces[1].index
        adj[a].append(b); adj[b].append(a)
bm.free()


def comps(cls):
    lab = np.full(nf, -1); cur = 0
    for i in range(nf):
        if lab[i] >= 0:
            continue
        st = [i]; lab[i] = cur
        while st:
            c = st.pop()
            for j in adj[c]:
                if lab[j] < 0 and cls[j] == cls[c]:
                    lab[j] = cur; st.append(j)
        cur += 1
    return lab, cur


def merge_small(lab):
    for _ in range(10):
        cnt = np.bincount(lab)
        small = set(np.nonzero(cnt < MIN_FACES)[0].tolist())
        if not small:
            break
        touch = defaultdict(lambda: defaultdict(int))
        for i in range(nf):
            for j in adj[i]:
                if lab[i] != lab[j] and lab[i] in small:
                    touch[lab[i]][lab[j]] += 1
        moved = 0
        for s_ in list(small):
            if touch[s_]:
                lab[lab == s_] = max(touch[s_].items(), key=lambda kv: kv[1])[0]; moved += 1
        if not moved:
            break
        _, lab = np.unique(lab, return_inverse=True)
    return lab


def bnd_edges(lab):
    return {(min(i, j), max(i, j)) for i in range(nf) for j in adj[i] if lab[i] != lab[j]}


ref_b = bnd_edges(pid)
print(f"{'구분':26s} {'조각':>7s} {'400+':>5s} {'최대비':>7s} {'경계에지':>8s} {'프록시경계와 겹침':>14s}")
print(f"{'프록시(이름 붙은 분할)':26s} {len(np.unique(pid)):7,} "
      f"{int((np.bincount(pid)>=MIN_FACES).sum()):5d} "
      f"{np.bincount(pid).max()/nf*100:6.1f}% {len(ref_b):8,} {'-':>14s}")

SCHEMES = {
    "shape index 5종": [-1.0, -0.625, -0.375, 0.375, 0.625, 1.0],
    "shape index 9종": list(np.linspace(-1, 1, 10)),
    "K 부호 3종": None,
}
out_lab = None
for name, edges in SCHEMES.items():
    if edges is None:
        fK = np.array([np.mean([K[v] for v in p.vertices]) for p in me.polygons])
        t = np.percentile(np.abs(fK), 50)
        cls = np.where(fK > t, 2, np.where(fK < -t, 0, 1))
    else:
        cls = np.digitize(fsi, edges[1:-1])
    lab, n0 = comps(cls)
    lab = merge_small(lab.copy())
    cnt = np.bincount(lab)
    b = bnd_edges(lab)
    ov = len(b & ref_b) / max(len(b), 1)
    print(f"{name:26s} {len(cnt):7,} {int((cnt>=MIN_FACES).sum()):5d} "
          f"{cnt.max()/nf*100:6.1f}% {len(b):8,} {ov*100:13.1f}%")
    if name.startswith("shape index 5"):
        out_lab = lab

me.attributes["part_id"].data.foreach_set("value", (out_lab + 1).astype(np.int32))
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
