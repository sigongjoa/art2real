# -*- coding: utf-8 -*-
"""part_id 로 메시를 실제 오브젝트로 가른다. 4단계(polish)가 파츠 단위로 손댈 수 있게.

    blender -b --python split_parts.py -- out/parts2.blend out/split.blend
"""
import os
import sys

import bpy
import bmesh
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
MIN_FACES = 400          # 이보다 작은 조각은 이웃에 흡수된 부스러기

bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = src.data
nf = len(me.polygons)
lab = np.empty(nf, np.int32); me.attributes["part_id"].data.foreach_get("value", lab)
mi = np.empty(nf, np.int32); me.polygons.foreach_get("material_index", mi)
mats = [m.name for m in me.materials]

uniq, cnt = np.unique(lab, return_counts=True)
keep = [(int(u), int(c)) for u, c in zip(uniq, cnt) if u > 0 and c >= MIN_FACES]
keep.sort(key=lambda t: -t[1])
print(f"파츠 {len(keep)}개 분리 ({MIN_FACES}면 미만은 버림)")

coll = bpy.data.collections.new("parts")
bpy.context.scene.collection.children.link(coll)
made = []
for pid, c in keep:
    sel = np.nonzero(lab == pid)[0]
    cls = mats[int(np.bincount(mi[sel]).argmax())]
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    keepset = set(sel.tolist())
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keepset], context='FACES')
    nm = bpy.data.meshes.new(f"p{pid:03d}_{cls}")
    bm.to_mesh(nm); bm.free()
    if not len(nm.polygons):
        continue
    o = bpy.data.objects.new(nm.name, nm)
    o.data.materials.append(bpy.data.materials[cls])
    coll.objects.link(o)
    made.append((o.name, len(nm.polygons)))
bpy.data.objects.remove(src, do_unlink=True)
print(f"분리 완료 {len(made)}개")
for n, f in made[:20]:
    print(f"  {n:24s} {f:>7,}면")
if len(made) > 20:
    print(f"  ... 외 {len(made)-20}개")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
