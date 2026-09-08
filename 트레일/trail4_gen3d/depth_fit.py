# -*- coding: utf-8 -*-
"""측면 판의 깊이를 메시에 **강제**한다. 폭은 건드리지 않는다.

    blender -b --python depth_fit.py -- out/win_norm.blend out/depthfit.blend

측면 원화가 있으니 깊이는 추측할 게 아니다. 높이 z 마다
    원화 y 구간 [a0,a1],  메시 y 구간 [g0,g1]
을 읽고 정점의 y 를 아핀으로 옮긴다:
    y' = (y - cg) * (da/dg) + ca
이러면 측면 실루엣이 **구성상** 일치한다. 폭(x)과 높이(z)는 그대로다.

한계: 같은 높이에서 x 에 따라 깊이가 다른 곳(팔은 앞, 몸통은 뒤)은
한 장의 측면 판으로 구분할 수 없다. 그래서 z 단위 아핀이 최선이다.
"""
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
import json as _json
FIT_SIDE = tuple(_json.load(open(os.path.join(HERE, "fit.json")))["side"])
# z 방향 평활 (행 단위). 15 로 했더니 표면에 **가로 골판지 무늬**가 생겼다 —
# 원화 깊이 프로파일이 화소 단위로 튀어서 행마다 배율이 계단처럼 바뀐 것이다.
# 2차차분 std: 평활1 110.5 / 15 8.3 / 40 1.6 / 80 0.76 / 150 0.34
SMOOTH = int(os.environ.get("DF_SMOOTH", "80"))
MAXS = 3.0           # 배율 상한 — 원화 span 이 끊긴 행에서 폭주 방지


def right(a, dx, dy, s):
    yy, xx = np.mgrid[0:RES, 0:RES]
    c = RES / 2
    return a[np.clip(np.rint(s * (yy - c) + c + dy), 0, RES - 1).astype(int),
             np.clip(np.rint(s * (xx - c) + c + dx), 0, RES - 1).astype(int)]


A = right(np.load(os.path.join(HERE, "true_side_clean.npy")), *FIT_SIDE)
import bpy_extras  # noqa
bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nv = len(me.vertices)
co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
print(f"정점 {nv:,}  y [{co[:,1].min():+.4f},{co[:,1].max():+.4f}]")

sc = (U1 - U0) / (RES - 1)
u_of = lambda px: (px / (RES - 1)) * (U1 - U0) + U0
z_of_row = lambda r: Z1 - (r / (RES - 1)) * (Z1 - Z0)

# --- 원화 깊이 프로파일 ---
a0 = np.full(RES, np.nan); a1 = np.full(RES, np.nan)
for r in range(RES):
    j = np.nonzero(A[r])[0]
    if len(j) > 1:
        a0[r], a1[r] = u_of(j.min()), u_of(j.max())
# 빈 행은 보간
idx = np.nonzero(~np.isnan(a0))[0]
a0 = np.interp(np.arange(RES), idx, a0[idx])
a1 = np.interp(np.arange(RES), idx, a1[idx])

# --- 메시 깊이 프로파일 (정점에서 직접) ---
rows = np.clip(((Z1 - co[:, 2]) / (Z1 - Z0) * RES).astype(int), 0, RES - 1)
g0 = np.full(RES, np.nan); g1 = np.full(RES, np.nan)
order = np.argsort(rows)
rs = rows[order]; ys = co[order, 1]
bounds = np.searchsorted(rs, np.arange(RES + 1))
for r in range(RES):
    s_, e_ = bounds[r], bounds[r + 1]
    if e_ - s_ >= 4:
        g0[r], g1[r] = ys[s_:e_].min(), ys[s_:e_].max()
idx = np.nonzero(~np.isnan(g0))[0]
g0 = np.interp(np.arange(RES), idx, g0[idx])
g1 = np.interp(np.arange(RES), idx, g1[idx])


def smooth(v, k):
    ker = np.ones(k) / k
    return np.convolve(np.pad(v, (k, k), mode='edge'), ker, mode='same')[k:-k]


da = smooth(a1 - a0, SMOOTH); ca = smooth((a0 + a1) / 2, SMOOTH)
dg = smooth(g1 - g0, SMOOTH); cg = smooth((g0 + g1) / 2, SMOOTH)
scale = np.clip(np.where(dg > 1e-4, da / np.maximum(dg, 1e-4), 1.0), 1.0 / MAXS, MAXS)
lo, hi = int((Z1 - 1.0) / (Z1 - Z0) * RES), int((Z1 - 0.0) / (Z1 - Z0) * RES)
print(f"깊이 배율: 중앙 {np.median(scale[lo:hi]):.3f}  "
      f"최소 {scale[lo:hi].min():.3f}  최대 {scale[lo:hi].max():.3f}")
for z in (0.06, 0.15, 0.25, 0.47, 0.57, 0.75, 0.92):
    r = int((Z1 - z) / (Z1 - Z0) * RES)
    print(f"   z {z:.2f}  메시 깊이 {dg[r]:.3f} -> 원화 {da[r]:.3f}  배율 {scale[r]:.3f}")

co[:, 1] = (co[:, 1] - cg[rows]) * scale[rows] + ca[rows]
me.vertices.foreach_set("co", co.ravel())
me.update()
print(f"적용 후 y [{co[:,1].min():+.4f},{co[:,1].max():+.4f}]")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
