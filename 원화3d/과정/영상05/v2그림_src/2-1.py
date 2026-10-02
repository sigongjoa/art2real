# -*- coding: utf-8 -*-
"""2-1 처음 보는 물건(비더만 Fig 1 의 생각): 상자 몸통 + 기둥 + 깔때기 + 용수철 + 쐐기 판 + 바퀴 + 휜 꼬리 + 휜 관.
오목한 이음매에서 나뉘고, 조각은 원기둥 · 벽돌 · 쐐기 · 원뿔 같은 단순 입체다. blender -b -P 2-1.py → ../2-1.png"""
import bpy, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 선화 as S
sc = S.scene(thick=2.6)
def curve(pts, r, taper_to=None, name="c"):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = r; cu.bevel_resolution = 6; cu.resolution_u = 24; cu.use_fill_caps = True
    if taper_to is not None:
        for i, bp in enumerate(sp.bezier_points): bp.radius = 1 + (taper_to - 1) * i / (len(pts) - 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); return S.white(o)
# 몸통: 벽돌
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.4)); b = bpy.context.object; b.scale = (4.2, 2.6, 1.7); S.white(b, smooth=False)
# 바퀴: 몸통 밑 반쯤 묻힌 원판
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.75, depth=0.35, location=(-0.6, -1.0, 0.45), rotation=(0, math.pi / 2, 0)); S.white(bpy.context.object)
# 기둥(원기둥) + 굽은 팔(관) + 깔때기(원뿔)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.2, depth=2.2, location=(-1.3, -0.4, 3.35)); S.white(bpy.context.object)
curve([(-1.3, -0.4, 4.3), (-1.45, -0.4, 4.9), (-1.9, -0.4, 5.4)], 0.17, name="팔")
bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.15, radius2=0.75, depth=1.1, location=(-2.25, -0.4, 5.85), rotation=(0, math.radians(-35), 0), end_fill_type="NOTHING")
S.white(bpy.context.object)
# 쐐기 판: 몸통 위 오른쪽, 기울어진 넓적한 쐐기
me = bpy.data.meshes.new("쐐기"); tri = [(0, 0), (1.5, 0), (1.1, 1.7)]; d = 1.3
me.from_pydata([(x, y, z) for y in (-d / 2, d / 2) for x, z in tri], [], [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]); me.update()
w = bpy.data.objects.new("쐐기", me); sc.collection.objects.link(w); w.location = (0.6, -0.1, 2.25); S.white(w, smooth=False)
# 용수철: 기둥 꼭대기에서 쐐기로 가는 지그재그 선
pts = []; n = 9
for i in range(n + 1):
    t = i / n; pts.append((-1.1 + 2.6 * t, -0.4, 4.0 - 0.6 * t + (0.28 if i % 2 else -0.28)))
cu = bpy.data.curves.new("용수철", "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
for p, q in zip(sp.points, pts): p.co = (*q, 1)
cu.bevel_depth = 0.07; cu.bevel_resolution = 4; o = bpy.data.objects.new("용수철", cu); sc.collection.objects.link(o); S.white(o)
# 왼쪽 꼬리: 점점 가늘어지는 휜 뿔
curve([(-2.0, -0.2, 1.4), (-3.3, -0.3, 1.7), (-4.4, -0.6, 1.0), (-5.0, -0.8, 0.2)], 0.38, taper_to=0.15, name="꼬리")
# 오른쪽: 아래로 휘는 관
curve([(2.0, 0.6, 1.0), (2.7, 0.5, 0.6), (2.9, 0.2, -0.4)], 0.18, name="관")
S.look((-1.0, 0, 3.0), -28, 18, ortho=16)
S.shot("2-1.png")
