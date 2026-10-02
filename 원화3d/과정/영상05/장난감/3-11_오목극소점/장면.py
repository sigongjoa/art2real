"""3-11 오목 극소점 — 구불 판 윤곽의 파인 점마다 빨간 점 · 빛 칼날이 마주 보는 점끼리 내리쳐 다섯 조각으로 벌어진다."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
L, LAM = 1.25, 0.5
w = lambda x: 0.27 + 0.12 * math.cos(2 * math.pi * x / LAM)
zc = lambda x: 1.15 + 0.12 * math.sin(2 * math.pi * x / 1.0)
cols = [(0.95, 0.55, 0.5), (0.98, 0.78, 0.45), (0.6, 0.82, 0.55), (0.5, 0.72, 0.95), (0.78, 0.6, 0.92)]
plate_m = mat("판", (0.98, 0.8, 0.5), 0.6)
post_m = mat("막대", (0.6, 0.42, 0.26), 0.8)
pieces = []
for k in range(5):
    x0, x1 = -L + 0.5 * k, -L + 0.5 * (k + 1); xm = (x0 + x1) / 2
    xs = [x0 + (x1 - x0) * i / 40 for i in range(41)]
    me = bpy.data.meshes.new("조각"); bm = bmesh.new()
    vs = [bm.verts.new((x - xm, 0, zc(x) + w(x))) for x in xs] + [bm.verts.new((x - xm, 0, zc(x) - w(x))) for x in reversed(xs)]
    bm.faces.new(vs); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("조각", me); bpy.context.scene.collection.objects.link(o); o.location = (xm, 0, 0)
    o.data.materials.append(plate_m); s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.12; s.offset = 0
    bv = o.modifiers.new("둥글게", "BEVEL"); bv.width = 0.015; bv.segments = 2; bv.limit_method = "ANGLE"
    zb = zc(xm) - w(xm); cyl(0.03, zb, post_m, o, (0, 0.0, zb / 2))
    pieces.append((o, xm))
red = mat("빨강", (1, 0.15, 0.12), 0.4, emit=1.5)
pinch = [-L + 0.5 * k for k in range(1, 5)]
dots = [ball(0.045, red, loc=(x, -0.075, zc(x) + s * w(x))) for x in pinch for s in (-1, 1)]
blade_m = mat("칼날", (1, 0.85, 0.4), 0.3, emit=1.5)
blades = [box((0.02, 0.2, 0.5), blade_m, loc=(x, 0, 3.0)) for x in pinch]
cat = 고양이("고양이", (-1.3, -0.7, 0)); cat[0].rotation_euler.z = 0.4

cams = {"front": camera("front", (0, -3.4, 1.0), (0, 0, 1.0), 28),
        "close": camera("close", (-0.4, -2.4, 1.3), (-0.35, 0, 1.1), 30),
        "low": camera("low", (0.6, -2.0, 0.3), (0.2, 0, 1.0), 24),
        "side": camera("side", (2.6, -2.8, 1.6), (0, 0, 1.0), 28),
        "wide": camera("wide", (0, -5.0, 1.8), (0, 0, 1.0), 28)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    for j, o in enumerate(dots):
        u = on(1, 0.05 + 0.1 * (j // 2), 0.25 + 0.1 * (j // 2)); pul = 1 + 0.3 * math.sin(fr / 2.2) * on(2)
        o.scale = [max(u * pul * (1 - on(4, 0, 0.2)), 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    for j, (b, x) in enumerate(zip(blades, pinch)):
        u = on(3, 0.05 + 0.18 * j, 0.3 + 0.18 * j)
        b.location.z = 3.0 - (3.0 - zc(x)) * u if u < 1 else zc(x) + 2.2 * on(4, 0.0, 0.3)
        b.keyframe_insert("location", frame=fr)
        b.hide_render = not (T.lines[3][0] <= fr < T.lines[4][0] + 8); b.keyframe_insert("hide_render", frame=fr)
    spread = on(4, 0.1, 0.6)
    for j, (o, xm) in enumerate(pieces):
        o.location.x = xm * (1 + 0.32 * spread); o.location.z = 0.1 * math.sin(math.pi * on(4, 0.1, 0.6))
        o.rotation_euler.y = 0.12 * math.sin(math.pi * on(4, 0.1, 0.8)) * (1 if j % 2 else -1) + 0.04 * math.sin(fr / 7 + j) * on(5)
        o.keyframe_insert("location", frame=fr); o.keyframe_insert("rotation_euler", frame=fr)
    hop = abs(math.sin(math.pi * 2 * on(4, 0.1, 0.5)))
    cat[0].location = (-1.3 + 0.45 * on(0, 0.1, 0.9), -0.7, 0.2 * hop); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.6, 0.35 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.1, 0.9) < 1)
끝(T, cams)
