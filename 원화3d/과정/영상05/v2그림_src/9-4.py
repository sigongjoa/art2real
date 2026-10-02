# -*- coding: utf-8 -*-
"""9-4 옆에서 본 몸통: (왼) 매끈한 몸통 · (가운데) 같은 몸통을 면이 꺾이는 자리로 나눈 조각 + 가로 세 칸
(갈비 우리 · 배 · 골반) · (오른) 그 속의 덩어리(갈비 달걀 · 등뼈 · 골반)와 바깥 윤곽."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B
bpy, bmesh = B.bpy, B.bmesh
from mathutils import Vector
B.scene(line=1.8); B.sun(58, 0, 55, 2.0)

def ring(z, y0, y1, w, c=0.25):
    """z 높이의 모깎은 사각 단면(앞 y0 · 뒤 y1 · 너비 w)."""
    return [(sx * (w / 2 - c), y, z) for sx in (-1, 1) for y in (y0, y1)] + [(sx * w / 2, y, z) for sx in (-1, 1) for y in (y0 + c, y1 - c)]

BLOCKS = {  # 앞은 -y
    "갈비": [(7.2, -0.45, 0.55, 1.5), (6.4, -0.95, 0.85, 1.9), (5.6, -0.98, 0.85, 1.85), (4.9, -0.8, 0.7, 1.65)],
    "배": [(4.9, -0.8, 0.62, 1.6), (4.35, -0.98, 0.45, 1.45), (3.9, -0.92, 0.55, 1.55)],
    "골반": [(3.9, -0.92, 0.6, 1.65), (3.3, -0.75, 1.0, 1.85), (2.65, -0.45, 0.75, 1.5)]}
COL = {"갈비": B.WARM, "배": (0.88, 0.86, 0.80), "골반": B.COOL}

def trunk(dy, color=None):
    return [B.hull(sum((ring(*r) for r in rs), []), k, color or COL[k], loc=(0, dy, 0)) for k, rs in BLOCKS.items()]

def bands(dy):
    for z in (4.9, 3.9):
        B.rod((1.4, dy - 1.35, z + 0.25), (1.4, dy + 1.35, z - 0.25), t=0.035)

# 왼: 매끈한 몸통
parts = trunk(-4.4, B.CLAY); bpy.context.view_layer.update()
sm = B.smooth_copy(parts, voxel=0.05, iters=25)
for o in parts: bpy.data.objects.remove(o)
# 가운데: 면 조각 + 세 칸
trunk(0.0); bands(0.0)
# 오른: 속 덩어리 + 바깥 윤곽(옆 단면선)
out = trunk(4.4, B.CLAY); bpy.context.view_layer.update()
j = B.smooth_copy(out, voxel=0.05, iters=25)
for o in out: bpy.data.objects.remove(o)
for l in B.section_lines(j, [((0, 0, 0), (1, 0, 0))], color=(0.45, 0.45, 0.48), t=0.03, lift=1.0):
    l.location.x += 1.3
bpy.data.objects.remove(j)
me = bpy.data.meshes.new("egg"); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1)
for v in bm.verts:
    x, y, z = v.co; v.co = Vector((x * 0.8 * (0.9 - 0.2 * z), y * 0.85 + 0.05, z * 1.15 + 5.95))
bm.to_mesh(me); bm.free(); egg = B._obj("갈비달걀", me, B.WARM); egg.location.y = 4.4
for p in me.polygons: p.use_smooth = True
B.hull(B.cbox(-0.75, 0.75, -0.55, 0.6, -0.5, 0.5, c=0.25), "골반덩어리", B.COOL, rot=(-18, 0, 0), loc=(0, 4.4 + 0.15, 3.2))
pts = [(0, 4.4 + y, z) for y, z in ((0.5, 7.3), (0.72, 6.3), (0.62, 5.2), (0.35, 4.4), (0.45, 3.6))]
for a, b in zip(pts, pts[1:]): B.rod(a, b, color=(0.35, 0.35, 0.38), t=0.06, dashed=0.2)
bands(4.4)
B.look((0, 0, 4.9), 90, 0, ortho=14.5)
B.shot("9-4")
