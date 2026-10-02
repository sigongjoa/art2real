# -*- coding: utf-8 -*-
"""2-7 비행기: 동체 + 날개 둘(3 부품)에서 시작해 수직 꼬리(4) · 수평 꼬리 둘(6) · 기수(7) · 엔진 둘(9)까지 하나씩 더한다.
blender -b -P 2-7.py → _렌더/2-7.png + 2-7.json → 2-7.typ"""
import bpy, math, sys, os, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 선화 as S
sc = S.scene(thick=2.2)
YAW, PITCH = -30, 22
y, p = math.radians(YAW), math.radians(PITCH)
D = mathutils.Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
RIGHT = mathutils.Vector((math.cos(y), math.sin(y), 0)); UPV = D.cross(RIGHT).normalized() * -1
if UPV.z < 0: UPV = -UPV
def slab(name, pts, t, off):
    """평면 다각형(x, y) 을 두께 t 로 — 날개 · 꼬리 판"""
    n = len(pts); vs = [(x, yy, -t / 2) for x, yy in pts] + [(x, yy, t / 2) for x, yy in pts]
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = off; return o
def plane(c, k):
    objs = []
    def add(o, smooth=True): S.white(o, smooth); o.location = mathutils.Vector(o.location) + c; objs.append(o)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.36, depth=5.0, rotation=(0, math.pi / 2, 0)); add(bpy.context.object)   # 동체
    for sg in (-1, 1):                                                                                     # 날개 둘(뒤로 젖힌)
        add(slab("날개", [(-0.9, 0), (0.6, 0), (2.0, sg * 3.0), (1.5, sg * 3.0)][:: sg], 0.08, (0, 0, -0.1)), False)
    if k >= 4:                                                                                             # 수직 꼬리
        o = slab("수직", [(1.6, 0), (2.5, 0), (2.7, 1.5), (2.3, 1.5)], 0.07, (0, 0, 0)); o.rotation_euler = (math.pi / 2, 0, 0); o.location = (0, 0, 0.25); add(o, False)
    if k >= 6:                                                                                             # 수평 꼬리 둘
        for sg in (-1, 1): add(slab("수평", [(1.8, 0), (2.5, 0), (2.85, sg * 1.2), (2.55, sg * 1.2)][:: sg], 0.06, (0, 0, 0.1)), False)
    if k >= 7:                                                                                             # 기수(둥근 앞)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1); o = bpy.context.object; o.scale = (0.8, 0.35, 0.35); o.location = (-2.5, 0, 0); add(o)
    if k >= 9:                                                                                             # 엔진 둘(날개 밑)
        for sg in (-1, 1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.17, depth=0.9, rotation=(0, math.pi / 2, 0)); o = bpy.context.object; o.location = (0.4, sg * 1.3, -0.38); add(o)
    return objs
LAB = {}
SLOTS = [(3, -5.2, 4.1), (4, 5.2, 4.1), (6, -5.2, -0.1), (7, 5.2, -0.1), (9, 0.0, -4.3)]
for k, a, b in SLOTS:
    c = RIGHT * a + UPV * b; plane(c, k); LAB["부품 %d" % k] = tuple(c - UPV * 1.75)
S.look((0, 0, 0), YAW, PITCH, ortho=27, dist=80)
S.shot("2-7.png"); S.save_json("2-7.json", S.px(LAB))
