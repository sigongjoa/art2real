"""11-4 커피포트 일반화 원기둥(Mundy 그림4) — 동그라미를 축 따라 밀어 몸통(크기 변화) · 주둥이(굽은 축 · 점점 작게) · 손잡이(C 자 축)를 차례로 쓸어 만든다 → 포트가 기울어 고양이 그릇에 물."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def sweep(pts, radii, m):                      # 축 + 단면 반지름 = 일반화 원기둥 · bevel_factor_end 로 쓸기
    cu = bpy.data.curves.new("gc", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 10; cu.use_fill_caps = True
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.use_endpoint_u = True; sp.order_u = 3
    for p, q, r in zip(sp.points, pts, radii): p.co = (*q, 1); p.radius = r
    o = bpy.data.objects.new("gc", cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return o, cu

T = 시작(); 무대(ARGS[1])
pot_m = mat("포트", (0.55, 0.72, 0.95), 0.4)
H = 1.7
prof = [(0.0, 0.5), (0.25, 0.66), (0.6, 0.72), (1.0, 0.6), (1.35, 0.42), (1.55, 0.36), (H, 0.44)]
body, bcu = sweep([(0, 0, z) for z, _ in prof], [r for _, r in prof], pot_m)
spout, scu = sweep([(0.5, 0, 0.45), (0.85, 0, 0.6), (1.0, 0, 1.0), (1.18, 0, 1.5)], [0.17, 0.13, 0.1, 0.07], pot_m)
handle, hcu = sweep([(-0.55, 0, 1.3), (-0.95, 0, 1.35), (-1.08, 0, 0.9), (-0.9, 0, 0.5), (-0.58, 0, 0.42)], [0.065] * 5, mat("손잡이", (0.98, 0.6, 0.45), 0.5))
knob = ball(0.11, mat("꼭지", (0.98, 0.72, 0.3), 0.5), loc=(0, 0, H + 0.08))
lid = cyl(0.42, 0.06, mat("뚜껑", (0.98, 0.72, 0.3), 0.5), loc=(0, 0, H), bevel=0.02)
ring_m = mat("단면", (1.0, 0.45, 0.08), 0.5, emit=2.5)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03); ring = put(bpy.context.object, ring_m)
PIV = Vector((0.55, 0, 0))
pivot = empty("기울기", loc=PIV); bpy.context.view_layer.update()
for o in (body, spout, handle, knob, lid):
    o.parent = pivot; o.matrix_parent_inverse = pivot.matrix_world.inverted()
bowl = cyl(0.22, 0.1, mat("그릇", (0.95, 0.5, 0.55), 0.5), loc=(1.9, 0, 0.05), bevel=0.03)
water_m = mat("물", (0.3, 0.6, 0.95), 0.2)
drops = [ball(0.05, water_m, loc=(0, 0, -1)) for _ in range(5)]
cat = 고양이("고양이", (2.5, -0.05, 0)); cat[0].rotation_euler.z = math.pi

cams = {"front": camera("front", (0.5, -6.2, 1.3), (0.5, 0, 1.2), 25),
        "close": camera("close", (0.2, -3.8, 1.5), (0, 0, 1.0), 26),
        "low": camera("low", (1.6, -2.4, 0.25), (0, 0, 1.0), 21),
        "top": camera("top", (-1.4, -3.2, 4.0), (0.2, 0, 0.9), 24),
        "orbit": camera("orbit", (0.3, -6.0, 1.5), (0.2, 0, 1.0), 25),
        "catcam": camera("catcam", (3.2, -1.6, 0.6), (1.6, 0, 0.5), 24)}

def u_(li, a, b, fr): return T.u(li, a, b, fr) if fr >= T.lines[li][0] else 0.0
TH = 0.55
for fr in range(1, T.end + 1):
    b = u_(1, 0.05, 0.85, fr) if fr >= T.lines[1][0] else 0.0
    if fr < T.lines[1][0]: b = 0.0
    s = u_(2, 0.05, 0.85, fr); h = u_(3, 0.05, 0.85, fr)
    if fr < T.lines[1][0]:                       # 0줄: 완성된 포트를 먼저 보여 줌
        b = s = h = 1.0
    bcu.bevel_factor_end = max(b, 0.001); scu.bevel_factor_end = max(s, 0.001); hcu.bevel_factor_end = max(h, 0.001)
    for c in (bcu, scu, hcu): c.keyframe_insert("bevel_factor_end", frame=fr)
    for o, v in ((body, b), (spout, s), (handle, h), (knob, b), (lid, b)):
        o.hide_render = v < 0.01; o.keyframe_insert("hide_render", frame=fr)
    knob.hide_render = lid.hide_render = b < 0.99; knob.keyframe_insert("hide_render", frame=fr); lid.keyframe_insert("hide_render", frame=fr)
    # 단면 고리: 몸통을 쓰는 동안 축을 따라 올라감
    z = H * b; rr = 0.5
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if z0 <= z <= z1: rr = r0 + (r1 - r0) * (z - z0) / max(1e-6, z1 - z0)
    ring.location = (0, 0, z); ring.scale = (rr + 0.04, rr + 0.04, 1); ring.hide_render = not (T.lines[1][0] <= fr and 0 < b < 1)
    ring.keyframe_insert("location", frame=fr); ring.keyframe_insert("scale", frame=fr); ring.keyframe_insert("hide_render", frame=fr)
    # 5줄: 포트가 기울어 그릇에 물방울
    t = u_(5, 0.05, 0.35, fr) * (1 - u_(5, 0.85, 1.0, fr))
    pivot.rotation_euler.y = TH * t; pivot.keyframe_insert("rotation_euler", frame=fr)
    tip = Vector((1.18, 0, 1.5)) - PIV; c, sn = math.cos(TH), math.sin(TH)
    tipw = PIV + Vector((tip.x * c + tip.z * sn, 0, -tip.x * sn + tip.z * c))
    for k, d in enumerate(drops):
        ph = (fr - T.lines[5][0]) / 8.0 - k * 0.6 if fr >= T.lines[5][0] else -1
        on = t > 0.95 and ph > 0
        f = ph % 1.0
        d.location = tipw.lerp(Vector((1.9, 0, 0.1)), f) + Vector((0, 0, 0.25 * math.sin(math.pi * f) * 0)) if on else Vector((0, 0, -1))
        d.keyframe_insert("location", frame=fr)
    lap = t > 0.95
    cat[1].rotation_euler = (0, 0.5 + 0.15 * math.sin(fr) if lap else -0.4, 0 if lap else 0.3 * math.sin(fr / 12)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    oc, _ = cams["orbit"]; v = u_(4, 0, 1, fr)
    ang = math.radians(-90 + 70 * v); oc.location = (6.0 * math.cos(ang), 6.0 * math.sin(ang), 1.5 + 1.0 * v); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.4 + 1.2 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
