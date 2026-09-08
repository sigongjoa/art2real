# -*- coding: utf-8 -*-
"""QuadriFlow 리토폴로지가 UV 파편화를 고치는지 3개 파츠로 검증.

    blender -b --python test_quad.py -- out/uv.blend out/quadtest.blend

마칭큐브 삼각형 수프에 Smart UV 를 걸면 계단 잡음마다 시임이 생겨 섬이
수백 개로 부서진다(r_wolf_cannon 417개, 면/섬 29.9). 쿼드로 다시 짜면
사라지는지 본다. ep01 교훈과도 맞는다 — 촘촘한 스윕 메시엔 엣지루프를
넣을 자리가 없다.
"""
import os
import sys
import time

import bpy
import bmesh

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
TARGETS = {"r_wolf_cannon__armor": 4000, "c_foot__armor": 2500, "c_shin__armor": 2000}


def islands(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    uvl = bm.loops.layers.uv.active
    if uvl is None:
        bm.free(); return -1
    bm.faces.ensure_lookup_table()
    seen, n = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        n += 1; st = [f]; seen.add(f.index)
        while st:
            c = st.pop()
            for l in c.loops:
                lr = l.link_loop_radial_next
                g = lr.face
                if g.index in seen:
                    continue
                if (l[uvl].uv - lr.link_loop_next[uvl].uv).length < 1e-5 and \
                   (l.link_loop_next[uvl].uv - lr[uvl].uv).length < 1e-5:
                    seen.add(g.index); st.append(g)
    bm.free(); return n


bpy.ops.wm.open_mainfile(filepath=SRC)
print(f"{'파츠':22s} {'전 면':>7s} {'전 섬':>6s} {'후 면':>7s} {'후 섬':>6s} {'면/섬':>7s} {'초':>5s}")
for name, tgt in TARGETS.items():
    o = bpy.data.objects.get(name)
    if not o:
        print(f"{name}: 없음"); continue
    f0, i0 = len(o.data.polygons), islands(o)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o
    t = time.time()
    try:
        bpy.ops.object.quadriflow_remesh(target_faces=tgt, use_preserve_sharp=True,
                                         use_preserve_boundary=True)
    except Exception as e:
        print(f"{name}: quadriflow 실패 {str(e)[:60]}"); continue
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.012)
    bpy.ops.object.mode_set(mode='OBJECT')
    f1, i1 = len(o.data.polygons), islands(o)
    print(f"{name:22s} {f0:7,} {i0:6,} {f1:7,} {i1:6,} {f1/max(i1,1):7.1f} {time.time()-t:5.0f}")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
