# -*- coding: utf-8 -*-
"""생성 메시 진단: 셸 개수(분할 가능성) + 발 벌어짐 각(판정 기준 이식 확인).

    blender -b --python probe_mesh.py -- out/turn_front.glb
"""
import math
import os
import sys

import bpy
import bmesh
import mathutils

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in obs:
    o.select_set(True)
bpy.context.view_layer.objects.active = obs[0]
if len(obs) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active

# 높이 1.0, 발바닥 z=0, 중심 x=y=0 — 원화 프레임과 같은 규약
co = [ob.matrix_world @ v.co for v in ob.data.vertices]
lo = mathutils.Vector([min(c[i] for c in co) for i in range(3)])
hi = mathutils.Vector([max(c[i] for c in co) for i in range(3)])
s = 1.0 / (hi.z - lo.z)
ob.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
lo, hi = lo * s, hi * s
ob.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
bpy.ops.object.transform_apply(location=True)
print(f"정점 {len(ob.data.vertices):,}  면 {len(ob.data.polygons):,}")

# --- 셸 개수 = 분할 가능성 ---
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(ob.data)
seen, shells = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        c = stack.pop()
        comp.append(c)
        for e in c.link_edges:
            o = e.other_vert(c)
            if o.index not in seen:
                seen.add(o.index); stack.append(o)
    shells.append(len(comp))
bpy.ops.object.mode_set(mode='OBJECT')
shells.sort(reverse=True)
print(f"셸(loose parts) {len(shells)}개  상위: {shells[:10]}")

# --- 발 벌어짐 각: 뒷꿈치 -> 앞아래 끝 ---
V = []
for sgn, side in ((-1, "왼"), (1, "오")):
    f = [c for c in (ob.matrix_world @ v.co for v in ob.data.vertices)
         if c.z < 0.20 and c.x * sgn > 0.02]
    if len(f) < 50:
        print(f"{side}발: 정점 부족 {len(f)}"); V.append(None); continue
    top = sorted(f, key=lambda c: -c.z)[:len(f) // 12]
    heel = mathutils.Vector((sum(c.x for c in top) / len(top),
                             sum(c.y for c in top) / len(top),
                             sum(c.z for c in top) / len(top)))
    # 발톱 끝 = 가장 낮고 가장 앞(-y)인 무리
    bot = sorted(f, key=lambda c: c.z + c.y * 0.5)[:len(f) // 40]
    tip = mathutils.Vector((sum(c.x for c in bot) / len(bot),
                            sum(c.y for c in bot) / len(bot),
                            sum(c.z for c in bot) / len(bot)))
    d = tip - heel
    print(f"{side}발 뒷꿈치 x{heel.x:+.3f} y{heel.y:+.3f} z{heel.z:.3f}"
          f" -> 끝 x{tip.x:+.3f} y{tip.y:+.3f} z{tip.z:.3f}"
          f"  정면기울기 {math.degrees(math.atan2(d.x, -d.z)):+.1f}도")
    V.append(d)
if all(v is not None for v in V):
    a = mathutils.Vector((V[0].x, 0, V[0].z)).normalized()
    b = mathutils.Vector((V[1].x, 0, V[1].z)).normalized()
    c = max(-1.0, min(1.0, a.dot(b)))
    print(f"=> 정면투영 cos {c:+.4f}  벌어짐 {math.degrees(math.acos(c)):.1f}도"
          f"   (원화 36.2도 / 손코딩 CAD 38.8도)")
