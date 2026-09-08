# -*- coding: utf-8 -*-
"""원화 재질맵(armor/dark/gold)을 생성 메시에 투영해 면마다 재질을 찍는다.

    blender -b --python project_mats.py -- out/win_norm.blend out/mats.blend

P3-SAM 이 못 쓰는 상황(Tencent 라이선스, 한국 제외)의 대체 분할이다.
면 법선이 가장 잘 향하는 판을 골라 그 판의 라벨을 읽는다. 판이 3개뿐이라
비스듬한 면은 오차가 크다 — 그래서 뒤에 다수결 평활을 한 번 건다.

정렬은 step3b 격자탐색 결과를 쓴다(판 -> 메시 공간 역변환).
"""
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
# step3b 실측: (dx, dy, scale) — 판이 메시보다 이만큼 이동/축소돼 있다
FIT = {"front": (8, 8, 0.94), "side": (8, 24, 0.94), "back": (40, 24, 0.94)}
COL = {1: (0.93, 0.93, 0.95, 1), 2: (0.10, 0.10, 0.12, 1), 3: (0.85, 0.70, 0.28, 1)}
NAME = {1: "armor", 2: "dark", 3: "gold"}


def load_map(k):
    q = np.load(os.path.join(HERE, f"win_{k}.npy"))
    dx, dy, s = FIT[k]
    # 판 -> 메시 공간: 이동 되돌리고 배율 되돌린다 (라벨맵이라 최근접)
    yy, xx = np.mgrid[0:RES, 0:RES]
    c = RES / 2
    sx = (xx - dx - c) / s + c
    sy = (yy - dy - c) / s + c
    sx = np.clip(np.rint(sx), 0, RES - 1).astype(int)
    sy = np.clip(np.rint(sy), 0, RES - 1).astype(int)
    return q[sy, sx]


bpy.ops.wm.open_mainfile(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
nf = len(me.polygons)
cen = np.empty(nf * 3); nor = np.empty(nf * 3)
me.polygons.foreach_get("center", cen)
me.polygons.foreach_get("normal", nor)
cen = cen.reshape(-1, 3); nor = nor.reshape(-1, 3)
print(f"면 {nf:,}")

M = {k: load_map(k) for k in ("front", "side", "back")}

# 어느 판이 이 면을 제일 정면으로 보는가
score = np.stack([-nor[:, 1], nor[:, 0], -nor[:, 0], nor[:, 1]], 1)   # front, +x, -x, back
pick = score.argmax(1)

U = np.where(pick == 0, cen[:, 0], np.where(pick == 3, -cen[:, 0], cen[:, 1]))
px = np.clip(((U - U0) / (U1 - U0) * RES).astype(int), 0, RES - 1)
py = np.clip(((Z1 - cen[:, 2]) / (Z1 - Z0) * RES).astype(int), 0, RES - 1)

lab = np.zeros(nf, np.uint8)
for i, k in ((0, "front"), (1, "side"), (2, "side"), (3, "back")):
    m = pick == i
    if i == 2:                                   # -x 면은 측면 판을 좌우 반전해 읽는다
        lab[m] = M[k][py[m], RES - 1 - px[m]]
    else:
        lab[m] = M[k][py[m], px[m]]

n0 = int((lab == 0).sum())
print(f"판이 배경으로 읽은 면 {n0:,} ({n0/nf*100:.1f}%) — 이웃 다수결로 메운다")

# 다수결 평활 + 배경 메우기: 면 인접 그래프 2회
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
adj = [[f.index for e in fa.edges for f in e.link_faces if f.index != fa.index]
       for fa in bm.faces]
bm.free()
for it in range(3):
    new = lab.copy()
    for i in range(nf):
        a = adj[i]
        if not a:
            continue
        cnt = np.bincount(lab[a], minlength=4)
        cnt[0] = 0                                # 배경은 후보에서 뺀다
        if cnt.max() > 0 and (lab[i] == 0 or cnt.argmax() != lab[i] and cnt.max() >= len(a) * 0.75):
            new[i] = cnt.argmax()
    ch = int((new != lab).sum()); lab = new
    print(f"  평활 {it+1}회 변경 {ch:,}")
lab[lab == 0] = 1

me.materials.clear()
slot = {}
for i, (v, n) in enumerate(sorted(NAME.items())):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = COL[v]
    m.diffuse_color = COL[v]
    me.materials.append(m)
    slot[v] = i
me.polygons.foreach_set("material_index", np.array([slot[v] for v in lab], np.int32))
me.update()
for v, n in NAME.items():
    c = int((lab == v).sum())
    print(f"{n:6s} {c:>8,} 면 ({c/nf*100:4.1f}%)")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
