# -*- coding: utf-8 -*-
"""파츠 경계를 메시 자신의 **접힘선**으로 스냅한다.

    blender -b --python snap_creases.py -- out/parts.blend out/parts2.blend

project_parts.py 는 원화의 2D 블롭을 그대로 던진다. 그래서 경계가 메시의 능선이
아니라 그림 가장자리에 떨어져 너덜거린다. 여기서는

    1) 각 영역을 침식해 확실한 **씨앗**만 남기고
    2) 다이헤드럴 각을 비용으로 하는 Dijkstra 로 다시 키운다.

평평한 면끼리는 싸게 붙고, 접힌 곳을 넘으려면 비싸다 -> 경계가 접힘선에 눌어붙는다.
"""
import heapq
import math
import os
import sys
import time

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
CREASE_K = 24.0          # 접힘 비용 배율. 클수록 경계가 능선에 더 달라붙는다
BAND = int(os.environ.get("SNAP_BAND", "6"))   # 경계에서 몇 겹을 풀어 줄지

bpy.ops.wm.open_mainfile(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
nf = len(me.polygons)
lab = np.empty(nf, np.int32)
me.attributes["part_id"].data.foreach_get("value", lab)
nor = np.empty(nf * 3); me.polygons.foreach_get("normal", nor); nor = nor.reshape(-1, 3)

t0 = time.time()
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
adj, cost = [[] for _ in range(nf)], [[] for _ in range(nf)]
for e in bm.edges:
    fs = e.link_faces
    if len(fs) != 2:
        continue
    a, b = fs[0].index, fs[1].index
    d = float(np.clip(np.dot(nor[a], nor[b]), -1, 1))
    w = 1.0 + CREASE_K * (1.0 - d) ** 0.5          # 평평하면 1, 접히면 비싸다
    adj[a].append(b); cost[a].append(w)
    adj[b].append(a); cost[b].append(w)
bm.free()
print(f"인접 그래프 {time.time()-t0:.0f}s")

# 1) 침식 — 경계에서 BAND 겹을 풀어 준다. 한 겹만 벗기면 Dijkstra 가 움직일
#    여유가 없어 경계가 그대로 남는다(실제로 16,450 -> 16,405 밖에 안 바뀌었다).
seed = lab.copy()
front = [i for i in range(nf) if any(lab[j] != lab[i] for j in adj[i])]
for _ in range(BAND):
    nxt = []
    for i in front:
        if seed[i]:
            seed[i] = 0
            nxt.extend(adj[i])
    front = [j for j in nxt if seed[j]]
print(f"씨앗 {int((seed>0).sum()):,} / {nf:,}  ({int((seed>0).sum())/nf*100:.0f}%)")

# 2) 비용 최소 확장
t0 = time.time()
INF = float('inf')
dist = np.full(nf, INF)
out = np.zeros(nf, np.int32)
h = []
for i in np.nonzero(seed)[0]:
    dist[i] = 0.0; out[i] = seed[i]
    heapq.heappush(h, (0.0, int(i)))
while h:
    d, i = heapq.heappop(h)
    if d > dist[i]:
        continue
    li = out[i]
    for j, w in zip(adj[i], cost[i]):
        nd = d + w
        if nd < dist[j]:
            dist[j] = nd; out[j] = li
            heapq.heappush(h, (nd, j))
print(f"확장 {time.time()-t0:.0f}s  미도달 {int((out==0).sum()):,}")
out[out == 0] = lab[out == 0]

me.attributes["part_id"].data.foreach_set("value", out.astype(np.int32))
me.update()
u, c = np.unique(out[out > 0], return_counts=True)
print(f"파츠 {len(u)}개, 400면 이상 {int((c>=400).sum())}개, 최대 {int(c.max()):,}면")
# 경계 길이 = 너덜거림 지표. 작을수록 능선에 붙었다
def bnd(L):
    return sum(1 for i in range(nf) for j in adj[i] if j > i and L[i] != L[j])
print(f"경계 에지  스냅 전 {bnd(lab):,}  ->  스냅 후 {bnd(out):,}")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
