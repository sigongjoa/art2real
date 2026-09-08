# -*- coding: utf-8 -*-
"""측면 깊이 강제 v2 — 계단 제거판.

    blender -b --python depth_fit2.py -- out/win_norm.blend out/depthfit2.blend

v1 이 표면에 가로 골판지 무늬를 만들었다. 원인이 둘이었다.
  (1) 원화 깊이 프로파일이 화소 단위로 튀어 행마다 배율이 계단처럼 바뀐다
      -> 평활 폭을 15 -> DF_SMOOTH(기본 80) 로. 2차차분 std 8.3 -> 0.76
  (2) **z 를 정수 행으로 양자화**해서 배율을 조회했다. 행 간격이 약 1.2mm 인데
      메시 삼각형이 2mm 급이라 인접 정점이 다른 행에 떨어져 단차가 난다
      -> np.interp 로 연속 조회.
(2) 가 (1) 보다 크다 — 평활을 아무리 해도 조회가 계단이면 계단이 남는다.
"""
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
SMOOTH = int(os.environ.get("DF_SMOOTH", "80"))
MAXS = 3.0
import json
FIT_SIDE = tuple(json.load(open(os.path.join(HERE, "fit.json")))["side"])
ax = np.arange(RES)
c = RES / 2


def warp(a, dx, dy, s):
    sx = np.clip(np.rint(s * (ax - c) + c + dx), 0, RES - 1).astype(int)
    sy = np.clip(np.rint(s * (ax - c) + c + dy), 0, RES - 1).astype(int)
    return a[np.ix_(sy, sx)]


A = warp(np.load(os.path.join(HERE, "true_side_clean.npy")), *FIT_SIDE)
bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nv = len(me.vertices)
co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)

sc = (U1 - U0) / (RES - 1)
a0 = np.full(RES, np.nan); a1 = np.full(RES, np.nan)
for r in range(RES):
    j = np.nonzero(A[r])[0]
    if len(j) > 1:
        a0[r], a1[r] = j.min() * sc + U0, j.max() * sc + U0
idx = np.nonzero(~np.isnan(a0))[0]
a0 = np.interp(ax, idx, a0[idx]); a1 = np.interp(ax, idx, a1[idx])

rows_i = np.clip(((Z1 - co[:, 2]) / (Z1 - Z0) * RES).astype(int), 0, RES - 1)
g0 = np.full(RES, np.nan); g1 = np.full(RES, np.nan)
order = np.argsort(rows_i)
rs = rows_i[order]; ys = co[order, 1]
b = np.searchsorted(rs, np.arange(RES + 1))
for r in range(RES):
    if b[r + 1] - b[r] >= 4:
        g0[r], g1[r] = ys[b[r]:b[r + 1]].min(), ys[b[r]:b[r + 1]].max()
idx = np.nonzero(~np.isnan(g0))[0]
g0 = np.interp(ax, idx, g0[idx]); g1 = np.interp(ax, idx, g1[idx])


def sm(v, k):
    ker = np.ones(k) / k
    return np.convolve(np.pad(v, (k, k), mode='edge'), ker, mode='same')[k:-k]


da = sm(a1 - a0, SMOOTH); ca = sm((a0 + a1) / 2, SMOOTH)
dg = sm(g1 - g0, SMOOTH); cg = sm((g0 + g1) / 2, SMOOTH)
scale = np.clip(np.where(dg > 1e-4, da / np.maximum(dg, 1e-4), 1.0), 1 / MAXS, MAXS)
d2 = np.diff(scale[int((Z1 - 1.0) / (Z1 - Z0) * RES):int((Z1 - 0.0) / (Z1 - Z0) * RES)], 2)
print(f"평활 {SMOOTH}  배율 [{scale.min():.3f},{scale.max():.3f}]  "
      f"2차차분 std {np.std(d2)*1000:.3f}e-3")

# **연속 조회** — 정수 행 인덱싱이 계단의 주범이다
rf = (Z1 - co[:, 2]) / (Z1 - Z0) * RES
s_v = np.interp(rf, ax, scale)
ca_v = np.interp(rf, ax, ca)
cg_v = np.interp(rf, ax, cg)
co[:, 1] = (co[:, 1] - cg_v) * s_v + ca_v
me.vertices.foreach_set("co", co.ravel())
me.update()
print(f"적용 후 y [{co[:,1].min():+.4f},{co[:,1].max():+.4f}]")

# 표면 평활. 계단(골판지)은 내 보정이 만든 게 아니라 **마칭큐브가 원래 갖고 있던** 것이다
# (FFT 최강 주기 2.08mm = 512^3 격자 간격, 보정 전후 동일). 깊이를 0.36배로 누르면
# 남은 깊이 대비 상대적으로 커져 보인다. 그래서 깊이 프로파일이 아니라 표면을 편다.
# IoU 대가는 거의 없다: 평활 0회 0.850 / 12회 0.848 / 20회 0.846
POST = int(os.environ.get("DF_POSTSMOOTH", "12"))
if POST:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    sm_ = o.modifiers.new("post", 'SMOOTH'); sm_.iterations = POST; sm_.factor = 0.5
    bpy.ops.object.modifier_apply(modifier="post")
    v2 = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", v2)
    v2 = v2.reshape(-1, 3)
    print(f"표면 평활 {POST}회 -> y [{v2[:,1].min():+.4f},{v2[:,1].max():+.4f}]")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
