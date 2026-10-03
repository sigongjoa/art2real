"""10-3 어깨 · 가슴 단면 — 팔 달린 덩어리 몸통을 빛 칼날 둘이 가른다. 가슴 높이 단면은 세 조각(몸통 + 팔 둘), 어깨 높이는 한 덩어리 · 두 단면이 떠올라 카메라를 향한다(Vanderpoel p.93)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
Z0 = 0.5
KEY = [(0.0, 0.29, 0.2), (0.3, 0.25, 0.17), (0.6, 0.31, 0.22), (0.85, 0.36, 0.2), (1.0, 0.3, 0.15)]
def ab(z):
    for (z0, a0, b0), (z1, a1, b1) in zip(KEY, KEY[1:]):
        if z <= z1: u = ease((z - z0) / (z1 - z0)); return a0 + (a1 - a0) * u, b0 + (b1 - b0) * u
    return KEY[-1][1:]
NA, NZ = 48, 40
me = bpy.data.meshes.new("몸통"); bm = bmesh.new(); rows = []
for j in range(NZ + 1):
    z = j / NZ; a, b = ab(z)
    rows.append([bm.verts.new((a * math.cos(2 * math.pi * i / NA), b * math.sin(2 * math.pi * i / NA), Z0 + z)) for i in range(NA)])
for j in range(NZ):
    for i in range(NA): bm.faces.new([rows[j][i], rows[j][(i + 1) % NA], rows[j + 1][(i + 1) % NA], rows[j + 1][i]])
bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1]); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
skin = mat("살", (0.98, 0.78, 0.62), 0.6)
torso = bpy.data.objects.new("몸통", me); bpy.context.scene.collection.objects.link(torso); me.materials.append(skin)
AX, AR, DR = 0.42, 0.075, 0.11
for s in (-1, 1):
    ball(DR, skin, loc=(s * 0.36, 0, Z0 + 0.84)); cyl(AR, 0.6, skin, loc=(s * AX, 0, Z0 + 0.5))
stand = mat("받침", (0.6, 0.45, 0.32), 0.8); cyl(0.04, Z0, stand, loc=(0, 0, Z0 / 2)); cyl(0.25, 0.04, stand, loc=(0, 0, 0.02), bevel=0.015)

def outline(shapes, n=96):         # 원점에서 본 합집합 윤곽(별 모양 가정) — 각도마다 마지막 안쪽 점
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n; c, s_ = math.cos(t), math.sin(t); last = 0
        for k in range(1, 400):
            r = k * 0.002; x, y = r * c, r * s_
            if any(f(x, y) for f in shapes): last = r
        pts.append((last * c, last * s_))
    return pts
def ring(pts, m, parent, pad=0.012):
    cu = bpy.data.curves.new("고리", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.02; cu.bevel_resolution = 3
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1); sp.use_cyclic_u = True
    for i, (x, y) in enumerate(pts):
        l = math.hypot(x, y) or 1; sp.points[i].co = (x + pad * x / l, y + pad * y / l, 0, 1)
    o = bpy.data.objects.new("고리", cu); bpy.context.scene.collection.objects.link(o); cu.materials.append(m); o.parent = parent; return o
ell = lambda a, b: (lambda x, y: (x / a) ** 2 + (y / b) ** 2 <= 1)
circ = lambda cx, r: (lambda x, y: (x - cx) ** 2 + y ** 2 <= r * r)
red, blue = mat("가슴선", (1.0, 0.45, 0.4), 0.4, emit=0.8), mat("어깨선", (0.3, 0.7, 1.0), 0.4, emit=0.8)
HC, HS = 0.6, 0.86
chest = empty("가슴단면", loc=(0, 0, Z0 + HC)); shoulder = empty("어깨단면", loc=(0, 0, Z0 + HS))
a, b = ab(HC); ring(outline([ell(a, b)]), red, chest)
for s in (-1, 1): ring([(s * AX + AR * math.cos(2 * math.pi * i / 48), AR * math.sin(2 * math.pi * i / 48)) for i in range(48)], red, chest, pad=0)
a, b = ab(HS); dz = HS - 0.84; rr = math.sqrt(max(DR * DR - dz * dz, 0))
ring(outline([ell(a, b), circ(0.36, rr), circ(-0.36, rr)]), blue, shoulder)
blade_m = mat("칼날", (1.0, 0.95, 0.6), 0.4, emit=2.0, alpha=True); alpha_of(blade_m).default_value = 0.35
blade = box((1.4, 1.0, 0.006), blade_m, loc=(0, 0, 3))

cat = 고양이("고양이", (-0.95, -0.5, 0)); cat[0].rotation_euler.z = 0.4
cams = {"front": camera("front", (0, -3.2, 1.0), (0, 0, 1.0), 36),
        "close": camera("close", (0.4, -1.9, 1.7), (0, 0, 1.2), 34),
        "side": camera("side", (1.4, -1.9, 1.5), (0, 0, 1.1), 34),
        "lift": camera("lift", (0, -3.1, 1.35), (0, -1.0, 1.3), 40),
        "wide": camera("wide", (0, -3.7, 0.5), (0, 0, 1.1), 30),
        "low": camera("low", (-0.6, -2.2, 0.25), (-0.3, 0, 0.8), 26)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    c1, c2 = g(1, 0.05, 0.7), g(3, 0.05, 0.7)
    if 0 < c2: z = 2.0 - (2.0 - Z0 - HS) * c2; on = c2 < 1
    elif 0 < c1: z = 2.0 - (2.0 - Z0 - HC) * c1; on = c1 < 1
    else: z, on = 3.0, False
    blade.location.z = z; blade.hide_render = not on; blade.keyframe_insert("location", frame=fr); blade.keyframe_insert("hide_render", frame=fr)
    for e, i, top in ((chest, 1, 1.05), (shoulder, 3, 1.6)):
        u = g(i, 0.65, 0.85); s = max(1e-3, u * (1 + 0.25 * math.sin(math.pi * u)))
        lf = g(5, 0.0, 0.6) * (1 - g(6, 0.5, 0.95)); base = Z0 + (HC if e is chest else HS)
        e.location = (0, -1.1 * lf, base + (top - base) * lf); e.rotation_euler.x = (math.pi / 2) * lf
        e.scale = (s, s, s); e.keyframe_insert("location", frame=fr); e.keyframe_insert("rotation_euler", frame=fr); e.keyframe_insert("scale", frame=fr)
    hop = 0.2 * math.sin(math.pi * g(2, 0.1, 0.35)) + 0.2 * math.sin(math.pi * g(4, 0.1, 0.35))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.7, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
