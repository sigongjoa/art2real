# -*- coding: utf-8 -*-
"""11-4 일반화 원기둥: 커피포트(사진 대신 블렌더 모형) → 부품마다 '단면을 축 따라 쓸어' 만든 원기둥(고리 + 빨간 축). 연구자 사진은 그리지 않음."""
import bpy, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
D = os.path.dirname(os.path.abspath(__file__)); V = mathutils.Vector
def bez(ps, t):
    while len(ps) > 1: ps = [a.lerp(b, t) for a, b in zip(ps, ps[1:])]
    return ps[0]
PARTS = {   # 이름: (축 조절점, 반지름 함수 r(t), 고리 수)
    "몸통": ([V((0, 0, 0)), V((0, 0, 1.6))], lambda t: 0.85 - 0.15 * t + 0.05 * math.sin(math.pi * t), 9),
    "뚜껑": ([V((0, 0, 1.6)), V((0, 0, 1.95))], lambda t: 0.68 * math.sqrt(max(0.0, 1 - (0.92 * t) ** 2)), 6),
    "꼭지": ([V((0, 0, 1.95)), V((0, 0, 2.2))], lambda t: 0.1 + 0.1 * t, 3),
    "주둥이": ([V((0.72, 0, 0.45)), V((1.45, 0, 0.7)), V((1.6, 0, 1.55))], lambda t: 0.24 - 0.16 * t, 10),
    "손잡이": ([V((-0.68, 0, 1.45)), V((-1.6, 0, 1.6)), V((-1.4, 0, 0.35)), V((-0.72, 0, 0.35))], lambda t: 0.08, 12),
}
def sweep(name, ctrl, rf, rings, segs, off=V((0, 0, 0)), col=(0.93, 0.93, 0.9, 1), wire=False):
    vs, fs = [], []; b = V((0, 1, 0))
    for i in range(rings + 1):
        t = i / rings; p = bez(ctrl, t); tg = (bez(ctrl, min(1, t + 1e-3)) - bez(ctrl, max(0, t - 1e-3))).normalized(); n = tg.cross(b).normalized()
        for j in range(segs):
            a = 2 * math.pi * j / segs; vs.append(p + off + rf(t) * (math.cos(a) * n + math.sin(a) * b))
    for i in range(rings):
        for j in range(segs): fs.append((i * segs + j, i * segs + (j + 1) % segs, (i + 1) * segs + (j + 1) % segs, (i + 1) * segs + j))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.color = col
    for f in me.polygons: f.use_smooth = not wire
    if wire: w = o.modifiers.new("w", "WIREFRAME"); w.thickness = 0.018
    return o
def tube(name, pts, r, col):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    cu.bevel_depth = r; cu.bevel_resolution = 4; o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); o.color = col; return o
sc = H.scene(res=(1100, 1100)); sc.render.film_transparent = True
# ① 모형
for n, (c, rf, k) in PARTS.items():
    o = sweep(n, c, rf, 48, 64); 
    if n == "꼭지": o.color = (0.85, 0.85, 0.82, 1)
H.look((0, 0, 1.1), 0, 12, ortho=4.3); H.shot(os.path.join(D, "_r", "11-4_pot.png"))
for o in list(sc.objects):
    if o.type in ("MESH", "CURVE"): bpy.data.objects.remove(o)
# ② 부품으로 나눈 일반화 원기둥 — 떼어 놓고 몸통 가운데와 회색 선으로 잇는다
OFF = {"몸통": V((0, 0, 0)), "뚜껑": V((0, 0, 0.75)), "꼭지": V((0, 0, 1.15)), "주둥이": V((0.85, 0, 0.25)), "손잡이": V((-0.85, 0, 0.1))}
RED = (0.9, 0.12, 0.1, 1); GRY = (0.55, 0.55, 0.55, 1)
hub = V((0, 0, 0.8))
for n, (c, rf, k) in PARTS.items():
    sweep(n, c, rf, k, 16, off=OFF[n], col=(0.15, 0.15, 0.18, 1), wire=True)
    tube(n + "축", [bez(c, i / 20) + OFF[n] for i in range(21)], 0.025, RED)
    mid = bez(c, 0.5) + OFF[n]
    if n != "몸통":
        tube(n + "이음", [hub, mid], 0.012, GRY)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=mid); bpy.context.object.color = GRY
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=hub); bpy.context.object.color = GRY
H.look((0, 0, 1.3), 0, 12, ortho=5.6); H.shot(os.path.join(D, "_r", "11-4_gc.png"))
