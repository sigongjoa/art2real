# -*- coding: utf-8 -*-
"""8-7 위: 눈 = 뼈 테(눈구멍) 속의 공 + 그 위에 얹힌 살의 띠(윗 · 아래 눈꺼풀). 앞 · 3/4 두 방향.
아래: 윤곽이 똑같은 머리 다섯 — 안내선만 휘어서 숙임 · 돌림이 읽힌다."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B
bpy, bmesh = B.bpy, B.bmesh
B.scene(line=2.0)
SKIN, WHITE, IRIS = (0.93, 0.74, 0.60), (0.97, 0.97, 0.96), (0.30, 0.42, 0.55)

def sphere(name, r, color, parent, seg=48, keep=None, thick=0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    if keep:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co)], context="VERTS")
    bm.to_mesh(me); bm.free(); o = B._obj(name, me, color, parent)
    for p in me.polygons: p.use_smooth = True
    if thick:
        m = o.modifiers.new("s", "SOLIDIFY"); m.thickness = thick; m.offset = 1
    return o

def eye(g):
    # 뼈 테: 판에서 공보다 큰 구멍을 판다
    bpy.ops.mesh.primitive_cube_add(size=1); plate = bpy.context.active_object; plate.parent = g
    plate.scale = (3.4, 1.0, 2.9); plate.location = (0, 0.55, 0.05); plate.data.materials.append(B.mat((0.80, 0.78, 0.75)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.28, segments=24, ring_count=12); cut = bpy.context.active_object
    cut.parent = g; cut.scale = (1.15, 1.0, 1.0)
    md = plate.modifiers.new("b", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cut; md.solver = "EXACT"
    bpy.context.view_layer.objects.active = plate; bpy.ops.object.modifier_apply(modifier="b"); bpy.data.objects.remove(cut)
    sphere("공", 1.0, WHITE, g)
    for r, t, c in ((0.42, 0.06, IRIS), (0.17, 0.09, (0.05, 0.05, 0.06))):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=t, vertices=40); d = bpy.context.active_object
        d.parent = g; d.rotation_euler = (math.pi / 2, 0, 0); d.location = (0, -math.sqrt(1 - r * r) + 0.0, 0); d.data.materials.append(B.mat(c))
    # 눈꺼풀 = 공 위에 얹힌 살의 띠
    sphere("윗꺼풀", 1.04, SKIN, g, keep=lambda v: v.y < 0.3 and 0.14 < v.z + 0.12 * v.y < 0.62, thick=0.14)
    sphere("아랫꺼풀", 1.04, SKIN, g, keep=lambda v: v.y < 0.2 and -0.72 < v.z < -0.46, thick=0.1)

eye(B.empty(loc=(-3.0, 0, 2.15), rot=(0, 0, 0)))
eye(B.empty(loc=(3.0, 0, 2.15), rot=(-10, 0, -50)))
# 머리 다섯: 부모가 세로로 늘인 공 → 어떻게 돌려도 윤곽은 같은 타원
PL = [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 0, 1))]
for k, rot in enumerate([(0, 0, 0), (28, 0, 0), (-25, 0, 0), (0, 0, 38), (22, 0, -45)]):
    par = B.empty(loc=((k - 2) * 2.75, 0, -2.45), scale=(1, 1, 1.28))
    s = sphere("머리", 0.95, (0.95, 0.94, 0.92), par, seg=64); s.rotation_euler = [math.radians(a) for a in rot]
    for l in B.section_lines(s, PL, t=0.022, lift=1.0):
        l.data.bevel_depth = 0.022
    nose = sphere("코", 0.07, B.ACCENT, s); nose.location = (0, -0.95, -0.25)
B.look((0, 0, 0), 0, 0, ortho=17)
B.shot("8-7")
