# -*- coding: utf-8 -*-
"""2-5 번호 붙인 지온 다섯(①벽돌 ②원기둥 ③굽은 손잡이 ④원뿔대 ⑤쐐기)과, 그 번호들로만 지은 물건 여섯.
blender -b -P 2-5.py → _렌더/2-5.png + 2-5.json(번호 자리) → 2-5.typ 가 번호 · 칸막이를 얹는다."""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 선화 as S
sc = S.scene(thick=2.2)
YAW = 22; _c, _s = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
def P(x, z, dx=0, dy=0, dz=0):
    """화면 가로(x) · 세로(z) 자리 + 물건 축 그대로의 오프셋"""
    return (x * _c + dx, x * _s + dy, z + dz)
TAGS = []
def tag(n, x, z, dx=0, dy=0, dz=0): TAGS.append((n, P(x, z, dx, dy, dz)))
def brick(loc, size, rz=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, rz)); o = bpy.context.object; o.scale = size; return S.white(o, smooth=False)
def cyl(loc, r1, r2, h, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot); return S.white(bpy.context.object)
def handle(loc, R, r, rot):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64, minor_segments=16, location=loc, rotation=rot)
    o = bpy.context.object; bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -1e-4], context="VERTS"); bm.to_mesh(o.data); bm.free(); return S.white(o)
def wedge(loc, w, d, h, top=0.35):
    """쐐기: 앞이 낮고 뒤가 높은 사다리꼴 기둥(옆에서 보면 직각 사다리꼴)"""
    me = bpy.data.meshes.new("w"); prof = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, -d / 2, h * top), (-w / 2, -d / 2, h * top),
                                          (-w / 2, d / 2, 0), (w / 2, d / 2, 0), (w / 2, d / 2, h), (-w / 2, d / 2, h)]
    me.from_pydata(prof, [], [(0, 1, 2, 3), (5, 4, 7, 6), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4), (1, 5, 6, 2)]); me.update()
    o = bpy.data.objects.new("w", me); sc.collection.objects.link(o); o.location = loc; return S.white(o, smooth=False)
UP = (math.pi / 2, 0, 0)             # 손잡이가 위로 선다(정면에서 보이는 고리)
# ---------- 왼쪽: 번호 지온 ----------
GX = (-12.4, -9.6); GZ = (2.3, 0.0, -2.3)
brick(P(GX[0], GZ[0]), (1.6, 0.9, 1.0)); tag(1, GX[0], GZ[0], dz=1.0)
cyl(P(GX[1], GZ[0]), 0.55, 0.55, 1.2); tag(2, GX[1], GZ[0], dz=1.1)
handle(P(GX[0], GZ[1] - 0.4), 0.6, 0.13, UP); tag(3, GX[0], GZ[1], dz=0.75)
cyl(P(GX[1], GZ[1]), 0.75, 0.35, 1.2); tag(4, GX[1], GZ[1], dz=1.1)
wedge(P((GX[0] + GX[1]) / 2, GZ[2] - 0.5), 1.6, 1.2, 1.1); tag(5, (GX[0] + GX[1]) / 2, GZ[2], dz=1.05)
# ---------- 오른쪽: 물건 ----------
OX = (-3.6, 1.6, 6.8); OZ = (1.6, -2.2)
# 전화기 = ⑤ 쐐기 몸 + ② 다이얼 + ③ 수화기
x, z = OX[0], OZ[0]
wedge(P(x, z - 0.6), 2.4, 1.8, 1.3, top=0.45)
sl = math.atan((1.3 - 1.3 * 0.45) / 1.8)                       # 앞 비탈 기울기
cyl(P(x, z, dy=0.0, dz=-0.6 + 1.3 * (0.45 + 1) / 2 + 0.08), 0.5, 0.5, 0.16, rot=(sl, 0, 0))   # 비탈 위 다이얼
handle(P(x, z, dy=0.7, dz=0.62), 0.95, 0.2, UP)
tag(5, x, z, dx=-1.6, dz=-0.45); tag(2, x, z, dx=0.75, dy=-0.2, dz=0.15); tag(3, x, z, dy=0.7, dz=1.85)
# 서류 가방 = ① + ③
x = OX[1]; brick(P(x, z), (2.4, 0.7, 1.6)); handle(P(x, z + 0.8), 0.5, 0.11, UP)
tag(1, x, z, dx=1.55, dz=-0.3); tag(3, x, z, dz=1.75)
# 서랍 = 납작 ① + ③(앞면)
x = OX[2]; brick(P(x, z - 0.4), (2.6, 2.0, 0.75)); handle(P(x, z - 0.4, dy=-1.0), 0.32, 0.08, (0, 0, math.pi))
tag(1, x, z, dz=0.65); tag(3, x, z, dy=-1.0, dz=-1.1)
# 컵 = ② + ③(옆)
z = OZ[1]; x = OX[0]; cyl(P(x, z), 0.65, 0.65, 1.5); handle(P(x, z, dx=-0.62), 0.42, 0.1, (math.pi / 2, -math.pi / 2, 0))
tag(2, x, z, dz=1.15); tag(3, x, z, dx=-1.45, dz=0.1)
# 양동이 = ④ + ③(위로 걸기)
x = OX[1]; cyl(P(x, z), 0.55, 0.8, 1.5); handle(P(x, z + 0.75), 0.78, 0.06, UP)
tag(4, x, z, dx=1.15, dz=-0.2); tag(3, x, z, dz=1.8)
# 램프 = ② 기둥 · 받침 + ④ 갓
x = OX[2]; cyl(P(x, z - 0.6), 0.6, 0.6, 0.15); cyl(P(x, z), 0.1, 0.1, 1.2); cyl(P(x, z + 0.85), 0.85, 0.35, 0.9)
tag(4, x, z, dx=1.25, dz=0.9); tag(2, x, z, dx=0.5, dz=-0.15)
S.look(P(-2.8, 0.1), YAW, 14, ortho=25)
S.shot("2-5.png")
d = S.px({str(i): p for i, (n, p) in enumerate(TAGS)}); S.save_json("2-5.json", [[TAGS[i][0], *d[str(i)]] for i in range(len(TAGS))])
