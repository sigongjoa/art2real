# -*- coding: utf-8 -*-
"""9-3 갈비뼈 덩어리 = 살짝 원뿔꼴인 달걀(아래쪽에서 가장 넓다) + 띠처럼 감긴 갈비(앞으로 내려간다).
뒤에는 납작한 어깨뼈 판 둘과 등뼈. 3/4 앞 · 옆 · 뒤."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B
bpy, bmesh = B.bpy, B.bmesh
from mathutils import Vector
B.scene(line=1.8)

def egg(g):
    me = bpy.data.meshes.new("egg"); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1)
    for v in bm.verts:
        x, y, z = v.co; v.co = Vector((x * 1.2 * (0.9 - 0.22 * z), y * 0.92 * (0.95 - 0.1 * z), z * 1.6))
    bm.to_mesh(me); bm.free(); o = B._obj("갈비", me, (0.93, 0.92, 0.89), g)
    for p in me.polygons: p.use_smooth = True
    return o

def on_back(o, x, z, lift=0.03, side=1):
    bpy.context.view_layer.update(); ok, hit, n, i = o.ray_cast(Vector((x, 5 * side, z)), Vector((0, -side, 0))); assert ok, (x, z); return hit.y + lift * side

def ribcage(g):
    o = egg(g)
    k = 0.55
    B.section_lines(o, [((0, 0, z), (0, -k, 1)) for z in (-1.0, -0.55, -0.1, 0.35, 0.8, 1.2)], t=0.035, lift=1.012)
    for s in (-1, 1):   # 어깨뼈: 등에 얹힌 납작한 세모 판
        P = [(s * 0.14, 0.95), (s * 0.68, 0.95), (s * 0.52, -0.45), (s * 0.66, 0.4)]
        pts = [(x, on_back(o, x, z, d), z) for x, z in P for d in (0.02, 0.12)]
        B.hull(pts, "어깨뼈", B.COOL, g)
    by = on_back(o, 0, 0, 0.12)
    B.rod((0, by, 2.0), (0, by, -2.2), color=(0.35, 0.35, 0.38), t=0.06, parent=g, dashed=0.2)
    B.hull([(x, on_back(o, x, z, d, -1), z) for x in (-0.12, 0.12) for z in (-0.5, 0.1, 0.7, 1.15) for d in (0.01, 0.08)], "복장뼈", B.WARM, g)

for x, yaw in ((-4.2, -30), (0, -90), (4.2, 180)):
    ribcage(B.empty(loc=(x, 0, 0), rot=(0, 0, yaw)))
B.look((0, 0, -0.1), 0, 5, ortho=13.8)
B.shot("9-3")
