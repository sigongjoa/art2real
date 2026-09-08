# -*- coding: utf-8 -*-
"""원화 재질맵의 **연결성분(파츠)** 을 가려짐 검사와 함께 메시에 투영한다.

    blender -b --python project_parts.py -- out/win_norm.blend out/parts.blend

앞 버전(project_mats.py)의 두 결함을 고친다:
  1) 가려짐을 안 봤다 — 팔 뒤 면이 몸을 뚫고 정면 판을 읽어 금색이 어깨에 튀었다.
     면 중심으로 광선을 쏘아 **첫 충돌이 그 면일 때만** 라벨을 받는다.
  2) 클래스 3개(armor/dark/gold)는 파츠가 아니다. 각 클래스의 2D 연결성분에
     ID 를 붙여 투영한다 — 발톱 3개, 무릎판, 정강이판이 각각 따로 나온다.
"""
import os
import sys
import time

import bpy
import bmesh
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
FIT = {"front": (8, 8, 0.94), "side": (8, 24, 0.94), "back": (40, 24, 0.94)}
MIN_BLOB = 260          # 이보다 작은 성분은 먹선 부스러기다
NAME = {1: "armor", 2: "dark", 3: "gold"}
COL = {1: (0.93, 0.93, 0.95, 1), 2: (0.10, 0.10, 0.12, 1), 3: (0.85, 0.70, 0.28, 1)}


def load_map(k):
    """build_partmaps.py 가 만든 파츠맵. 블렌더엔 cv2 가 없어 밖에서 만든다."""
    pid = np.load(os.path.join(HERE, f"pid_{k}.npy"))
    q = np.load(os.path.join(HERE, f"cls_{k}.npy"))
    return q, pid, {}


bpy.ops.wm.open_mainfile(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
nf = len(me.polygons)
cen = np.empty(nf * 3); nor = np.empty(nf * 3)
me.polygons.foreach_get("center", cen)
me.polygons.foreach_get("normal", nor)
cen = cen.reshape(-1, 3); nor = nor.reshape(-1, 3)

VIEWS = [("front", np.array([0., 1., 0.])), ("sidep", np.array([-1., 0., 0.])),
         ("siden", np.array([1., 0., 0.])), ("back", np.array([0., -1., 0.]))]
MAPKEY = {"front": "front", "sidep": "side", "siden": "side", "back": "back"}
MAPS = {k: load_map(k) for k in ("front", "side", "back")}
for k in MAPS:
    print(f"{k}: 파츠맵 최대ID {int(MAPS[k][1].max())}")

# 면 -> 판 우선순위 (법선이 카메라를 향하는 정도)
score = np.stack([-nor[:, 1], nor[:, 0], -nor[:, 0], nor[:, 1]], 1)
order = np.argsort(-score, 1)

t0 = time.time()
lab = np.zeros(nf, np.int32)
cls = np.zeros(nf, np.uint8)
hit_stat = [0, 0, 0, 0, 0]
for i in range(nf):
    c = Vector(cen[i])
    for slot in range(2):                       # 1·2순위 판만 본다
        v = order[i, slot]
        if score[i, v] <= 0.05:
            break
        name, d = VIEWS[v]
        dirv = Vector(d)
        org = c - dirv * 4.0
        ok, loc, _, fidx = ob.ray_cast(org, dirv)
        if not ok or (loc - c).length > 0.004:  # 앞에 다른 면이 있다 = 가려짐
            continue
        key = MAPKEY[name]
        q, pid, _ = MAPS[key]
        u = c.x if name == "front" else (-c.x if name == "back" else c.y)
        px = int(np.clip((u - U0) / (U1 - U0) * RES, 0, RES - 1))
        py = int(np.clip((Z1 - c.z) / (Z1 - Z0) * RES, 0, RES - 1))
        if name == "siden":
            px = RES - 1 - px
        p = pid[py, px]
        if p:
            lab[i] = p if key == "front" else p + (10000 if key == "side" else 20000)
            cls[i] = q[py, px]
            hit_stat[v] += 1
            break
    else:
        hit_stat[4] += 1
print(f"광선검사 {time.time()-t0:.0f}s  front {hit_stat[0]:,} +x {hit_stat[1]:,} "
      f"-x {hit_stat[2]:,} back {hit_stat[3]:,}  못읽음 {int((lab==0).sum()):,}")

bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
adj = [[f.index for e in fa.edges for f in e.link_faces if f.index != fa.index]
       for fa in bm.faces]
bm.free()
for it in range(6):
    new = lab.copy(); newc = cls.copy()
    idx = np.nonzero(lab == 0)[0]
    for i in idx:
        a = [j for j in adj[i] if lab[j]]
        if not a:
            continue
        vals, cnt = np.unique(lab[a], return_counts=True)
        w = vals[cnt.argmax()]
        new[i] = w; newc[i] = cls[a[np.argmax(lab[a] == w)]]
    ch = int((new != lab).sum()); lab, cls = new, newc
    print(f"  확산 {it+1}회 {ch:,} 채움, 남은 공백 {int((lab==0).sum()):,}")
    if ch == 0:
        break
cls[cls == 0] = 1

me.materials.clear()
slot = {}
for v in (1, 2, 3):
    m = bpy.data.materials.new(NAME[v])
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = COL[v]
    m.diffuse_color = COL[v]
    me.materials.append(m); slot[v] = len(me.materials) - 1
me.polygons.foreach_set("material_index",
                        np.array([slot[int(v)] for v in cls], np.int32))
at = me.attributes.new("part_id", 'INT', 'FACE')
at.data.foreach_set("value", lab.astype(np.int32))
me.update()

uniq, cnt = np.unique(lab[lab > 0], return_counts=True)
big = [(int(u), int(c)) for u, c in zip(uniq, cnt) if c >= 400]
print(f"파츠 {len(uniq)}개 (400면 이상 {len(big)}개)")
for v in (1, 2, 3):
    n = int((cls == v).sum())
    print(f"{NAME[v]:6s} {n:>8,} 면 ({n/nf*100:4.1f}%)")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
