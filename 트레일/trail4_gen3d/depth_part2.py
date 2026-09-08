# -*- coding: utf-8 -*-
"""파츠별 깊이 압축 v2 — 목표를 **원화 측면 실루엣 자체**로.

    blender -b --python depth_part2.py -- out/nd_named2.blend out/dp2.blend

v1 은 목표를 CAD 프록시의 y 범위로 잡았다가 +0.03 밖에 못 얻었다.
프록시 자체가 원화보다 깊었기 때문이다(54번).

여기서는 파츠마다 y 압축률을 훑어서 **원화 측면 실루엣 밖으로 나가는 화소를
최소화**하는 값을 고른다. 목표가 원화니까 프록시의 오차가 안 섞인다.

측면 밖 화소 기여 실측(54번 뒤): 검 55% / 드래곤두상 41% / 투구 55% /
드래곤턱 42% / 늑대캐논 22% / 늑대두상 23% — 팔·검·투구가 절반이다.
몸통(정강이·허벅지·흉갑)은 14~21% 라 손대지 않는다.
"""
import json
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
MINF = float(os.environ.get("DP2_MIN", "0.40"))     # 최대 압축
MINOUT = float(os.environ.get("DP2_MINOUT", "0.20"))  # 밖 비율이 이 아래면 통과
c = RES / 2
axr = np.arange(RES)


def warp(a, dx, dy, s):
    sx = np.clip(np.rint(s * (axr - c) + c + dx), 0, RES - 1).astype(int)
    sy = np.clip(np.rint(s * (axr - c) + c + dy), 0, RES - 1).astype(int)
    return a[np.ix_(sy, sx)]


FIT = json.load(open(os.path.join(HERE, "fit.json")))
A = warp(np.load(os.path.join(HERE, "true_side_clean.npy")), *FIT["side"])

bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
names = json.load(open(os.path.join(HERE, "named_parts.json")))
nf = len(me.polygons)
pid = np.empty(nf, np.int32); me.attributes["part_id"].data.foreach_get("value", pid)
nv = len(me.vertices)
co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
tri = np.stack([lv[ls], lv[ls + 1], lv[ls + 2]], 1)

# 정점 -> 파츠 (면 라벨 다수결)
from collections import Counter
cnt = [Counter() for _ in range(nv)]
for i in range(nf):
    p = int(pid[i])
    for j in range(3):
        cnt[tri[i, j]][p] += 1
vpart = np.array([cnt[v].most_common(1)[0][0] if cnt[v] else 0 for v in range(nv)])
fac = np.ones(nv); ctr = co[:, 1].copy()
BLUR = int(os.environ.get("DP2_BLUR", "12"))

def _dilate(m, k=2):
    """블렌더 파이썬엔 cv2 가 없다. 이동+OR 로 팽창해 정점 사이 구멍을 메운다."""
    out = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def outside(vy, vz, vsel):
    """면 채우기 대신 **정점 래스터 + 팽창**. 정점이 50만 개라 충분하다."""
    px = np.clip(((vy[vsel] - U0) / (U1 - U0) * RES).astype(np.int32), 0, RES - 1)
    py = np.clip(((Z1 - vz[vsel]) / (Z1 - Z0) * RES).astype(np.int32), 0, RES - 1)
    m = np.zeros((RES, RES), bool)
    m[py, px] = True
    m = _dilate(m, 2)
    return int(m.sum()), int((m & ~A).sum())


print(f"{'파츠':20s} {'투영':>8s} {'밖(전)':>8s} {'%':>5s} {'배율':>6s} {'밖(후)':>8s} {'%':>5s}")
rows = []
touched = 0
for k, nm in enumerate(names):
    p = k + 1
    fm = pid == p
    if fm.sum() < 400:
        continue
    vm0 = vpart == p
    if vm0.sum() < 200:
        continue
    a0, o0 = outside(co[:, 1], co[:, 2], vm0)
    if a0 < 200 or o0 / a0 < MINOUT:
        rows.append((nm, a0, o0, 1.0, o0)); continue
    vm = vpart == p
    y = co[vm, 1]
    cy = (np.percentile(y, 99) + np.percentile(y, 1)) / 2
    best = (o0, 1.0)
    for f in np.arange(0.95, MINF - 0.001, -0.05):
        yy = co[:, 1].copy()
        yy[vm] = (y - cy) * f + cy
        _, oo = outside(yy, co[:, 2], vm)
        if oo < best[0]:
            best = (oo, float(f))
    if best[1] < 1.0:
        fac[vm] = best[1]; ctr[vm] = cy
        touched += int(vm.sum())
    rows.append((nm, a0, o0, best[1], best[0]))
rows.sort(key=lambda r: -(r[2] - r[4]))
for nm, a0, o0, f, o1 in rows[:14]:
    print(f"{nm:20s} {a0:8,} {o0:8,} {o0/max(a0,1)*100:5.0f} {f:6.2f} {o1:8,} "
          f"{o1/max(a0,1)*100:5.0f}")
# 파츠마다 따로 누르면 이음매가 찢어진다 (실제로 종횡비 p99.9 가 41.9 로 튀었다).
# 압축률과 중심을 정점 그래프 위에서 번지게 해서 경계를 부드럽게 잇는다.
if BLUR:
    nb = [[] for _ in range(nv)]
    for i in range(nf):
        a_, b_, c_ = tri[i]
        nb[a_] += [b_, c_]; nb[b_] += [a_, c_]; nb[c_] += [a_, b_]
    idxs = np.concatenate([np.array(x, np.int32) if x else np.zeros(0, np.int32) for x in nb])
    owner = np.concatenate([np.full(len(x), i, np.int32) for i, x in enumerate(nb)])
    deg = np.maximum(np.bincount(owner, minlength=nv), 1)
    for _ in range(BLUR):
        acc = np.bincount(owner, weights=fac[idxs], minlength=nv)
        fac = 0.5 * fac + 0.5 * acc / deg
        acc = np.bincount(owner, weights=ctr[idxs], minlength=nv)
        ctr = 0.5 * ctr + 0.5 * acc / deg
    print(f"압축률 번짐 {BLUR}회  fac [{fac.min():.3f},{fac.max():.3f}]")
co[:, 1] = (co[:, 1] - ctr) * fac + ctr
print(f"손댄 정점 {touched:,} / {nv:,} ({touched/nv*100:.1f}%)")
me.vertices.foreach_set("co", co.ravel())
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
