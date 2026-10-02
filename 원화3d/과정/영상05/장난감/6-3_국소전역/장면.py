"""6-3 국소/전역 완성 후보(Thielen 그림2) — 남색 네모 뒤 원판. 네모가 반투명해지면 뒤 모양이 넷으로 바뀐다: 원(전역) · 뾰족(국소) · 잘림 · 혹. 보이는 부분은 늘 같다."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 0.3, 1.5)).scale = (3.8, 3.0, 1)
CX, CZ, R, EDGE = -0.45, 1.5, 0.8, 0.05                  # 원판 중심 · 반지름 · 네모 왼쪽 변 x
th0 = math.acos((EDGE - CX) / R)                         # 네모 변에 닿는 각
arc = lambda a0, a1, n=64: [(CX + R * math.cos(a0 + (a1 - a0) * i / n), CZ + R * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
tip = CX + R / math.cos(th0)
def bump(a): return R + 0.32 * math.exp(-(a / 0.35) ** 2)
outlines = [arc(0, 2 * math.pi)[:-1],                                            # 원(전역)
            arc(th0, 2 * math.pi - th0) + [(tip, CZ)],                           # 뾰족(국소)
            arc(math.acos(0.8), 2 * math.pi - math.acos(0.8)),                 # 잘림
            [(CX + bump(a) * math.cos(a), CZ + bump(a) * math.sin(a)) for a in [(-math.pi + 2 * math.pi * i / 96) for i in range(96)]]]
org = mat("원판", (1.0, 0.5, 0.15), 0.7)
cands = []
for k, pts in enumerate(outlines):
    me = bpy.data.meshes.new("c%d" % k); bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, 0, z)) for x, z in pts]); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("후보%d" % k, me); bpy.context.scene.collection.objects.link(o)
    o.location.y = 0.15; o.modifiers.new("두께", "SOLIDIFY").thickness = 0.06; me.materials.append(org); cands.append(o)
sq_m = mat("네모", (0.18, 0.24, 0.5), 0.7, alpha=True); sa = alpha_of(sq_m)
sq = box((1.5, 0.05, 2.0), sq_m, loc=(EDGE + 0.75, -0.05, 1.5), bevel=0.02)

cat = 고양이("고양이", (-1.3, -0.9, 0)); cat[0].scale = (1.5, 1.5, 1.5); cat[0].rotation_euler.z = 0.3
cams = {"front": camera("front", (0, -4.1, 1.4), (0, 0, 1.4), 28),
        "close": camera("close", (0.1, -2.9, 1.5), (0.1, 0, 1.5), 26),
        "low": camera("low", (-0.3, -3.0, 0.3), (0, 0, 1.4), 22),
        "glass": camera("glass", (0.8, -3.3, 1.7), (0.2, 0, 1.5), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    see = T.u(2, 0, 0.3, fr) * (1 - T.u(6, 0, 0.4, fr))                 # 네모 반투명
    sa.default_value = 1 - 0.7 * see; sa.keyframe_insert("default_value", frame=fr)
    if fr < T.lines[3][0]: k = (fr // 14) % 4 if fr >= T.lines[2][0] + 8 else 0      # 후보를 차례로
    elif fr < T.lines[4][0]: k = 1
    elif fr < T.lines[5][0]: k = 0
    elif fr < T.lines[6][0]: k = (fr // 12) % 4
    else: k = 2
    for i, o in enumerate(cands): o.hide_render = i != k; o.keyframe_insert("hide_render", frame=fr)
    cat[1].rotation_euler = (0.4 * see * math.sin(fr / 5), -0.45, 0.3 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.x = -1.3 + 0.25 * math.sin(fr / 40); cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, abs(math.cos(fr / 40)) > 0.3)
    for kk, (cm, _) in cams.items():
        p = base[kk].copy(); p.x += 0.2 * math.sin(fr / 37 + len(kk)); p.y += 0.25 * math.sin(fr / 47)
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
