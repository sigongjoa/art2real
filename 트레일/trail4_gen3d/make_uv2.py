# -*- coding: utf-8 -*-
"""파츠마다 언랩 방식을 **재서** 고른다. 하나로 고정하지 않는다.

    blender -b --python make_uv2.py -- out/named2.blend out/uv2.blend

sweep_uv2 실측:
    r_wolf_cannon  smart66 423섬/왜곡1.2   시임55 25섬/왜곡856   <- 시임은 못 쓴다
    c_shin         smart66   4섬/왜곡1.2   시임40  1섬/왜곡1.2   <- 시임이 낫다
    a_cuirass      smart66 100섬/왜곡1.1   smooth+smart89 4섬/1.9
복잡한 파츠는 시임을 적게 주면 펴지지 않아 왜곡이 터지고, 단순한 통 모양은
시임 하나로 깨끗이 펴진다. 그래서 후보를 다 돌려 보고
**왜곡 <= MAXD 중 섬이 가장 적은 것**을 고른다.
"""
import json
import math
import os
import sys
import time

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
RATIO, MIN_FACES, MAXD = 0.10, 400, 2.0
# 평활은 **분할 전에 전체 메시에** 한 번만 건다. 파츠별로 따로 걸면 각자
# 안쪽으로 수축해 파츠 사이에 틈이 벌어진다 (실제로 체커 렌더에 흰 틈이 났다).
PRESMOOTH = int(os.environ.get("UV_PRESMOOTH", "10"))
CAND = [("smart89", "smart", 89),
        ("sharp40", "unwrap", 40),
        ("sharp55", "unwrap", 55),
        ("smart66", "smart", 66)]


def islands(me):
    bm = bmesh.new(); bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    seen, n = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        n += 1; st = [f]; seen.add(f.index)
        while st:
            c = st.pop()
            for l in c.loops:
                lr = l.link_loop_radial_next; g = lr.face
                if g.index in seen:
                    continue
                if (l[uvl].uv - lr.link_loop_next[uvl].uv).length < 1e-5 and \
                   (l.link_loop_next[uvl].uv - lr[uvl].uv).length < 1e-5:
                    seen.add(g.index); st.append(g)
    bm.free(); return n


def stretch_fill(o):
    m = o.data
    uv = np.empty(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_total", lt)
    a3 = np.empty(len(m.polygons)); m.polygons.foreach_get("area", a3)
    a2 = np.array([0.5 * abs(np.dot(uv[s:s + t, 0], np.roll(uv[s:s + t, 1], -1)) -
                             np.dot(uv[s:s + t, 1], np.roll(uv[s:s + t, 0], -1)))
                   for s, t in zip(ls, lt)])
    sc = np.sqrt(np.divide(a2, a3, out=np.zeros_like(a2), where=a3 > 1e-12))
    sc = sc[sc > 0]
    d = float(np.percentile(sc, 95) / max(np.percentile(sc, 5), 1e-9)) if len(sc) else 1e9
    return d, float(a2.sum())


def do_uv(o, mode, ang):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if mode == "smart":
        bpy.ops.uv.smart_project(angle_limit=math.radians(ang), island_margin=0.012)
    else:
        bpy.ops.mesh.mark_seam(clear=True)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.edges_select_sharp(sharpness=math.radians(ang))
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.012)
        bpy.ops.uv.pack_islands(margin=0.012)
    bpy.ops.object.mode_set(mode='OBJECT')


bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
if PRESMOOTH:
    bpy.context.view_layer.objects.active = src
    sm = src.modifiers.new("s", 'SMOOTH'); sm.iterations = PRESMOOTH; sm.factor = 0.7
    bpy.ops.object.modifier_apply(modifier="s")
    print(f"전체 평활 {PRESMOOTH}회 (분할 전)")
me = src.data
nf = len(me.polygons)
lab = np.empty(nf, np.int32); me.attributes["part_id"].data.foreach_get("value", lab)
mi = np.empty(nf, np.int32); me.polygons.foreach_get("material_index", mi)
mats = [m.name for m in me.materials]
names = json.load(open(os.path.join(HERE, "named_parts.json")))
uniq, cnt = np.unique(lab, return_counts=True)
keep = [(int(u), int(c)) for u, c in zip(uniq, cnt) if c >= MIN_FACES]

coll = bpy.data.collections.new("uv")
bpy.context.scene.collection.children.link(coll)
t0 = time.time()
rows, dump = [], {}
for pid, c in sorted(keep, key=lambda t: -t[1]):
    sel = np.nonzero(lab == pid)[0]
    cls = mats[int(np.bincount(mi[sel]).argmax())]
    nm = names[pid - 1] if 0 < pid <= len(names) else f"p{pid}"
    best = None
    for tag, mode, ang in CAND:
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        ks = set(sel.tolist())
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context='FACES')
        m2 = bpy.data.meshes.new("t"); bm.to_mesh(m2); bm.free()
        o = bpy.data.objects.new("t", m2); coll.objects.link(o)
        d = o.modifiers.new("d", 'DECIMATE'); d.ratio = RATIO
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="d")
        do_uv(o, mode, ang)
        dist, area = stretch_fill(o)
        isl = islands(o.data)
        score = (isl if dist <= MAXD else 10 ** 6 + isl)
        if best is None or score < best[0]:
            if best is not None:
                bpy.data.objects.remove(best[1], do_unlink=True)
            best = (score, o, tag, isl, dist, area)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    _, o, tag, isl, dist, area = best
    o.name = f"{nm}__{cls}"; o.data.name = o.name
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials[cls])
    rows.append((o.name, len(o.data.polygons), isl, dist, area, tag))
    m = o.data
    uv = np.empty(len(m.loops) * 2); m.uv_layers[0].data.foreach_get("uv", uv)
    ls = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_total", lt)
    dump[o.name] = {"uv": uv.reshape(-1, 2).tolist(), "ls": ls.tolist(), "lt": lt.tolist()}
bpy.data.objects.remove(src, do_unlink=True)
print(f"언랩 {time.time()-t0:.0f}s")
print(f"{'파츠':22s} {'면':>6s} {'섬':>5s} {'왜곡':>5s} {'채택':>18s}")
for n, f, i, d, a, tg in sorted(rows, key=lambda r: -r[2])[:12]:
    print(f"{n:22s} {f:6,} {i:5,} {d:5.1f} {tg:>18s}")
print(f"섬 합계 {sum(r[2] for r in rows):,}  (앞 버전 3,255)")
from collections import Counter
print("채택 분포:", dict(Counter(r[5] for r in rows)))
json.dump(dump, open(os.path.join(HERE, "uv_dump.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
