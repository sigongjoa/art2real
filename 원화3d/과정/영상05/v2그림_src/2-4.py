# -*- coding: utf-8 -*-
"""2-4 같은 부품 둘(상자 · 둥근 손잡이), 붙이는 자리만 바꾼다: 서류 가방 · 서랍 · 컵 · 양동이.
blender -b -P 2-4.py → _렌더/2-4.png + 2-4.json(라벨 자리) → 2-4.typ 가 라벨을 얹는다."""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 선화 as S
sc = S.scene()
def box(loc, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; return S.white(o, smooth=False)
def cyl(loc, r, h):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=h, location=loc); return S.white(bpy.context.object)
def handle(loc, R, r, rot):
    """반 고리(둥근 손잡이): 토러스의 위 절반"""
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64, minor_segments=16, location=loc, rotation=rot)
    o = bpy.context.object; bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -1e-4], context="VERTS"); bm.to_mesh(o.data); bm.free()
    return S.white(o)
X = [-7.5, -2.5, 2.5, 6.6]
_c, _s = math.cos(math.radians(20)), math.sin(math.radians(20))
def P(x, y, z):
    """화면 가로축(시점 yaw 20)을 따라 놓는다 — 물건마다 같은 높이에 보이게"""
    return (x * _c - y * _s + 0, x * _s + y * _c, z)
def Q(x, dx, dy, z):
    """물건 자리(P) + 물건 축 그대로의 오프셋(손잡이를 면에 붙일 때)"""
    a = P(x, 0, z); return (a[0] + dx, a[1] + dy, z)
# a 서류 가방: 손잡이를 윗면에
box(P(X[0], 0, 1.4), (3.2, 0.9, 2.2)); handle(P(X[0], 0, 2.5), 0.6, 0.11, (math.pi / 2, 0, 0))
# b 서랍: 같은 상자를 눕히고 손잡이를 앞면에
box(P(X[1], 0, 0.55), (3.4, 2.6, 0.9)); handle(Q(X[1], 0.6, -1.3, 0.55), 0.38, 0.09, (0, 0, math.pi))
# c 컵: 원기둥 옆면에
cyl(P(X[2], 0, 0.85), 0.75, 1.7); handle(Q(X[2], -0.72, 0, 0.9), 0.48, 0.1, (math.pi / 2, -math.pi / 2, 0))
# d 양동이: 원기둥 위로 걸기
cyl(P(X[3], 0, 0.85), 0.8, 1.7); handle(P(X[3], 0, 1.7), 0.78, 0.06, (math.pi / 2, 0, 0))
S.look(P(-0.45, 0, 1.0), 20, 18, ortho=19.5)
S.shot("2-4.png")
S.save_json("2-4.json", S.px({k: P(x, 0, -0.6) for k, x in zip("abcd", X)}))
