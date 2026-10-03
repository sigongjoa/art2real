"""10-4 손가락 단면 — 큰 장난감 손가락 옆에서 단면 고리 셋(넓적 → 둥긂 → 동그람)이 하나씩 떠오르고, 이어 붙으면 살이 채워져 손가락이 되고 까딱인다(Bridgman, Hundred Hands p.113)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
SEC = [(0.3, 0.24, 0.16, 4.0), (0.85, 0.19, 0.155, 2.8), (1.3, 0.15, 0.14, 2.0)]   # (높이, 반폭, 반두께, 지수)
def sec_at(z):
    if z <= SEC[0][0]: return SEC[0][1:]
    for s0, s1 in zip(SEC, SEC[1:]):
        if z <= s1[0]: u = (z - s0[0]) / (s1[0] - s0[0]); return tuple(a + (b - a) * u for a, b in zip(s0[1:], s1[1:]))
    return SEC[-1][1:]
def se(a, b, n, t):          # 초타원 한 점
    c, s = math.cos(t), math.sin(t)
    return a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s)
NA, NZ, Z0, Z1 = 48, 14, 0.05, 1.3
skin = mat("살", (0.98, 0.76, 0.6), 0.6, alpha=True); sa = alpha_of(skin); skin.show_transparent_back = False
def seg(z0, z1, parent, pivot):          # 마디 하나: z0..z1 로프트(피벗 기준 지역 좌표)
    me = bpy.data.meshes.new("마디"); bm = bmesh.new(); rows = []
    for j in range(NZ + 1):
        z = z0 + (z1 - z0) * j / NZ; a, b, n = sec_at(z)
        k = 0.94 + 0.06 * math.sin(math.pi * j / NZ)                 # 마디 가운데가 살짝 불룩 → 관절 자리가 잘록
        rows.append([bm.verts.new((*(v * k for v in se(a, b, n, 2 * math.pi * i / NA)), z - pivot)) for i in range(NA)])
    for j in range(NZ):
        for i in range(NA): bm.faces.new([rows[j][i], rows[j][(i + 1) % NA], rows[j + 1][(i + 1) % NA], rows[j + 1][i]])
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1]); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new("마디", me); bpy.context.scene.collection.objects.link(o); me.materials.append(skin); o.parent = parent; return o
finger = empty("손가락축", loc=(0, 0, Z0))
j1 = empty("관절1", finger, (0, 0, 0.5 - Z0)); j2 = empty("관절2", j1, (0, 0, 0.42))
segs = [seg(Z0, 0.5, finger, Z0), seg(0.5, 0.92, j1, 0.5), seg(0.92, Z1, j2, 0.92)]
fo = segs[0]
tip = ball(0.145, skin, j2, (0, 0, Z1 - 0.92), scale=(1, 0.97, 0.9))
nail = ball(0.1, mat("손톱", (1.0, 0.88, 0.9), 0.25, alpha=True), j2, (0, -0.1, Z1 - 0.95), scale=(1, 0.45, 1.3)); na = alpha_of(nail.data.materials[0])

COLS = [(1.0, 0.45, 0.45), (1.0, 0.75, 0.3), (0.35, 0.75, 1.0)]
rings = []
for k, (z, a, b, n) in enumerate(SEC):
    cu = bpy.data.curves.new("고리%d" % k, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.024; cu.bevel_resolution = 3
    sp = cu.splines.new("POLY"); sp.points.add(NA - 1); sp.use_cyclic_u = True
    for i in range(NA): x, y = se(a + 0.01, b + 0.01, n, 2 * math.pi * i / NA); sp.points[i].co = (x, y, 0, 1)
    r = bpy.data.objects.new("고리%d" % k, cu); bpy.context.scene.collection.objects.link(r); cu.materials.append(mat("고리색%d" % k, COLS[k], 0.4, emit=0.7))
    rings.append((r, z))
SIDE = Vector((-0.75, -0.2, 0))                                                      # 처음엔 옆에 떠 있음

cat = 고양이("고양이", (0.6, 0.15, 0)); cat[0].rotation_euler.z = math.pi - 0.3
cams = {"front": camera("front", (0, -3.2, 0.7), (-0.25, 0, 0.75), 36),
        "close": camera("close", (-0.6, -1.9, 1.3), (-0.5, 0, 0.7), 34),
        "side": camera("side", (1.2, -2.3, 0.9), (-0.2, 0, 0.75), 34),
        "wide": camera("wide", (0, -3.6, 0.45), (-0.2, 0, 0.8), 30),
        "low": camera("low", (0.9, -1.8, 0.2), (0.2, 0, 0.7), 26)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    join = g(4, 0.05, 0.6)
    for k, (r, z) in enumerate(rings):
        u = g(k + 1, 0.05, 0.4); s = max(1e-3, u * (1 + 0.3 * math.sin(math.pi * u)) * (1 - g(5, 0.05, 0.25)))
        stack_z = 0.5 + 0.35 * k
        r.location = (SIDE * (1 - join)) + Vector((0, 0, stack_z + (z - stack_z) * join))
        r.rotation_euler = (0.5 * (1 - join) * (1 - g(0, 0, 1) * 0), 0, 0.4 * math.sin(fr / 25) * (1 - join))
        r.scale = (s, s, s); r.keyframe_insert("location", frame=fr); r.keyframe_insert("rotation_euler", frame=fr); r.keyframe_insert("scale", frame=fr)
    # 손가락 살: 처음엔 희미(줄 0 은 보이게), 단면 설명 동안 숨김, 이으면 차오름
    vis = (1 - g(1, 0, 0.3)) + g(4, 0.5, 1.0)
    sa.default_value = min(1, vis); sa.keyframe_insert("default_value", frame=fr); na.default_value = min(1, vis); na.keyframe_insert("default_value", frame=fr)
    for o in segs + [tip, nail]: o.hide_render = vis < 0.02; o.keyframe_insert("hide_render", frame=fr)
    bend = 0.35 * math.sin(math.pi * g(5, 0.2, 0.9)) + 0.25 * math.sin(math.pi * 2 * g(6, 0.1, 0.9))
    for jt in (j1, j2): jt.rotation_euler.x = -bend * 1.3; jt.keyframe_insert("rotation_euler", frame=fr)
    finger.rotation_euler.x = -bend * 0.4; finger.keyframe_insert("rotation_euler", frame=fr)
    hop = 0.2 * math.sin(math.pi * g(5, 0.2, 0.5))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.7, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
