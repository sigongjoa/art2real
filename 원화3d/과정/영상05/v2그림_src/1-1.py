# -*- coding: utf-8 -*-
"""1-1 나뭇가지 너머의 건물(Kellman & Shipley Fig 1 사진의 생각을 다시 연출):
앙상한 가지가 앞에서 건물을 수십 조각으로 자르지만 건물 하나로 보인다. blender -b -P 1-1.py → _렌더/1-1.png → typst 1-1.typ → ../1-1.png"""
import bpy, bmesh, math, random, sys, os, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_렌더", "1-1.png")   # 1-1.typ 가 흰 판 가운데 80% 로 얹는다
sc = H.scene(res=(1920, 1080), transparent=False, cavity=False)
sc.view_settings.view_transform = "Standard"; sc.world.color = (0.86, 0.89, 0.93)          # 흐린 하늘
sc.display.shading.light = "STUDIO"; sc.display.shading.show_shadows = False
try: sc.display.shading.studio_light = "outdoor.sl"          # 하늘빛이 위에서 — 풀밭 윗면이 밝게
except TypeError as e: print("studio_light", e)
def box(loc, size, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; o.color = color; return o
STONE, DARK = (0.74, 0.69, 0.60, 1), (0.25, 0.23, 0.22, 1)
# ---- 건물: 높은 탑 + 낮은 몸채 + 작은 탑 둘 (총안 · 창) ----
def tower(cx, w, h, y=0.0):
    box((cx, y, h / 2), (w, w, h), STONE)
    n = 4; s = w / (2 * n - 1)
    for i in range(n):                                   # 총안(꼭대기 톱니)
        for sx, sy in ((1, 0), (0, 1)):
            pass
    for i in range(n):
        x = cx - w / 2 + s / 2 + i * 2 * s
        box((x, y - w / 2 + s / 2, h + s / 2), (s, s, s), STONE)
    for k in range(int(h // 2.6)):                       # 세로로 늘어선 좁은 창
        box((cx, y - w / 2 - 0.01, 1.6 + k * 2.6), (w * 0.18, 0.05, 1.1), DARK)
tower(-2.5, 4.0, 15.0)
box((5.5, 1.0, 3.5), (9.0, 4.0, 7.0), STONE)                         # 몸채
for k in range(4): box((2.5 + k * 2.0, -1.02, 2.8), (0.6, 0.05, 1.8), DARK)
tower(3.4, 2.4, 9.0, y=0.4); tower(7.8, 2.4, 9.0, y=0.4)
box((5.6, -1.04, 1.1), (1.2, 0.05, 2.2), DARK)                        # 문
box((0, 0, -0.05), (80, 60, 0.1), (0.62, 0.70, 0.52, 1))              # 풀밭
# ---- 앞쪽 나무: 재귀 가지(가늘어지며 갈라진다) ----
random.seed(7); bm = bmesh.new()
def seg(a, b, r0, r1):
    d = b - a; L = d.length
    m = mathutils.Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=6, radius1=r0, radius2=r1, depth=L, matrix=m)
def branch(p, d, L, r, depth):
    q = p + d * L; seg(p, q, r, r * 0.7)
    if depth == 0 or r < 0.012: return
    for _ in range(random.choice((2, 2, 3))):
        nd = (d + mathutils.Vector((random.uniform(-0.9, 0.9), random.uniform(-0.3, 0.3), random.uniform(-0.1, 0.7)))).normalized()
        branch(q, nd, L * random.uniform(0.62, 0.82), r * 0.62, depth - 1)
for x, y, lean in ((-8.5, -9.0, 0.10), (-3.6, -11.0, -0.05), (1.0, -7.5, 0.05), (4.8, -10.5, 0.08), (9.0, -9.5, -0.12), (-0.8, -13.0, 0.12), (6.8, -7.0, -0.05)):
    base = mathutils.Vector((x, y, 0)); trunk = mathutils.Vector((lean, 0, 1)).normalized()
    top = base + trunk * random.uniform(2.6, 3.6); seg(base, top, 0.3, 0.22)
    for _ in range(4):
        d = (trunk + mathutils.Vector((random.uniform(-1.0, 1.0), random.uniform(-0.2, 0.2), random.uniform(0.2, 0.9)))).normalized()
        branch(top, d, 3.2, 0.18, 7)
me = bpy.data.meshes.new("가지"); bm.to_mesh(me); bm.free(); t = bpy.data.objects.new("가지", me); sc.collection.objects.link(t); t.color = (0.05, 0.045, 0.04, 1)
# ---- 카메라: 원근 · 사람 눈높이에서 살짝 올려다봄 ----
cam = sc.camera; cam.data.type = "PERSP"; cam.data.lens = 30
cam.location = (1.0, -34.0, 4.0); cam.rotation_euler = mathutils.Vector((0.5, 34.0, 4.5)).to_track_quat("-Z", "Y").to_euler()
H.shot(OUT)
