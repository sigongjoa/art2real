# -*- coding: utf-8 -*-
"""파츠별로 갈라 UV 를 편다. 995,164면을 통째로 Smart UV 하면 섬이 수천 개 나온다.

    blender -b --python make_uv.py -- out/named2.blend out/uv.blend

파츠 경계가 곧 UV 시임이다 — 분할을 이름 있게 한 값이 여기서 돌아온다.
데시메이트를 먼저 하는 이유: 마칭큐브 512^3 메시는 면이 잘고 균일해서 언랩이
느리고 섬이 잘게 부서진다. 파츠를 나눈 뒤에 줄여야 시임을 안 넘는다.
"""
import json
import os
import sys
import time

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RATIO = float(os.environ.get("UV_RATIO", "0.10"))
MIN_FACES = 400

bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = src.data
nf = len(me.polygons)
lab = np.empty(nf, np.int32); me.attributes["part_id"].data.foreach_get("value", lab)
mi = np.empty(nf, np.int32); me.polygons.foreach_get("material_index", mi)
mats = [m.name for m in me.materials]
names = json.load(open(os.path.join(HERE, "named_parts.json")))

uniq, cnt = np.unique(lab, return_counts=True)
keep = [(int(u), int(c)) for u, c in zip(uniq, cnt) if c >= MIN_FACES]
print(f"파츠 {len(keep)}개 언랩 (데시메이트 {RATIO})")

coll = bpy.data.collections.new("uv")
bpy.context.scene.collection.children.link(coll)
made = []
t0 = time.time()
for pid, c in sorted(keep, key=lambda t: -t[1]):
    sel = np.nonzero(lab == pid)[0]
    cls = mats[int(np.bincount(mi[sel]).argmax())]
    nm = names[pid - 1] if 0 < pid <= len(names) else f"p{pid}"
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    ks = set(sel.tolist())
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context='FACES')
    nmesh = bpy.data.meshes.new(f"{nm}__{cls}")
    bm.to_mesh(nmesh); bm.free()
    if not len(nmesh.polygons):
        continue
    o = bpy.data.objects.new(nmesh.name, nmesh)
    o.data.materials.append(bpy.data.materials[cls])
    coll.objects.link(o)
    d = o.modifiers.new("dec", 'DECIMATE'); d.ratio = RATIO
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="dec")
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.012)
    bpy.ops.object.mode_set(mode='OBJECT')
    made.append(o.name)
bpy.data.objects.remove(src, do_unlink=True)
print(f"언랩 {time.time()-t0:.0f}s  오브젝트 {len(made)}개")

# --- UV 통계 + 레이아웃 좌표 덤프 ---
rows, dump = [], {}
for n in made:
    o = bpy.data.objects[n]
    m = o.data
    nl = len(m.loops)
    uv = np.empty(nl * 2); m.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    ls = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_total", lt)
    # UV 면적 / 3D 면적 = 채움률과 왜곡
    ar3 = np.empty(len(m.polygons)); m.polygons.foreach_get("area", ar3)
    a2 = np.zeros(len(m.polygons))
    for i in range(len(m.polygons)):
        p = uv[ls[i]:ls[i] + lt[i]]
        a2[i] = 0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1)) -
                          np.dot(p[:, 1], np.roll(p[:, 0], -1)))
    bm = bmesh.new(); bm.from_mesh(m)
    seams = sum(1 for e in bm.edges if len(e.link_faces) == 2 and
                any(l[bm.loops.layers.uv.active].uv != l.link_loop_radial_next.link_loop_next[
                    bm.loops.layers.uv.active].uv for l in e.link_loops)) if bm.loops.layers.uv.active else 0
    bm.free()
    scale = np.sqrt(np.divide(a2, ar3, out=np.zeros_like(a2), where=ar3 > 1e-12))
    ok = scale > 0
    rows.append((n, len(m.polygons), float(a2.sum()),
                 float(np.percentile(scale[ok], 95) / max(np.percentile(scale[ok], 5), 1e-9))))
    dump[n] = {"uv": uv.tolist(), "ls": ls.tolist(), "lt": lt.tolist()}
tot = sum(r[2] for r in rows)
print(f"{'파츠':22s} {'면':>7s} {'UV면적':>8s} {'왜곡 p95/p5':>10s}")
for n, f, a, d in sorted(rows, key=lambda r: -r[1])[:14]:
    print(f"{n:22s} {f:7,} {a:8.3f} {d:10.1f}")
print(f"합계 UV 면적 {tot:.2f} (오브젝트마다 0~1 정규화 -> 1.0 이 꽉 찬 것)")
json.dump(dump, open(os.path.join(HERE, "uv_dump.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
