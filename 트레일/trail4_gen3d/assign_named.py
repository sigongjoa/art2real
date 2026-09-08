# -*- coding: utf-8 -*-
"""생성 메시를 **아카이브 파츠 이름**으로 가른다.

    blender -b --python assign_named.py -- out/parts2.blend out/named.blend

앞의 두 실패:
  - 원화 재질맵 연결성분: 흰 갑주가 어깨를 통해 전신이 한 덩어리라 갑판이 안 갈린다.
    게다가 판별로 ID 를 따로 매겨서 같은 표면이 3조각 났다.
  - 이면각 능선: 임계값 스윕 결과 어떤 값도 안 된다 (6도면 조각 48,251개,
    22도면 하나로 99.7%). 마칭큐브 메시의 능선 그물이 닫혀 있지 않아 반드시 샌다.

파츠 목록은 발견할 게 아니라 **이미 있다.** trail3 의 CAD 빌더가 만든 61개
이름 붙은 프록시(proxy/*.stl)를 공간 사전으로 쓴다. 면 중심에서 가장 가까운
프록시의 이름을 받는다. 클래스(armor/dark/gold)는 원화 투영 결과를 파츠 단위
다수결로 굳힌다 — 어디서 갈라지나는 프록시가, 무엇인가는 원화가 정한다.
"""
import glob
import os
import sys
import time

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
PXD = os.path.join(HERE, "..", "trail3_freecad", "proxy")
DROP = {"c_cuirass", "c_helm"}          # armor2 판(a_)이 더 나중 버전이다
# 점 표본이 아니라 **면**을 BVH 에 넣는다. 표본으로 하면 STL 정점이 성긴 파츠
# (평평한 판)가 지고, 실제로 median 50mm / p95 147mm 로 어긋났다.

bpy.ops.wm.open_mainfile(filepath=SRC)
gen = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = gen.data
nf = len(me.polygons)
cen = np.empty(nf * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
mi = np.empty(nf, np.int32); me.polygons.foreach_get("material_index", mi)
mats = [m.name for m in me.materials]

# --- 프록시 적재: 정점+면을 그대로 BVH 에 ---
PV, PF, tag, names = [], [], [], []
base = 0
for p in sorted(glob.glob(os.path.join(PXD, "*.stl"))):
    nm = os.path.splitext(os.path.basename(p))[0]
    if nm in DROP:
        continue
    bpy.ops.wm.stl_import(filepath=p)
    o = bpy.context.selected_objects[0]
    v = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3) * 0.001                    # FreeCAD 는 mm
    tris = np.array([list(p.vertices) for p in o.data.polygons
                     if len(p.vertices) == 3], np.int32)
    bpy.data.objects.remove(o, do_unlink=True)
    if len(v) < 8 or not len(tris):
        continue
    k = len(names); names.append(nm)
    PV.append(v); PF.append(tris + base); tag.append(np.full(len(tris), k))
    base += len(v)
pts = np.vstack(PV); faces = np.vstack(PF); tag = np.concatenate(tag)
lo, hi = pts.min(0), pts.max(0)
print(f"프록시 {len(names)}개, 면 {len(faces):,}  bbox z {lo[2]:.3f}~{hi[2]:.3f}")

# --- 좌표계 맞춤: 생성 메시와 같은 규약(높이 1.0, 접지 0, x 중앙) ---
gl = cen.min(0); gh = cen.max(0)
s = (gh[2] - gl[2]) / (hi[2] - lo[2])
pts = pts * s
lo, hi = pts.min(0), pts.max(0)
# x,y 를 bbox 중심끼리 맞추면 안 된다. 두 좌표계는 이미 같은 규약으로 정규화돼
# 있고(x=0 중심선, y=0 허리, z=0 접지), CAD 쪽은 검·망토 때문에 bbox 가
# 비대칭이다(x[-0.348,+0.282] y[-0.378,+0.090]). 중심을 맞추면 전체가
# x+0.033, **y+0.145** 밀려 최근접 배정이 통째로 틀어진다.
# 접지선만 맞춘다.
pts[:, 2] += gl[2] - lo[2]
print(f"맞춤 배율 {s:.3f}  -> 프록시 z {pts[:,2].min():.3f}~{pts[:,2].max():.3f}"
      f"  생성 z {gl[2]:.3f}~{gh[2]:.3f}")

print(f"  faces dtype {faces.dtype} min {faces.min()} max {faces.max()} 정점 {len(pts)}")
assert faces.min() >= 0 and faces.max() < len(pts), "면 인덱스 범위 오류"
# numpy 정수를 그대로 넘기면 BVHTree 가 -1 로 읽는다. 파이썬 int 로 변환한다.
bvh = mathutils.bvhtree.BVHTree.FromPolygons(
    [mathutils.Vector(p) for p in pts.tolist()], faces.tolist(), all_triangles=True)

t0 = time.time()
lab = np.empty(nf, np.int32)
dist = np.empty(nf)
for i in range(nf):
    _, _, idx, d = bvh.find_nearest(mathutils.Vector(cen[i]))
    lab[i] = tag[idx] if idx is not None else 0
    dist[i] = d if d is not None else 0.0
print(f"최근접 배정 {time.time()-t0:.0f}s  거리 중앙 {np.median(dist)*1000:.1f}mm "
      f"p95 {np.percentile(dist,95)*1000:.1f}mm")

# --- 클래스는 **면 단위**로 유지한다 ---
# 파츠 단위 다수결로 굳혔더니 프록시 파츠가 커서 전 파츠가 armor 로 먹혔다
# (금색 발톱도, 검은 띠도). 합친 아틀라스의 재질이 ['armor'] 하나뿐이었다.
# 클래스는 원화 투영이 면마다 이미 정해 놓았으니 덮어쓰지 않는다.
KEEP_FACE_CLASS = os.environ.get("PART_MAJORITY") is None
newmi = mi.copy()
rows = []
for k, nm in enumerate(names):
    m = lab == k
    c = int(m.sum())
    if not c:
        continue
    v = int(np.bincount(mi[m], minlength=len(mats)).argmax())
    if not KEEP_FACE_CLASS:
        newmi[m] = v
    rows.append((nm, c, mats[v]))
me.polygons.foreach_set("material_index", newmi)
for i, n in enumerate(mats):
    print(f"  면 단위 클래스 {n:6s} {int((newmi==i).sum()):>8,} ({(newmi==i).mean()*100:4.1f}%)")
me.attributes["part_id"].data.foreach_set("value", (lab + 1).astype(np.int32))
me.update()
rows.sort(key=lambda r: -r[1])
print(f"배정된 파츠 {len(rows)}개")
for nm, c, cl in rows[:14]:
    print(f"  {nm:18s} {c:>8,}면  {cl}")
if len(rows) > 14:
    print(f"  ... 외 {len(rows)-14}개")
np.save(os.path.join(HERE, "named_labels.npy"), lab)
import json
json.dump(names, open(os.path.join(HERE, "named_parts.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
