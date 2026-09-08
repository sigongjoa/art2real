# -*- coding: utf-8 -*-
"""파츠 경계는 **메시의 능선**이 정하고, 파츠의 정체는 원화가 정한다.

    blender -b --python segment_creases.py -- out/parts2.blend out/seg.blend [임계값]

앞 버전의 설계 오류: 파츠 ID 를 판(front/side/back)별로 따로 매겼다. 그래서 같은
갑주 표면이 어느 카메라가 봤느냐에 따라 3조각이 났다(111,868 / 82,238 / 70,642 면이
전부 같은 표면). 게다가 원화의 흰 갑주는 어깨를 통해 전신이 한 덩어리라 애초에
클래스 연결성분으로는 갑판이 안 갈린다.

그래서 뒤집는다.
    어디서 갈라지나 -> 이면각(능선). 3D 가 아는 것.
    무엇인가       -> 원화 재질 클래스. 2D 만 아는 것.

이면각은 **평활한 법선**으로 잰다. 마칭큐브 512^3 격자의 계단 잡음이 그대로
능선으로 잡히면 조각이 수만 개로 부서진다.
"""
import os
import sys
from collections import defaultdict

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
THRESH = float(argv[2]) if len(argv) > 2 else None
SMOOTH = 4            # 법선 평활 횟수
MIN_FACES = 800       # 이보다 작은 조각은 이웃에 합친다

bpy.ops.wm.open_mainfile(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
nf = len(me.polygons)
nor = np.empty(nf * 3); me.polygons.foreach_get("normal", nor); nor = nor.reshape(-1, 3)
mi = np.empty(nf, np.int32); me.polygons.foreach_get("material_index", mi)
mats = [m.name for m in me.materials]

bm = bmesh.new(); bm.from_mesh(me)
pairs = np.array([[e.link_faces[0].index, e.link_faces[1].index]
                  for e in bm.edges if len(e.link_faces) == 2], np.int32)
bm.free()
A, B = pairs[:, 0], pairs[:, 1]
print(f"면 {nf:,}  내부 에지 {len(pairs):,}")

# --- 법선 평활: 이웃 평균. 계단 잡음을 죽이고 진짜 갑판 모서리는 남긴다 ---
sm = nor.copy()
deg = np.bincount(np.concatenate([A, B]), minlength=nf).astype(float)[:, None]
for _ in range(SMOOTH):
    acc = np.zeros_like(sm)
    np.add.at(acc, A, sm[B]); np.add.at(acc, B, sm[A])
    sm = sm + acc / np.maximum(deg, 1)
    sm /= np.linalg.norm(sm, axis=1, keepdims=True)
ang = np.degrees(np.arccos(np.clip((sm[A] * sm[B]).sum(1), -1, 1)))
print("평활 후 이면각:", {f"p{p}": round(float(np.percentile(ang, p)), 1)
                       for p in (90, 95, 98, 99, 99.5, 99.9)})


def regions(t):
    """능선을 안 넘는 면끼리 묶는다 (union-find)."""
    par = np.arange(nf)

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    keep = ang <= t
    for a, b in zip(A[keep], B[keep]):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    lab = np.array([find(i) for i in range(nf)])
    _, lab = np.unique(lab, return_inverse=True)
    return lab


if THRESH is None:
    print(f"\n{'임계':>5s} {'조각':>7s} {'800면+':>7s} {'최대':>9s} {'최대비율':>8s}")
    for t in (6, 8, 10, 12, 15, 18, 22, 28):
        lab = regions(t)
        c = np.bincount(lab)
        print(f"{t:5.0f} {len(c):7,} {int((c>=MIN_FACES).sum()):7,} "
              f"{int(c.max()):9,} {c.max()/nf*100:7.1f}%")
    print("\n임계값을 골라 다시 부를 것: ... -- <src> <out> <임계값>")
    raise SystemExit

lab = regions(THRESH)
cnt = np.bincount(lab)
print(f"임계 {THRESH}도 -> 조각 {len(cnt):,}개, 최대 {int(cnt.max()):,}면")

# --- 작은 조각은 접촉면이 가장 넓은 이웃에 흡수 ---
for _ in range(8):
    small = np.nonzero(cnt < MIN_FACES)[0]
    if not len(small):
        break
    smallset = set(small.tolist())
    touch = defaultdict(lambda: defaultdict(int))
    for a, b in zip(A, B):
        la, lb = lab[a], lab[b]
        if la == lb:
            continue
        if la in smallset: touch[la][lb] += 1
        if lb in smallset: touch[lb][la] += 1
    moved = 0
    for s in small:
        if not touch[s]:
            continue
        best = max(touch[s].items(), key=lambda kv: kv[1])[0]
        lab[lab == s] = best; moved += 1
    if not moved:
        break
    _, lab = np.unique(lab, return_inverse=True)
    cnt = np.bincount(lab)
print(f"흡수 후 조각 {len(cnt):,}개  중앙 {int(np.median(cnt)):,}면  최대 {int(cnt.max()):,}면")

# --- 정체는 원화가 정한다: 조각마다 재질 클래스 다수결 ---
newmi = np.zeros(nf, np.int32)
tally = {}
for r in range(len(cnt)):
    m = lab == r
    v = int(np.bincount(mi[m], minlength=len(mats)).argmax())
    newmi[m] = v
    tally[r] = (v, int(m.sum()))
me.polygons.foreach_set("material_index", newmi)
me.attributes["part_id"].data.foreach_set("value", (lab + 1).astype(np.int32))
me.update()
for i, n in enumerate(mats):
    k = sum(1 for v, _ in tally.values() if v == i)
    f = int((newmi == i).sum())
    print(f"{n:6s} 조각 {k:3d}개  {f:>8,}면 ({f/nf*100:4.1f}%)")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
