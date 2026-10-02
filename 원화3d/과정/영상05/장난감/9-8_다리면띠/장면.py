"""9-8 다리 면 · 띠 — Vanderpoel 1907 p138. 큰 다리 조각상(허벅지 팔각 기둥 → 무릎 상자 → 앞이 모난 정강이)이 돈다 · 앞 · 옆 · 뒤 면에 색 · 빛 판이 위에서 아래로 훑으며 지나간 자리마다 단면 띠가 켜진다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def color(m, c, fr):
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Base Color"].default_value = (*c, 1)
    p.inputs["Base Color"].keyframe_insert("default_value", frame=fr)
lerp = lambda a, b, k: tuple(x + (y - x) * k for x, y in zip(a, b))

def oct_(w, d): return [(w / 2 * math.cos(2 * math.pi * (k + 0.5) / 8), d / 2 * math.sin(2 * math.pi * (k + 0.5) / 8)) for k in range(8)]
def sq(w, d): return [(w / 2, -d / 2), (w / 2, 0), (w / 2, d / 2), (0, d / 2), (-w / 2, d / 2), (-w / 2, 0), (-w / 2, -d / 2), (0, -d / 2)]
def shin(s):                                     # 앞(−y) 이 모난 오각 → 8 점(뒤쪽 변에 가운데 점)
    P = [(0.12, -0.02), (0.11, 0.06), (0.1, 0.12), (0, 0.13), (-0.1, 0.12), (-0.11, 0.06), (-0.12, -0.02), (0, -0.16)]
    return [(x * s, y * s) for x, y in P]
RINGS = [(1.75, oct_(0.44, 0.42)), (1.4, oct_(0.37, 0.35)), (1.08, sq(0.26, 0.26)), (0.95, sq(0.25, 0.27)), (0.84, shin(1.0)), (0.6, shin(1.12)), (0.24, shin(0.6))]
bm = bmesh.new(); rings = [[bm.verts.new((x, y, z)) for x, y in pts] for z, pts in RINGS]
for r0, r1 in zip(rings, rings[1:]):
    for k in range(8): bm.faces.new((r0[k], r0[(k + 1) % 8], r1[(k + 1) % 8], r1[k]))
bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("다리"); bm.to_mesh(me); bm.free()
BASE, FR_, SI, BK = (0.93, 0.86, 0.74), (1.0, 0.58, 0.45), (0.5, 0.82, 0.62), (0.55, 0.65, 1.0)
mf, ms, mb = mat("앞", BASE, 0.6), mat("옆", BASE, 0.6), mat("뒤", BASE, 0.6)
for m in (mf, ms, mb): me.materials.append(m)
for p in me.polygons: p.material_index = 0 if p.normal.y < -0.55 else (2 if p.normal.y > 0.55 else 1)
L = empty("다리돌림", loc=(0, 0, 0))
leg = bpy.data.objects.new("다리", me); bpy.context.scene.collection.objects.link(leg); leg.parent = L
b = leg.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.006, 2
foot = box((0.2, 0.42, 0.14), mat("발", BASE, 0.6), L, (0, -0.1, 0.17), bevel=0.04)
cyl(0.35, 0.1, mat("받침", (0.93, 0.9, 0.84), 0.8), loc=(0, 0, 0.05), bevel=0.02)
# 띠: 고리 점을 따라 빛 막대(조금 크게)
glow = mat("띠", (1.0, 0.45, 0.1), 0.5, emit=1.0)
bands = []
for z, pts in RINGS[1:-1] + [(1.6, [((a + c) / 2, (b_ + d) / 2) for (a, b_), (c, d) in zip(RINGS[0][1], RINGS[1][1])]), (0.42, [((a + c) / 2, (b_ + d) / 2) for (a, b_), (c, d) in zip(RINGS[5][1], RINGS[6][1])])]:
    E = empty("띠", L, (0, 0, z))
    for k in range(8):
        p, q = Vector((*pts[k], 0)) * 1.05, Vector((*pts[(k + 1) % 8], 0)) * 1.05
        bb = bar(p, q, 0.009, glow); bb.parent = E
    E["z"] = z; bands.append(E)
plate_m = mat("훑기", (0.6, 0.9, 1.0), 0.3, emit=1.2, alpha=True); plate_m.show_transparent_back = False; plate_m.shadow_method = "NONE"; pa = alpha_of(plate_m)
plate = box((0.9, 0.9, 0.006), plate_m, loc=(0, 0, 2.0))

cams = {"front": camera("front", (0.2, -3.2, 1.05), (0, 0, 0.95), 30),
        "close": camera("close", (0.4, -1.6, 1.35), (0, 0, 1.3), 32),
        "side": camera("side", (2.4, -1.3, 1.0), (0, 0, 0.95), 30),
        "low": camera("low", (0.6, -1.9, 0.3), (0, 0, 1.0), 26),
        "orbit": camera("orbit", (0, -2.8, 1.1), (0, 0, 0.95), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    L.rotation_euler.z = 0.5 * math.sin(t * 0.5) + 0.8 * T.u(3, 0.1, 0.9, fr) * (1 - T.u(4, 0, 0.5, fr)); key(L, fr, "rotation_euler")
    color(mf, lerp(BASE, FR_, T.u(1, 0.3, 0.6, fr)), fr); color(ms, lerp(BASE, SI, T.u(1, 0.5, 0.8, fr)), fr); color(mb, lerp(BASE, BK, T.u(1, 0.6, 0.9, fr)), fr)
    sweep = T.u(4, 0.05, 1.0, fr); pz = 1.85 - 1.7 * sweep
    plate.location.z = pz; pa.default_value = 0.35 * T.u(4, 0, 0.1, fr) * (1 - T.u(5, 0.0, 0.2, fr)); key(plate, fr, "location"); pa.keyframe_insert("default_value", frame=fr)
    plate.hide_render = not (T.lines[4][0] <= fr <= T.lines[5][0] + 10); key(plate, fr, "hide_render")
    # 2 · 3 줄: 허벅지 · 정강이 쪽 띠 미리 하나씩 · 4 줄: 판이 지나간 띠가 켜진다
    for E in bands:
        z = E["z"]
        on = (fr >= T.lines[4][0] and pz <= z) or (z > 1.0 and T.lines[2][0] + 20 <= fr < T.lines[3][0]) or (z < 0.9 and T.lines[3][0] + 20 <= fr < T.lines[4][0])
        on = on and fr < T.lines[6][0] + (T.lines[6][1] - T.lines[6][0]) * 0.6
        E.scale = (1.0 if on else 0.001,) * 3; key(E, fr, "scale")
        for bb in E.children: bb.hide_render = not on; bb.keyframe_insert("hide_render", frame=fr)
    oc, _ = cams["orbit"]; a = math.radians(-90 + 60 * math.sin(t * 0.5)); oc.location = (2.8 * math.cos(a), 2.8 * math.sin(a), 1.2); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.z = 1.35 - 0.6 * T.u(3, 0, 0.8, fr) + 0.0 * t; cc.location.x = 0.4 * math.cos(t * 0.6); key(cc, fr, "location")
    _, ct = cams["close"]; ct.location.z = 1.3 - 0.6 * T.u(3, 0, 0.8, fr) + 0.4 * T.u(5, 0, 0.6, fr); key(ct, fr, "location")
끝(T, cams)
