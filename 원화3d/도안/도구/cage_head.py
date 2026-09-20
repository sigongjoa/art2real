"""**저폴리 케이지 + 섭디비전.** 영상에서 사람이 실제로 하는 공정.

    blender -b --python cage_head.py -- <art3d출력폴더> <출력.blend> [--n 12] [--sub 2]

릴리프(relief.py)와 대비하는 쪽이다. 차이는 하나:

    relief   격자 한 장에 판 단차를 **구워 넣는다**       (정면이 구조적으로 맞다)
    cage     매끈한 저폴리 형태 + 디테일은 **얹는 물체**  (형태가 먼저, 디테일은 나중)

케이지 링은 **형태가 꺾이는 z 에만** 놓는다 — 균일 격자는 엣지 루프를 놓을 자리가
없어서 판 구분이 안 생긴다(LESSON: cage_vs_sweep). 어디가 꺾이는지는 잰 외형의
반폭 곡률에서 고른다. 사람이 눈으로 고르지 않는다.

읽는 건 `buildspec.json` 뿐이다.
"""
import json
import math
import os
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
D, DST = argv[0], os.path.abspath(argv[1])
opt = dict(zip(argv[2::2], argv[3::2]))
N = int(opt.get("--n", 12))              # 링 점 수
SUB = int(opt.get("--sub", 2))
KEEP = int(opt.get("--rings", 9))        # 케이지 링 수 (저폴리)

bpy.ops.wm.read_factory_settings(use_empty=True)
spec = json.load(open(f"{D}/buildspec.json", encoding="utf-8"))
hw = spec["envelope"]["halfwidth"]["rows"]
dp = spec["envelope"]["depth"]["rows"]


def _at(rows, z, i):
    if z <= rows[0][0]:
        return rows[0][i]
    for a, b in zip(rows, rows[1:]):
        if z <= b[0]:
            u = (z - a[0]) / max(1e-9, b[0] - a[0])
            return a[i] + (b[i] - a[i]) * u
    return rows[-1][i]


def yr(z):
    if dp:
        y0, y1 = _at(dp, z, 1), _at(dp, z, 2)
        return (y0 + y1) / 2, max((y1 - y0) / 2, 1e-5)
    return 0.0, max(_at(hw, z, 1), 1e-5)


# ── 링을 놓을 z: **반폭의 2차 차분이 큰 곳** = 형태가 꺾이는 곳
zs = [r[0] for r in hw]
w = [r[1] for r in hw]
curv = [0.0] * len(zs)
for i in range(1, len(zs) - 1):
    curv[i] = abs(w[i - 1] - 2 * w[i] + w[i + 1])
order = sorted(range(1, len(zs) - 1), key=lambda i: -curv[i])
pick = sorted({0, len(zs) - 1} | set(order[:max(0, KEEP - 2)]))
print(f"외형 행 {len(zs)}개 중 **꺾이는 {len(pick)}개**에만 링을 놓는다 "
      f"(z {', '.join(f'{zs[i]:.3f}' for i in pick)})")

bm = bmesh.new()
rings = []
for i in pick:
    z = zs[i]
    rx = max(w[i], 1e-5)
    cy, ry = yr(z)
    row = []
    for t in range(N):
        a = 2 * math.pi * t / N
        row.append(bm.verts.new((rx * math.cos(a), cy + ry * math.sin(a), z)))
    rings.append(row)
for r0, r1 in zip(rings, rings[1:]):
    for t in range(N):
        u = (t + 1) % N
        bm.faces.new((r0[t], r0[u], r1[u], r1[t]))
# 위아래 캡 — 부채꼴 대신 중심점 하나로 (Subsurf 가 둥글린다)
for row, z, up in ((rings[0], zs[pick[0]], -1), (rings[-1], zs[pick[-1]], 1)):
    cy, ry = yr(z)
    c = bm.verts.new((0.0, cy, z + up * ry * 0.25))
    for t in range(N):
        u = (t + 1) % N
        bm.faces.new((row[t], row[u], c) if up > 0 else (row[u], row[t], c))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("head_cage")
bm.to_mesh(me); bm.free()
cage = bpy.data.objects.new("head_cage", me)
bpy.context.scene.collection.objects.link(cage)
s = cage.modifiers.new("sub", 'SUBSURF')
s.levels = s.render_levels = SUB
for p in me.polygons:
    p.use_smooth = True
print(f"케이지 면 {len(me.polygons)} (Subsurf {SUB} 전)")


def surf(x, z):
    rx = max(_at(hw, z, 1), 1e-5)
    cy, ry = yr(z)
    u = min(1.0, abs(x) / rx)
    return cy - ry * math.sqrt(max(0.0, 1 - u * u))


def poly_dist(poly, x, z):
    best = 1e9
    for kk in range(len(poly)):
        ax, az = poly[kk]; bx, bz = poly[(kk + 1) % len(poly)]
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / L2))
        best = min(best, math.hypot(x - (ax + t * dx), z - (az + t * dz)))
    return best


# ── 디테일: **본체에 파넣지 않고 얹는 물체로.** 지우고 다시 얹기가 자유롭다
ndet = 0
for p in spec["parts"]:
    if p["ops"].get("skip") or not p.get("poly"):
        continue
    prot = p["ops"]["protrusion"]
    if p["ops"].get("make") == "recess":
        prot = -abs(prot) * 0.6
    for gi, poly in enumerate(p["poly"]):
        if len(poly) < 3:
            continue
        b = bmesh.new()
        try:
            vs = [b.verts.new((x, 0.0, z)) for x, z in poly]
            b.faces.new(vs)
        except ValueError:
            b.free(); continue
        bmesh.ops.triangulate(b, faces=b.faces[:])
        bmesh.ops.join_triangles(b, faces=b.faces[:], angle_face_threshold=3.14,
                                 angle_shape_threshold=3.14)
        bmesh.ops.subdivide_edges(b, edges=b.edges[:], cuts=2, use_grid_fill=True)
        for v in b.verts:
            v.co.y = surf(v.co.x, v.co.z) - prot * min(
                1.0, poly_dist(poly, v.co.x, v.co.z) / 0.004)
        bmesh.ops.solidify(b, geom=b.faces[:] + b.edges[:] + b.verts[:],
                           thickness=0.0015)
        bmesh.ops.recalc_face_normals(b, faces=b.faces[:])
        dm = bpy.data.meshes.new(f"{p['id']}_{gi}_Details")
        b.to_mesh(dm); b.free()
        do = bpy.data.objects.new(dm.name, dm)
        bpy.context.scene.collection.objects.link(do)
        do.parent = cage
        ndet += 1
print(f"_Details 물체 {ndet}개를 얹었다 (본체에 파넣지 않는다)")
bpy.ops.wm.save_as_mainfile(filepath=DST)
print("SAVED", DST)
