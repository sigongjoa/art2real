# -*- coding: utf-8 -*-
"""2-2 원기둥 하나에서 지온 만들기: 단면 모서리(곧게) · 대칭(없앰) · 크기(커짐 · 커졌다 작아짐) · 축(굽힘).
지온마다 따로 렌더 → 2-2.typ 가 가운데 원기둥 둘레에 화살표 · 이름표로 배치. blender -b -P 2-2.py"""
import bpy, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 선화 as S
sc = S.scene(res=(800, 560), thick=2.6)
def geon(name, verts=64, r1=1, r2=1, bend=0, barrel=0, asym=0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=4, end_fill_type="NGON")
    o = bpy.context.object; o.name = name
    if barrel or bend or asym:
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.subdivide(number_cuts=24); bpy.ops.object.mode_set(mode="OBJECT")
    for v in o.data.vertices:
        z = v.co.z / 2
        if barrel: k = 1 + barrel * (1 - z * z); v.co.x *= k; v.co.y *= k
        if asym and v.co.x < 0: v.co.x *= asym          # 단면 한쪽만 납작 → 거울 대칭 없음
    if bend:
        m = o.modifiers.new("b", "SIMPLE_DEFORM"); m.deform_method = "BEND"; m.angle = math.radians(bend); m.deform_axis = "Y"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="b")
    o.rotation_euler = (0, math.pi / 2, 0)                # 축을 가로로
    S.white(o, smooth=verts > 8); return o
G = {"원기둥": geon("원기둥"), "각기둥": geon("각기둥", verts=4), "원뿔": geon("원뿔", r1=0.35, r2=1.25),
     "통": geon("통", r1=0.55, r2=0.55, barrel=1.1), "굽은관": geon("굽은관", r1=0.6, r2=0.6, bend=120), "비대칭": geon("비대칭", asym=0.35)}
for k in G:
    for j, o in G.items(): o.hide_render = (j != k)
    S.look((0, 0, 0), 28, 18, ortho=5.8); S.shot("2-2_%s.png" % k)
