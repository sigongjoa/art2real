"""3-8 코사인 면(Hoffman & Richards 1984) — 물결 원판의 골에 빨간 고리 · 꼬치처럼 돌려 뒤집으면 산마루였던 자리가 골이 되고 파란 고리가 나온다."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
R, A, LAM, TH = 1.0, 0.07, 0.4, 0.04
hgt = lambda p: A * math.cos(2 * math.pi * p / LAM)
me = bpy.data.meshes.new("물결"); bm = bmesh.new(); NR, NT = 60, 96
c0 = bm.verts.new((0, 0, hgt(0))); rings = []
for i in range(1, NR + 1):
    p = R * i / NR; rings.append([bm.verts.new((p * math.cos(2 * math.pi * j / NT), p * math.sin(2 * math.pi * j / NT), hgt(p))) for j in range(NT)])
for j in range(NT): bm.faces.new((c0, rings[0][j], rings[0][(j + 1) % NT]))
for a, b in zip(rings, rings[1:]):
    for j in range(NT): bm.faces.new((a[j], b[j], b[(j + 1) % NT], a[(j + 1) % NT]))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
tilt = empty("기울임", loc=(0, 0, 1.25)); tilt.rotation_euler.x = 0.75
flip = empty("뒤집개", tilt)
sheet = bpy.data.objects.new("물결", me); bpy.context.scene.collection.objects.link(sheet); sheet.parent = flip
sheet.data.materials.append(mat("판", (0.98, 0.86, 0.55), 0.55)); s = sheet.modifiers.new("두께", "SOLIDIFY"); s.thickness = TH; s.offset = 0
red, blue = mat("빨강", (1, 0.22, 0.15), 0.4, emit=1.0), mat("파랑", (0.25, 0.55, 1), 0.4, emit=1.0)
def 고리(p, z, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=p, minor_radius=0.03, major_segments=96, minor_segments=10); o = bpy.context.object
    bpy.ops.object.shade_smooth(); o.data.materials.append(m); o.parent = flip; o.location = (0, 0, z); return o
reds = [고리(p, hgt(p) + TH / 2 + 0.005, red) for p in (0.2, 0.6)]
blues = [고리(p, hgt(p) - TH / 2 - 0.005, blue) for p in (0.4, 0.8)]
wood = mat("기둥", (0.6, 0.42, 0.26), 0.8)
for x in (-1.2, 1.2):
    cyl(0.05, 1.25, wood, loc=(x, 0, 0.625)); bar((x, 0, 1.25), (x * 0.86, 0, 1.25), 0.03, wood)
cat = 고양이("고양이", (-1.9, -0.9, 0)); cat[0].rotation_euler.z = 0.5

cams = {"front": camera("front", (0, -4.0, 1.5), (0, 0, 1.15), 30),
        "close": camera("close", (0, -2.6, 2.1), (0, 0, 1.15), 30),
        "top": camera("top", (0.2, -1.6, 3.2), (0, 0, 1.15), 30),
        "side": camera("side", (2.7, -2.6, 1.3), (0, 0, 1.1), 28)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    flip.rotation_euler.x = math.pi * on(2, 0.1, 0.9) + 0.06 * math.sin(fr / 7) * (fr < T.lines[2][0])
    flip.rotation_euler.z = 0.25 * math.sin(fr / 30)
    flip.keyframe_insert("rotation_euler", frame=fr)
    rv = on(1, 0.2, 0.6) * (1 - on(2, 0, 0.2)) + on(6, 0.0, 0.3) * 0
    bv = on(4, 0.1, 0.5)
    for k, o in enumerate(reds): v = on(1, 0.2 + 0.2 * k, 0.5 + 0.2 * k) * (1 - on(2, 0, 0.2)); o.scale = [max(v, 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    for k, o in enumerate(blues): v = on(4, 0.1 + 0.2 * k, 0.4 + 0.2 * k); o.scale = [max(v, 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    hop = abs(math.sin(math.pi * 2 * on(2, 0.2, 0.8)))
    cat[0].location = (-1.9 + 0.3 * on(0, 0.1, 0.9), -0.9, 0.2 * hop); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.6, 0.2 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.1, 0.9) < 1)
끝(T, cams)
