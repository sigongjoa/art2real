"""**하나의 연속 표면으로 만든다.** 판을 독립 물체로 쪼개지 않는다.

    blender -b --python relief.py -- <art3d출력폴더> <출력.blend> [--scale 0.55] [--step 2]

왜 이렇게 바꾸나: 판 49개를 각각 물체로 만들고 각각 `guessed` 깊이로 밀면 서로
겹치고 파편이 된다 — 부품 IoU 0.892 가 전체 0.619 로 무너진 게 그것이다.
**연결된 한 장은 구조적으로 파편이 될 수 없다.**

분할은 여기서 물체를 나누는 게 아니라 두 가지를 준다:
    크리스 엣지   판 경계 = 접힘. Subsurf 를 걸어도 각이 살아남는다
    재질 ID       판의 톤(흰/금/청회/검정) 그대로

높이는 `depth.npy` (크리스 인플레이션) 에서 온다 — **지어낸 값이 아니라 잰 값이다.**
"""
import json
import os
import sys

import math

import bmesh
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
D, DST = argv[0], os.path.abspath(argv[1])
opt = dict(zip(argv[2::2], argv[3::2]))
SCALE = float(opt.get("--scale", 0.55))     # 높이장 -> 월드 배율 (앞뒤 두께)
STEP = int(opt.get("--step", 2))            # 격자 간격 (px)
BACK = float(opt.get("--back", 0.75))       # 뒤통수는 앞보다 얕다
RELIEF = float(opt.get("--relief", 1.0))    # 판 단차 배율 (0 이면 민 돔)

# **빈 씬에서 시작한다.** 기본 시작 씬의 큐브(2m)가 남으면 프레임을 통째로 덮어
# 과함 66.9% 로 나온다 — 메쉬 탓으로 오해하기 딱 좋다(실측).
bpy.ops.wm.read_factory_settings(use_empty=True)

spec = json.load(open(f"{D}/buildspec.json", encoding="utf-8"))
lab = np.load(f"{D}/labels.npy")
h = np.load(f"{D}/depth.npy")
f = spec["px_to_world"]
k, ytop, ztop = f["world_per_px"], f["y_top_px"], f["z_top"]
# **중심은 스펙이 쓴 값 그대로.** 이미지 bbox 로 다시 구하면 32px 어긋난다(실측).
cxg = f["center_x_px"]

# ── 실루엣 = 판의 합집합에서 **선 홈을 메운 것**. 물체가 차지하는 면이다.
#    (부품 GT 는 선을 뺀 판이지만, 표면은 선 자리에도 있다 — 거기가 홈이 된다)
# **`lab > 0` 은 투구가 아니다** — 위쪽 검은 띠까지 이미지 전체를 덮는다(실측 56.5%,
# x 0~511). 설계도가 유일한 진실이므로 **스펙이 남긴 부품의 영역만** 쓴다.
regs = {p["from"]["region"] for p in spec["parts"] if not p["ops"].get("skip")}
occ = np.isin(lab, list(regs))
print(f"부품 영역 {len(regs)}개 · 실루엣 {occ.mean():.1%}")
pad = np.zeros_like(occ)
for dy in range(-2, 3):
    for dx in range(-2, 3):
        pad |= np.roll(np.roll(occ, dy, 0), dx, 1)
sil = pad.copy()
for dy in range(-2, 3):
    for dx in range(-2, 3):
        sil &= np.roll(np.roll(pad, dy, 0), dx, 1)

H, W = sil.shape

# ── **높이 = 외형 돔 + 판별 작은 단차.**
# `depth.npy` 를 그대로 높이로 쓰면 판마다 절대 높이가 제각각이라 이웃 사이가
# 절벽이 되고, 격자가 그걸 수직 벽으로 이어 **가로 리본 더미**가 된다(실측:
# 정면 IoU 0.943 인데 30/60/90 도에서 형태가 없다).
# 전체 형태는 잰 외형(z별 반폭)이 주고, 분할은 그 위의 얕은 단차만 준다.
hw_rows = spec["envelope"]["halfwidth"]["rows"]
dp_rows = spec["envelope"]["depth"]["rows"]


def _at(rows, z, i):
    if z <= rows[0][0]:
        return rows[0][i]
    for a, b in zip(rows, rows[1:]):
        if z <= b[0]:
            u = (z - a[0]) / max(1e-9, b[0] - a[0])
            return a[i] + (b[i] - a[i]) * u
    return rows[-1][i]


def dome(x, z):
    rx = max(_at(hw_rows, z, 1), 1e-5)
    if dp_rows:
        y0, y1 = _at(dp_rows, z, 1), _at(dp_rows, z, 2)
        cy, ry = (y0 + y1) / 2, max((y1 - y0) / 2, 1e-5)
    else:
        cy, ry = 0.0, rx
    u = min(1.0, abs(x) / rx)
    return cy - ry * math.sqrt(max(0.0, 1 - u * u))


# 판별 돌출 (설계도의 값 — 손으로 적지 않는다)
prot = {}
for pp in spec["parts"]:
    v = pp["ops"]["protrusion"]
    if pp["ops"].get("make") == "recess":
        v = -abs(v) * 0.6
    prot[pp["from"]["region"]] = v * RELIEF
bm = bmesh.new()
idx = {}
for i in range(0, H, STEP):
    for j in range(0, W, STEP):
        if sil[i, j]:
            x = (j + 0.5 - cxg) * k
            z = ztop - (i + 0.5 - ytop) * k
            idx[(i, j)] = bm.verts.new((x, dome(x, z) - prot.get(int(lab[i, j]), 0.0), z))
bm.verts.index_update()

quads = []
for i in range(0, H - STEP, STEP):
    for j in range(0, W - STEP, STEP):
        c = [(i, j), (i, j + STEP), (i + STEP, j + STEP), (i + STEP, j)]
        if all(p in idx for p in c):
            try:
                quads.append((bm.faces.new([idx[p] for p in c]), i, j))
            except ValueError:
                pass
print(f"앞면 격자 정점 {len(idx)} · 면 {len(quads)}")

# ── 뒷면. **격자 색인으로 직접 꿰맨다.** Solidify 는 법선 방향으로 밀어서 옆으로도
#    부푼다(실측: 두께 0.026 = 창의 29%, 과함 66.9%). bridge_loops 는 눈·구멍마다
#    생긴 고리를 엉뚱하게 이어 붙인다. 색인이 있으니 옆면을 직접 만들면 된다.
bidx = {}
for (i, j), v in idx.items():
    bidx[(i, j)] = bm.verts.new((v.co.x, -v.co.y * BACK, v.co.z))
for i in range(0, H - STEP, STEP):
    for j in range(0, W - STEP, STEP):
        c = [(i, j), (i, j + STEP), (i + STEP, j + STEP), (i + STEP, j)]
        if all(p in bidx for p in c):
            try:
                bm.faces.new([bidx[p] for p in reversed(c)])
            except ValueError:
                pass
# 옆면: 앞면의 경계 엣지마다 뒷면의 같은 두 점과 사각형 하나
rev = {v: p for p, v in idx.items()}
nside = 0
for e in [e for e in bm.edges if len(e.link_faces) == 1 and e.verts[0] in rev
          and e.verts[1] in rev]:
    p0, p1 = rev[e.verts[0]], rev[e.verts[1]]
    try:
        bm.faces.new([idx[p0], idx[p1], bidx[p1], bidx[p0]])
        nside += 1
    except ValueError:
        pass
print(f"뒷면 + 옆면 {nside}개로 닫았다")

# ── 판 경계에 크리스. **여기가 분할이 하는 일이다** — 물체를 나누지 않는다
cl = bm.edges.layers.float.get('crease_edge') or bm.edges.layers.float.new('crease_edge')
lut = {fa: int(lab[i + STEP // 2, j + STEP // 2]) for fa, i, j in quads}
ncre = 0
for e in bm.edges:
    ls = [lut.get(fa) for fa in e.link_faces if fa in lut]
    if len(ls) == 2 and ls[0] != ls[1]:
        e[cl] = 1.0
        ncre += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

me = bpy.data.meshes.new("relief")
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new("relief", me)
bpy.context.scene.collection.objects.link(ob)
m = ob.modifiers.new("sub", 'SUBSURF')
m.levels = m.render_levels = 1
print(f"면 {len(me.polygons)} · 크리스 엣지 {ncre} · 연결 성분 1장")
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("SAVED", DST)
