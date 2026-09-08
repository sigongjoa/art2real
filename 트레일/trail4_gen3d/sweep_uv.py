# -*- coding: utf-8 -*-
"""UV 파편화 원인 규명 스윕. 임계값을 지어내지 않는다.

    blender -b --python sweep_uv.py -- out/named2.blend

가설: 데시메이트가 만든 가늘고 긴 삼각형의 법선 요동이 Smart UV 의 각도 조건을
계속 건드려 섬이 부서진다. 그렇다면 (1) 평활하거나 (2) 각도를 올리면 줄어야 한다.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
PARTS = {"r_wolf_cannon": None, "c_foot": None, "c_shin": None}


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


def sharpness(me):
    """이웃 면 법선각의 p95. 계단 잡음의 크기."""
    bm = bmesh.new(); bm.from_mesh(me)
    a = [math.degrees(e.calc_face_angle(0.0)) for e in bm.edges if len(e.link_faces) == 2]
    bm.free()
    return float(np.percentile(a, 95)) if a else 0.0


bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = src.data
nf = len(me.polygons)
lab = np.empty(nf, np.int32); me.attributes["part_id"].data.foreach_get("value", lab)
import json
names = json.load(open(os.path.join(os.path.dirname(SRC), "..", "named_parts.json")))
name2pid = {names[i]: i + 1 for i in range(len(names))}

print(f"{'파츠':14s} {'설정':26s} {'면':>7s} {'섬':>6s} {'면/섬':>7s} {'법선각p95':>9s}")
for pname in PARTS:
    pid = name2pid.get(pname)
    sel = np.nonzero(lab == pid)[0]
    if not len(sel):
        print(f"{pname}: 없음"); continue
    for dec, smooth, ang in ((0.10, 0, 66), (0.10, 0, 89), (0.10, 10, 66),
                             (0.10, 10, 89), (0.10, 25, 89), (0.03, 10, 89)):
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        ks = set(sel.tolist())
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context='FACES')
        m2 = bpy.data.meshes.new("t"); bm.to_mesh(m2); bm.free()
        o = bpy.data.objects.new("t", m2); bpy.context.scene.collection.objects.link(o)
        d = o.modifiers.new("d", 'DECIMATE'); d.ratio = dec
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="d")
        if smooth:
            s = o.modifiers.new("s", 'SMOOTH'); s.iterations = smooth; s.factor = 0.7
            bpy.ops.object.modifier_apply(modifier="s")
        sh = sharpness(o.data)
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(ang), island_margin=0.012)
        bpy.ops.object.mode_set(mode='OBJECT')
        f, i = len(o.data.polygons), islands(o.data)
        print(f"{pname:14s} dec{dec:<5.2f} smooth{smooth:<3d} ang{ang:<3d} "
              f"{f:7,} {i:6,} {f/max(i,1):7.1f} {sh:9.1f}")
        bpy.data.objects.remove(o, do_unlink=True)
