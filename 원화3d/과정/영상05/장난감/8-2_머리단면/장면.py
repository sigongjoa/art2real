"""8-2 머리 단면 — Bridgman 1920 p214. 흰 책장 앞에 머리 상자 다섯이 각도를 바꿔 뜬다 · 가운데 머리의 면이 색으로 켜지고 · 빛 판이 내려와 자르면 단면은 동그라미가 아니라 각진 꼴."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def clean(m):
    m.show_transparent_back = False; m.use_backface_culling = True; m.shadow_method = "HASHED"; return m

# 위에서 본 머리 꼴: 앞은 판판 · 앞 모서리 꺾임 · 뒤는 둥긂
P = [(-0.21, -0.36), (0.21, -0.36), (0.31, -0.2), (0.31, 0.2), (0.2, 0.36), (-0.2, 0.36), (-0.31, 0.2), (-0.31, -0.2)]
EDGE_MAT = [0, 1, 2, 2, 2, 2, 2, 1]          # 0 앞면 · 1 볼(꺾임) · 2 옆 · 뒤 ; 3 단면 · 4 위아래 뚜껑
def prism(name, z0, z1, mats, cap_top, cap_bot, parent):
    n = len(P); v = [(x, y, z0) for x, y in P] + [(x, y, z1) for x, y in P]
    f = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    for m in mats: me.materials.append(m)
    for i, p in enumerate(me.polygons): p.material_index = EDGE_MAT[i] if i < n else (cap_bot if i == n else cap_top)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.parent = parent
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments, b.limit_method = 0.012, 2, "ANGLE"
    return o

skin, dark = mat("살", (0.98, 0.78, 0.65), 0.7), mat("눈", (0.06, 0.05, 0.06), 0.3)
lav = mat("상자", (0.74, 0.76, 0.97), 0.6)
cut = mat("단면", (1.0, 0.42, 0.35), 0.5, emit=0.6)
cm = [mat("앞", (0.74, 0.76, 0.97), 0.6), mat("볼", (0.74, 0.76, 0.97), 0.6), mat("옆", (0.74, 0.76, 0.97), 0.6)]
def head(name, loc, center=False):
    R = empty(name, loc=loc); ms = (cm if center else [lav] * 3) + [cut, lav]
    lo = prism(name + "아래", -0.4, 0.0, ms, 3, 4, R)
    U = empty(name + "윗", R); up = prism(name + "위", 0.0, 0.42, ms, 4, 3, U)
    box((0.34, 0.07, 0.05), skin, U, (0, -0.38, 0.14), bevel=0.015)
    for s in (-1, 1): ball(0.035, dark, U, (s * 0.11, -0.36, 0.06))
    me = bpy.data.meshes.new("코"); me.from_pydata([(0, 0, -0.01), (-0.06, 0, -0.2), (0.06, 0, -0.2), (0, -0.13, -0.2)], [], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
    n = bpy.data.objects.new("코", me); bpy.context.scene.collection.objects.link(n); put(n, skin, R, (0, -0.36, 0))
    box((0.22, 0.1, 0.1), skin, R, (0, -0.37, -0.33), bevel=0.02)
    return R, U

board = mat("책장", (1, 0.99, 0.95), 1.0, emit=1.45)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, board, loc=(0, 0.75, 2.2)).scale = (2.7, 4.7, 1)
S = 0.8
spots = [(-0.62, 3.25), (0.62, 3.25), (0, 2.2), (-0.62, 1.15), (0.62, 1.15)]
poses = [(0, 0, 0.6), (0.25, 0, -0.5), (0, 0, -0.35), (-0.3, 0, 0.9), (0, 0.2, -1.2)]
heads = [head("머리%d" % i, (x, 0, z), i == 2) for i, (x, z) in enumerate(spots)]
for R, _ in heads: R.scale = (S, S, S)
C, CU = heads[2]

ring = bpy.ops.mesh.primitive_torus_add(major_radius=0.37 * S, minor_radius=0.012, major_segments=64)
ring = put(bpy.context.object, mat("동그라미", (1.0, 0.85, 0.2), 0.5, emit=3.0), loc=(0, 0, 2.2 + 0.01))
blade_m = clean(mat("칼", (0.5, 0.9, 1.0), 0.3, emit=2.0, alpha=True)); bla = alpha_of(blade_m)
blade = box((1.0, 1.0, 0.012), blade_m, loc=(0, 0, 3))

cams = {"front": camera("front", (0, -3.0, 2.2), (0, 0, 2.2), 30),
        "close": camera("close", (0.35, -1.75, 2.35), (0, 0, 2.2), 35),
        "side": camera("side", (2.3, -2.6, 2.6), (0, 0, 2.2), 30),
        "low": camera("low", (0.5, -1.6, 1.6), (0, 0, 2.3), 30),
        "top": camera("top", (0, -0.4, 3.7), (0, 0, 2.2), 35),
        "top2": camera("top2", (1.0, -1.25, 3.25), (0.35, 0, 2.25), 32),
        "orbit": camera("orbit", (0, -2.0, 2.3), (0, 0, 2.2), 35)}
cols = [(1.0, 0.55, 0.45), (1.0, 0.85, 0.35), (0.45, 0.85, 0.6)]

for fr in range(1, T.end + 1):
    t = fr / 24
    for i, (R, U) in enumerate(heads):
        k = 1.0 if i == 2 else T.u(1, 0.05 + 0.13 * i, 0.25 + 0.13 * i, fr)
        if i != 2: k *= 1 - T.u(4, 0, 0.3, fr)          # 자르기 전에 나머지는 물러난다
        R.scale = Vector((S, S, S)) * max(0.001, k * (1 + 0.2 * math.sin(math.pi * min(k, 1))))
        px, py, pz = poses[i]; w = T.u(1, 0.1 + 0.13 * i, 0.4 + 0.13 * i, fr) * (1 - T.u(6, 0, 0.3, fr) if i == 2 else 1)
        R.rotation_euler = (px * w, py * w, pz * w + 0.12 * math.sin(t * 1.5 + i))
        if i == 2: R.rotation_euler.z = pz * w + (1 - T.u(1, 0, 0.3, fr)) * 0.6 * math.sin(t * 2) + 2 * math.pi * T.u(6, 0.2, 1, fr)
        key(R, fr, "scale", "rotation_euler")
    # 3 줄: 앞면 → 볼 → 옆면 색이 켜진다
    for j, m in enumerate(cm):
        k = T.u(3, 0.05 + 0.28 * j, 0.25 + 0.28 * j, fr)
        c = [0.74 + (cols[j][0] - 0.74) * k, 0.76 + (cols[j][1] - 0.76) * k, 0.97 + (cols[j][2] - 0.97) * k, 1]
        p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Base Color"].default_value = c
        p.inputs["Base Color"].keyframe_insert("default_value", frame=fr)
    # 4 줄: 칼판이 내려와 자르고 윗덩이가 옆으로 비킨다 · 6 줄에 다시 붙는다
    d = T.u(4, 0.1, 0.5, fr); blade.location.z = 3.2 - 1.0 * d; key(blade, fr, "location")
    bla.default_value = 0.6 * T.u(4, 0, 0.1, fr) * (1 - T.u(4, 0.55, 0.7, fr)); bla.keyframe_insert("default_value", frame=fr)
    lift = T.u(4, 0.5, 0.95, fr) * (1 - T.u(6, 0, 0.35, fr))
    CU.location = (1.5 * lift, 0.3 * lift, 0.5 * math.sin(math.pi * min(1, lift)) + 0.1 * lift); CU.rotation_euler = (0, -0.5 * lift, 0); key(CU, fr, "location", "rotation_euler")
    # 5 줄: 짐작한 동그라미가 깜빡이다 사라진다
    on = T.lines[4][0] + (T.lines[4][1] - T.lines[4][0]) * 0.8 <= fr < T.lines[5][0] + (T.lines[5][1] - T.lines[5][0]) * 0.5
    ring.hide_render = not on or (fr // 3) % 3 == 0; ring.keyframe_insert("hide_render", frame=fr)
    oc, _ = cams["orbit"]; a = math.radians(-90 + 50 * math.sin(t * 0.5)); oc.location = (2.0 * math.cos(a), 2.0 * math.sin(a), 2.4); key(oc, fr, "location")
    tc, _ = cams["top"]; tc.location.z = 3.7 - 0.25 * T.u(5, 0, 1, fr); key(tc, fr, "location")
    fc, _ = cams["front"]; fc.location.y = -3.0 + 0.3 * math.sin(t * 0.7) + 0.9 * T.u(4, 0, 0.6, fr) * (1 - T.u(6, 0, 0.3, fr)); key(fc, fr, "location")
끝(T, cams)
