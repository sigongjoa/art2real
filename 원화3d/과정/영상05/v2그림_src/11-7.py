# -*- coding: utf-8 -*-
"""11-7 앤더슨: 찰흙 개 → 초록 상자 틀 → 부위(머리 · 몸통 · 다리 · 꼬리) → 자세 바꾼 개. dog() 는 원화3d/과정/영상05/교재3D_3.py ⑨ 에서 옮김."""
import bpy, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
D = os.path.dirname(os.path.abspath(__file__))
PARTS = {"몸": ((0, 0, 1.4), (1.6, 0.55, 0.5), 0), "목": ((1.45, 0, 1.95), (0.3, 0.28, 0.55), -35), "머리": ((1.9, 0, 2.45), (0.55, 0.3, 0.3), 0),
         "다리앞1": ((1.1, 0.35, 0.6), (0.17, 0.17, 0.6), 0), "다리앞2": ((1.1, -0.35, 0.6), (0.17, 0.17, 0.6), 0),
         "다리뒤1": ((-1.1, 0.35, 0.6), (0.17, 0.17, 0.6), 0), "다리뒤2": ((-1.1, -0.35, 0.6), (0.17, 0.17, 0.6), 0), "꼬리": ((-1.85, 0, 1.75), (0.35, 0.1, 0.1), 35)}
COLS = {"몸": (0.9, 0.25, 0.2, 1), "목": (0.95, 0.85, 0.2, 1), "머리": (0.95, 0.85, 0.2, 1), "꼬리": (0.2, 0.3, 0.9, 1),
        "다리앞1": (0.3, 0.85, 0.4, 1), "다리앞2": (0.2, 0.75, 0.8, 1), "다리뒤1": (0.65, 0.35, 0.9, 1), "다리뒤2": (0.85, 0.45, 0.85, 1)}
def dog(kind, pose=0.0, x0=0):
    for n, (loc, s, ry) in PARTS.items():
        loc = mathutils.Vector(loc); rot = ry
        if pose and n.startswith("다리앞"): rot += -40 * pose; loc += mathutils.Vector((0.35 * pose, 0, 0.12 * pose))
        if pose and n.startswith("다리뒤"): rot += 30 * pose; loc += mathutils.Vector((-0.3 * pose, 0, 0.1 * pose))
        if pose and n in ("목", "머리"): loc += mathutils.Vector((0, 0, 0.35 * pose))
        if pose and n == "꼬리": rot += 40 * pose
        loc += mathutils.Vector((x0, 0, 0))
        if kind == "점토":
            bpy.ops.object.metaball_add(type="ELLIPSOID", location=loc); m = bpy.context.object; el = m.data.elements[0]; el.size_x, el.size_y, el.size_z = s[0] * 1.1, s[1] * 1.1, s[2] * 1.1
            m.rotation_euler = (0, math.radians(rot), 0); m.data.resolution = 0.08; m.data.render_resolution = 0.05; m.color = (0.35, 0.55, 0.85, 1)
        else:
            bpy.ops.mesh.primitive_cube_add(size=2, location=loc, rotation=(0, math.radians(rot), 0)); m = bpy.context.object; m.scale = s
            m.color = (0.45, 0.9, 0.5, 1) if kind == "틀" else COLS[n]
sc = H.scene(res=(2600, 820)); sc.render.film_transparent = True
sc.display.shading.show_cavity = True
for k, (kind, pose) in enumerate([("점토", 0), ("틀", 0), ("부위", 0), ("점토", 1.0)]):
    dog(kind, pose, x0=(k - 1.5) * 7.2)
# 메타볼은 이름 앞부분이 같으면 한 덩어리로 녹는다 — 두 마리가 섞이지 않게 x 로 충분히 뗌
H.look((0, 0, 1.45), 22, 0, ortho=27.9); H.shot(os.path.join(D, "_r", "11-7.png"))
