# -*- coding: utf-8 -*-
"""곡률이 잡음인지 신호인지 가른다.

    blender -b --python curv_sweep.py -- out/named2.blend

이산 가우스 곡률의 부호합은 가우스-보네로 맞는데(위상 불변량이라 잡음이 상쇄된다)
|K| 적분은 36,798 sr 로 구(4pi=12.57)의 3,000배였다. 마칭큐브 계단면의 각 결손이
+/- 로 요동치며 쌓인 것이다. 그렇다면 평활할수록 |K| 는 급격히 떨어지고
부호합은 그대로여야 한다. 그게 맞으면 "잡음"이 확정된다.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
TWO_PI = 2.0 * math.pi


def curv(me):
    bm = bmesh.new(); bm.from_mesh(me)
    nv = len(bm.verts)
    ang = np.zeros(nv)
    bm.verts.ensure_lookup_table()
    for f in bm.faces:
        vs = [l.vert for l in f.loops]
        n = len(vs)
        for i, v in enumerate(vs):
            e1 = vs[(i - 1) % n].co - v.co
            e2 = vs[(i + 1) % n].co - v.co
            if e1.length > 1e-12 and e2.length > 1e-12:
                ang[v.index] += e1.angle(e2)
    bnd = np.array([any(len(e.link_faces) < 2 for e in v.link_edges) for v in bm.verts])
    K = np.where(bnd, math.pi - ang, TWO_PI - ang)
    area = sum(f.calc_area() for f in bm.faces)
    ne = sum(1 for e in bm.edges if len(e.link_faces) == 2)
    sharp = np.percentile([math.degrees(e.calc_face_angle(0.0))
                           for e in bm.edges if len(e.link_faces) == 2], 95)
    bm.free()
    return K.sum(), np.abs(K).sum(), area, sharp, nv


bpy.ops.wm.open_mainfile(filepath=SRC)
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
print(f"{'평활':>5s} {'데시':>6s} {'정점':>9s} {'sum K':>8s} {'∫|K|':>10s} "
      f"{'∫|K|/4pi':>9s} {'법선각p95':>9s}")
for dec, sm in ((1.0, 0), (0.10, 0), (0.10, 10), (0.10, 30), (0.10, 80),
                (0.03, 30), (0.01, 30)):
    o = src.copy(); o.data = src.data.copy()
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    if dec < 1.0:
        d = o.modifiers.new("d", 'DECIMATE'); d.ratio = dec
        bpy.ops.object.modifier_apply(modifier="d")
    if sm:
        s = o.modifiers.new("s", 'SMOOTH'); s.iterations = sm; s.factor = 0.7
        bpy.ops.object.modifier_apply(modifier="s")
    k, ak, ar, sh, nv = curv(o.data)
    print(f"{sm:5d} {dec:6.2f} {nv:9,} {k:8.1f} {ak:10.1f} {ak/(4*math.pi):9.1f} {sh:9.1f}")
    bpy.data.objects.remove(o, do_unlink=True)
print("\n부호합 sum K 는 위상 불변량이라 안 변해야 하고,")
print("∫|K| 만 떨어지면 그 차이는 전부 테셀레이션 잡음이다.")
