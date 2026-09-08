# -*- coding: utf-8 -*-
"""**파츠별** 깊이 보정. 목표는 CAD 프록시의 y 범위.

    blender -b --python depth_part.py -- out/nd_named2.blend out/dp.blend

전신 일괄 깊이 압축(48번)은 버렸다 — 측면 IoU 하나만 오르고 부피가 27% 날아갔다(52번).
같은 높이에서 팔과 몸통을 한 배율로 눌러버리는 게 문제였다.

파츠마다 목표가 따로 있다: trail3 CAD 프록시는 아카이브 상수로 만든 것이라
파츠별 y 범위가 곧 원화가 의도한 깊이다. 그걸로 파츠마다 따로 맞춘다.
깊이 비가 이미 1.0 근처인 파츠(허리·어깨·발)는 건드리지 않는다.
"""
import glob
import json
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
PXD = os.path.join(HERE, "..", "trail3_freecad", "proxy")
DROP = {"c_cuirass", "c_helm"}
TOL = float(os.environ.get("DP_TOL", "1.25"))     # 이 비율 안이면 안 건드린다
MAXC = float(os.environ.get("DP_MAXC", "0.45"))   # 최대 압축 (너무 누르면 판때기가 된다)

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

# 정점 -> 파츠 (면 라벨을 정점으로 옮긴다. 경계 정점은 가장 많이 붙은 파츠)
vp = np.zeros((nv, 1), np.int32)
cnt = {}
for i in range(nf):
    for j in range(lt[i]):
        v = lv[ls[i] + j]
        cnt.setdefault(v, {}).setdefault(int(pid[i]), 0)
        cnt[v][int(pid[i])] += 1
vpart = np.array([max(cnt[v].items(), key=lambda kv: kv[1])[0] if v in cnt else 0
                  for v in range(nv)])

# 프록시 y 범위 (assign_named 와 같은 정렬: 높이로 배율, 접지선만)
cen = np.empty(nf * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
gl, gh = cen.min(0), cen.max(0)
PV = {}
allv = []
for p in sorted(glob.glob(os.path.join(PXD, "*.stl"))):
    nm = os.path.splitext(os.path.basename(p))[0]
    if nm in DROP:
        continue
    bpy.ops.wm.stl_import(filepath=p)
    ob = bpy.context.selected_objects[0]
    v = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3) * 0.001
    bpy.data.objects.remove(ob, do_unlink=True)
    if len(v) < 8:
        continue
    PV[nm] = v; allv.append(v)
pts = np.vstack(allv); lo, hi = pts.min(0), pts.max(0)
s = (gh[2] - gl[2]) / (hi[2] - lo[2])
zoff = gl[2] - lo[2] * s
print(f"프록시 정렬 배율 {s:.4f}")

print(f"{'파츠':18s} {'정점':>7s} {'메시 깊이':>9s} {'목표':>8s} {'비':>6s} {'적용':>8s}")
touched = 0
rows = []
for k, nm in enumerate(names):
    m = vpart == (k + 1)
    if m.sum() < 100 or nm not in PV:
        continue
    y = co[m, 1]
    dg = np.percentile(y, 99) - np.percentile(y, 1)
    py = PV[nm][:, 1] * s
    da = py.max() - py.min()
    if dg < 1e-4 or da < 1e-4:
        continue
    ratio = dg / da
    if ratio <= TOL:
        rows.append((nm, int(m.sum()), dg, da, ratio, 1.0)); continue
    f = max(1.0 / ratio, MAXC)
    cgy = (np.percentile(y, 99) + np.percentile(y, 1)) / 2
    cay = (py.max() + py.min()) / 2
    co[m, 1] = (y - cgy) * f + cay
    touched += int(m.sum())
    rows.append((nm, int(m.sum()), dg, da, ratio, f))
rows.sort(key=lambda r: -r[4])
for nm, n, dg, da, r, f in rows[:14]:
    print(f"{nm:18s} {n:7,} {dg:9.3f} {da:8.3f} {r:6.2f} {f:8.3f}"
          + ("" if f < 1.0 else "  (통과)"))
print(f"손댄 정점 {touched:,} / {nv:,} ({touched/nv*100:.1f}%)")
me.vertices.foreach_set("co", co.ravel())
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
