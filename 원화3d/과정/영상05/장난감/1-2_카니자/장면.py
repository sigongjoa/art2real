"""1-2 카니자 삼각형 — 이 빠진 원반 셋이 흰 판 앞에 떠 있다. 고양이가 「삼각형」 밑변에 올라섰다가 빠진다 · 옆에서 보면 원반뿐."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
# 흰 판(빛 영향 없이 고른 흰색 — 착시는 바탕이 고와야 선다)
board = mat("판", (1, 1, 1), 1.0, emit=1.45)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, board, loc=(0, 1.2, 1.7)).scale = (3.6, 3.4, 1)

# 이 빠진 원반: 꼭짓점마다 60° 홈이 가운데를 본다
C, R, r = Vector((0, 0, 1.25)), 0.85, 0.3
black = mat("원반", (0.02, 0.02, 0.025), 0.5)
verts = []
for a in (90, 210, 330):
    v = C + Vector((math.cos(math.radians(a)), 0, math.sin(math.radians(a)))) * R; verts.append(v)
    to_c = math.degrees(math.atan2((C - v).z, (C - v).x))
    me = bpy.data.meshes.new("pac"); bm = bmesh.new(); c0 = bm.verts.new((0, 0, 0))
    arc = [bm.verts.new((r * math.cos(math.radians(to_c + 30 + 300 * k / 60)), r * math.sin(math.radians(to_c + 30 + 300 * k / 60)), 0)) for k in range(61)]
    bm.faces.new([c0] + arc); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("원반", me); bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (math.pi / 2, 0, 0); o.location = v
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.04
    o.data.materials.append(black)

# 뇌가 이은 모서리 — 빛나는 가는 막대, 6 번째 줄에서 나타남
glow = mat("윤곽", (1.0, 0.45, 0.08), 0.5, emit=2.0, alpha=True); ga = alpha_of(glow)
edges = [bar(verts[i] + Vector((0, -0.03, 0)), verts[(i + 1) % 3] + Vector((0, -0.03, 0)), 0.022, glow) for i in range(3)]

cat = 고양이("고양이", (-2.6, -0.1, 0))
base_z = C.z - R / 2                          # 밑변 높이
cams = {"front": camera("front", (0, -4.2, 1.2), (0, 0, 1.15), 35),
        "close": camera("close", (0, -3.0, 1.2), (0, 0, 1.15), 30),
        "low": camera("low", (1.3, -2.2, 0.25), (-0.4, 0, 0.7), 26),
        "catcam": camera("catcam", (-1.7, -1.2, 0.55), (0, 0, 0.9), 26),
        "fall": camera("fall", (0.8, -1.9, 0.45), (0, -0.1, 0.5), 26),
        "orbit": camera("orbit", (0, -4.2, 1.2), (0, 0.1, 1.15), 30)}

for fr in range(1, T.end + 1):
    x, z, spin, walk = -2.6, 0.0, 0.0, False
    if fr >= T.lines[1][0]:
        u = T.u(1, 0, 0.75, fr); x = -2.6 + (2.6 - 0.55) * u; walk = 0 < u < 1
    if fr >= T.lines[2][0]:
        crouch = T.u(2, 0, 0.3, fr) * (1 - T.u(2, 0.3, 0.4, fr)); j = T.u(2, 0.35, 0.95, fr)
        x = -0.55 + 0.55 * j; z = -0.05 * crouch + base_z * j + 0.35 * math.sin(math.pi * j)
    if fr >= T.lines[3][0]:
        d = T.u(3, 0.2, 0.45, fr); x = 0.0; z = base_z * (1 - d * d); spin = 1.6 * d
        z += 0.08 * math.sin(math.pi * T.u(3, 0.45, 0.6, fr))          # 콩
    root = cat[0]; root.location = (x, -0.1, max(z, 0)); root.rotation_euler.x = spin * (1 - T.u(3, 0.6, 0.8, fr) if fr >= T.lines[3][0] else 1)
    root.keyframe_insert("location", frame=fr); root.keyframe_insert("rotation_euler", frame=fr)
    look_up = T.u(1, 0.75, 0.95, fr) * (1 - T.u(2, 0.3, 0.4, fr)) if fr >= T.lines[1][0] else 0
    cat[1].rotation_euler = (0, -0.6 * look_up, 0.5 * math.sin(fr / 9) * T.u(4, 0, 0.2, fr) if fr >= T.lines[4][0] else 0)
    cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    oc, ot = cams["orbit"]; u = T.u(4, 0, 0.7, fr) if fr >= T.lines[4][0] else 0
    a = math.radians(-90 + 72 * u); dist = 4.2 - 0.6 * u
    oc.location = (dist * math.cos(a), dist * math.sin(a), 1.2 + 0.3 * u); oc.keyframe_insert("location", frame=fr)
    ga.default_value = 0.9 * T.u(5, 0.1, 0.6, fr) if fr >= T.lines[5][0] else 0.0; ga.keyframe_insert("default_value", frame=fr)
    for e in edges: e.hide_render = fr < T.lines[5][0]; e.keyframe_insert("hide_render", frame=fr)
끝(T, cams)
