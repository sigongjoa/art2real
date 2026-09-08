# -*- coding: utf-8 -*-
"""두 손실을 그림으로. (1) 어느 시점에도 안 보이는 면 (2) 곡률 잡음.

    blender -b --python shot_loss.py -- out/named2.blend out/L
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, PRE = os.path.abspath(argv[0]), os.path.abspath(argv[1])
TWO_PI = 2.0 * math.pi


def ring(n):
    return [(math.sin(a), -math.cos(a), 0.0) for a in (2 * math.pi * i / n for i in range(n))]


KSCALE = None
VIEWSETS = {"v3": [(0, 1, 0), (-1, 0, 0), (0, -1, 0)], "v6": ring(6)}


def setup(o):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'VERTEX'
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = 'BOTH'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 700
    sc.view_settings.view_transform = 'Standard'
    if "c" not in bpy.data.objects:
        cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 1.2
        cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    return bpy.data.objects["c"]


def paint(o, fcol, name):
    me = o.data
    if me.color_attributes.get(name):
        me.color_attributes.remove(me.color_attributes[name])
    ca = me.color_attributes.new(name, 'BYTE_COLOR', 'CORNER')
    nl = len(me.loops)
    buf = np.empty(nl * 4, np.float32); buf[3::4] = 1.0
    ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_total", lt)
    for i in range(len(me.polygons)):
        s = ls[i] * 4
        for j in range(lt[i]):
            buf[s + j * 4:s + j * 4 + 3] = fcol[i]
    ca.data.foreach_set("color", buf)
    me.update()
    for a in me.color_attributes:
        pass
    me.color_attributes.active_color_index = list(me.color_attributes).index(ca)


def render(cam, tag):
    sc = bpy.context.scene
    for az, v in ((0, "front"), (90, "side"), (180, "back")):
        a = math.radians(az)
        cam.location = (math.sin(a) * 6, -math.cos(a) * 6, 0.5)
        cam.rotation_euler = (math.radians(90), 0, a)
        sc.render.filepath = f"{PRE}_{tag}_{v}.png"
        bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
bpy.context.view_layer.objects.active = o
d = o.modifiers.new("d", 'DECIMATE'); d.ratio = 0.12
bpy.ops.object.modifier_apply(modifier="d")
me = o.data
nf = len(me.polygons)
cen = np.empty(nf * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
nor = np.empty(nf * 3); me.polygons.foreach_get("normal", nor); nor = nor.reshape(-1, 3)
a3 = np.empty(nf); me.polygons.foreach_get("area", a3)
cam = setup(o)

# --- (1) 시점 커버리지 ---
for tag, dirs in VIEWSETS.items():
    seen = np.zeros(nf, bool)
    for dv in dirs:
        v = Vector(dv)
        cand = np.nonzero(nor @ np.array(dv) < -0.05)[0]
        for k in cand:
            c = Vector(cen[k])
            hit, loc, _, _ = o.ray_cast(c - v * 4.0, v)
            if hit and (loc - c).length <= 0.006:
                seen[k] = True
    pct = a3[seen].sum() / a3.sum() * 100
    # 미관측 면은 정의상 가려져 있다. 밖에서 통짜로 찍으면 안 보인다 —
    # 보이는 면을 지우고 **미관측만** 남겨야 어디가 비었는지 보인다.
    ob = o.copy(); ob.data = o.data.copy()
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    o.hide_render = True
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if seen[f.index]], context='FACES')
    bm.to_mesh(ob.data); bm.free()
    if len(ob.data.polygons):
        paint(ob, np.tile(np.array([0.88, 0.15, 0.15]), (len(ob.data.polygons), 1)), "cov")
        render(cam, tag)
    print(f"{tag}: 가시 {pct:.1f}%  미관측 {100-pct:.1f}%  "
          f"(남긴 면 {len(ob.data.polygons):,})")
    bpy.data.objects.remove(ob, do_unlink=True)
    o.hide_render = False

# 몸 전체 실루엣 (비교용 고스트)
paint(o, np.tile(np.array([0.86, 0.87, 0.89]), (nf, 1)), "ghost")
render(cam, "ghost")

# --- (2) 곡률 잡음 ---
for tag, sm in (("k0", 0), ("k30", 30)):
    ob = o.copy(); ob.data = o.data.copy()
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    o.hide_render = True
    if sm:
        s = ob.modifiers.new("s", 'SMOOTH'); s.iterations = sm; s.factor = 0.7
        bpy.ops.object.modifier_apply(modifier="s")
    m2 = ob.data
    bm = bmesh.new(); bm.from_mesh(m2); bm.verts.ensure_lookup_table()
    ang = np.zeros(len(m2.vertices))
    for f in bm.faces:
        vs = [l.vert for l in f.loops]
        n = len(vs)
        for i, v in enumerate(vs):
            e1 = vs[(i - 1) % n].co - v.co; e2 = vs[(i + 1) % n].co - v.co
            if e1.length > 1e-12 and e2.length > 1e-12:
                ang[v.index] += e1.angle(e2)
    bnd = np.array([any(len(e.link_faces) < 2 for e in v.link_edges) for v in bm.verts])
    K = np.where(bnd, math.pi - ang, TWO_PI - ang)
    bm.free()
    # |K| 를 본다. 부호는 상쇄되지만 **잡음의 크기**는 |K| 에 남는다.
    # 두 그림의 눈금을 같게 하려고 원본의 p90 으로 고정한다 (환경변수로 전달).
    fk = np.array([np.mean([abs(K[v]) for v in p.vertices]) for p in m2.polygons])
    if KSCALE is None:
        KSCALE = float(np.percentile(fk, 90))
        print(f"  |K| 눈금 = 원본 p90 = {KSCALE:.4f} sr")
    t = np.clip(fk / KSCALE, 0, 1)
    # 흰 -> 주황 -> 검정
    col = np.stack([1.0 - t * 0.95, 1.0 - t * 0.75, 1.0 - t * 0.30], 1)
    bpy.context.scene.display.shading.show_cavity = False
    paint(ob, col, "curv")
    render(cam, tag)
    print(f"{tag}: sum K {K.sum():.1f}  ∫|K| {np.abs(K).sum():.0f} "
          f"({np.abs(K).sum()/(4*math.pi):.0f}x 구)  (빨강=볼록, 파랑=오목)")
    bpy.data.objects.remove(ob, do_unlink=True)
    o.hide_render = False
print("LOSSSHOT OK")
