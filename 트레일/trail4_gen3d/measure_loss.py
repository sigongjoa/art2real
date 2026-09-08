# -*- coding: utf-8 -*-
"""두 가지 정보 손실을 각각 잰다.

    blender -b --python measure_loss.py -- out/uv3.blend out/named2.blend

(1) UV 손실 — 곡면을 평면으로 편 대가. 가우스 곡률이 0 이 아니면 등거리 전개가
    불가능하다(Theorema Egregium). 대가는 **왜곡**이나 **자름** 중 하나로 낸다.
    잰다: 파츠별 텍셀 밀도(2048^2 기준 mm/texel)와 그 편차.

(2) 원화 손실 — 3D 를 2D 로 투영한 대가. 이건 차원이 사라진 것이라 되돌릴 수 없다.
    잰다: 정면/측면/후면 세 판으로 표면의 몇 %나 실제로 볼 수 있나.
    그리고 시점을 N 개로 늘리면 몇 %까지 오르나.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
UVB, MESHB = os.path.abspath(argv[0]), os.path.abspath(argv[1])
ATLAS = 2048
FIG_MM = 2000.0          # 전신 1.0 을 2m 로 본다

# ---------- (1) UV 손실 ----------
bpy.ops.wm.open_mainfile(filepath=UVB)
rows = []
for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
    m = o.data
    if not m.uv_layers:
        continue
    n = len(m.polygons)
    uv = np.empty(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(n, np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(n, np.int32); m.polygons.foreach_get("loop_total", lt)
    a3 = np.empty(n); m.polygons.foreach_get("area", a3)
    a2 = np.array([0.5 * abs(np.dot(uv[s:s + t, 0], np.roll(uv[s:s + t, 1], -1)) -
                             np.dot(uv[s:s + t, 1], np.roll(uv[s:s + t, 0], -1)))
                   for s, t in zip(ls, lt)])
    ok = (a3 > 1e-12) & (a2 > 1e-14)
    # 텍셀당 실제 길이 = sqrt(3D면적/UV면적) / 아틀라스변 * 전신mm
    mm_per_texel = np.sqrt(a3[ok] / a2[ok]) / ATLAS * FIG_MM
    rows.append((o.name, n, float(a3.sum()), float(a2.sum()),
                 float(np.percentile(mm_per_texel, 5)),
                 float(np.median(mm_per_texel)),
                 float(np.percentile(mm_per_texel, 95))))
rows.sort(key=lambda r: -r[2])
print("(1) UV 손실 — 2048^2 아틀라스 기준 텍셀 하나가 덮는 실제 길이(mm)")
print(f"{'파츠':22s} {'3D면적':>8s} {'UV채움':>7s} {'p5':>6s} {'중앙':>6s} {'p95':>6s} {'p95/p5':>7s}")
for n, f, a3, a2, lo, md, hi in rows[:12]:
    print(f"{n:22s} {a3:8.4f} {a2:7.3f} {lo:6.2f} {md:6.2f} {hi:6.2f} {hi/max(lo,1e-9):7.2f}")
allmd = np.array([r[5] for r in rows])
print(f"  전체: 텍셀 크기 중앙 {np.median(allmd):.2f}mm, "
      f"파츠간 최소 {allmd.min():.2f} ~ 최대 {allmd.max():.2f}mm "
      f"(비 {allmd.max()/allmd.min():.1f}배)")
print(f"  UV 채움 합계 {sum(r[3] for r in rows):.1f} / {len(rows)}.0 "
      f"= {sum(r[3] for r in rows)/len(rows)*100:.0f}%")

# ---------- (2) 원화 손실 ----------
bpy.ops.wm.open_mainfile(filepath=MESHB)
ob = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = ob.data
nf = len(me.polygons)
cen = np.empty(nf * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
nor = np.empty(nf * 3); me.polygons.foreach_get("normal", nor); nor = nor.reshape(-1, 3)
rng = np.random.default_rng(0)
idx = rng.choice(nf, 40000, replace=False)          # 표본. 전수는 너무 느리다
a3 = np.empty(nf); me.polygons.foreach_get("area", a3)
w = a3[idx]

print()
print("(2) 원화 손실 — 시점 N 개로 표면의 몇 %(면적가중)를 실제로 볼 수 있나")
print(f"{'시점':>4s} {'각도':28s} {'가시면적':>8s} {'미관측':>8s}")


def coverage(dirs):
    seen = np.zeros(len(idx), bool)
    for d in dirs:
        dv = Vector(d)
        face = nor[idx] @ np.array(d) < -0.05          # 카메라를 향하는 면만
        cand = np.nonzero(face)[0]
        for k in cand:
            c = Vector(cen[idx[k]])
            hit, loc, _, _ = ob.ray_cast(c - dv * 4.0, dv)
            if hit and (loc - c).length <= 0.004:
                seen[k] = True
    return float(w[seen].sum() / w.sum())


def ring(n, elev=0.0):
    return [(math.sin(a) * math.cos(elev), -math.cos(a) * math.cos(elev), -math.sin(elev))
            for a in (2 * math.pi * i / n for i in range(n))]


for n, lab, dirs in (
        (3, "정면/측면/후면 (지금 쓰는 것)", [(0, 1, 0), (-1, 0, 0), (0, -1, 0)]),
        (4, "수평 4방", ring(4)),
        (6, "수평 6방", ring(6)),
        (8, "수평 8방", ring(8)),
        (12, "수평 12방", ring(12)),
        (14, "수평 12방 + 위/아래", ring(12) + [(0, 0, -1), (0, 0, 1)]),
        (26, "수평 12 + 위아래 12 + 상하", ring(12) + ring(12, 0.6) + [(0, 0, -1), (0, 0, 1)])):
    c = coverage(dirs)
    print(f"{n:4d} {lab:28s} {c*100:7.1f}% {(1-c)*100:7.1f}%")
