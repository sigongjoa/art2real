"""3-2 최소점 규칙(Hoffman & Richards 1984) — 술잔이 잘록한 골(빨간 고리)에서 위로 갈라진다 · 판을 대면 두 얼굴 · 얼굴은 술잔이 불룩했던 자리(파란 선)에서 갈라진다."""
import bpy, bmesh, math
from 장난감_공용 import *

def link(o): bpy.context.scene.collection.objects.link(o); return o
def lathe(name, prof, m, seg=64):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)] for r, z in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m); return o
def 매끈(pts, n=8):
    out = []
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        for k in range(n):
            u = 0.5 - 0.5 * math.cos(math.pi * k / n); out.append((r0 + (r1 - r0) * u, z0 + (z1 - z0) * k / n))
    return out + [pts[-1]]
def 판(name, pts, s, W, m):                             # 옆선 pts 에서 x=s*W 까지 판
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        vs = [bm.verts.new(v) for v in ((s * r0, -0.06, z0), (s * W, -0.06, z0), (s * W, -0.06, z1), (s * r1, -0.06, z1))]
        bm.faces.new(vs if s > 0 else vs[::-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m)
    so = o.modifiers.new("두께", "SOLIDIFY"); so.thickness = 0.12; so.offset = -1; return o
def 고리(R, z, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.022, major_segments=64, minor_segments=12, location=(0, 0, z))
    o = bpy.context.object; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o

T = 시작(); 무대(ARGS[1])
C = [(0.45, 0.25), (0.45, 0.32), (0.12, 0.42), (0.08, 0.6), (0.18, 0.75), (0.07, 0.9), (0.42, 1.25), (0.3, 1.55), (0.45, 1.8)]
P = 매끈(C)
gold = mat("술잔", (0.95, 0.75, 0.3), 0.35)
cuts = [0, 24, 40, 56, len(P) - 1]                     # 극소점(제어점 3 · 5 · 7)에서 자름
parts = [lathe("술잔%d" % k, P[a:b + 1], gold) for k, (a, b) in enumerate(zip(cuts, cuts[1:]))]
box((1.7, 0.7, 0.25), mat("받침대", (0.85, 0.82, 0.78), 0.8), loc=(0, 0.1, 0.125), bevel=0.03)
red = mat("빨강", (1.0, 0.2, 0.15), 0.4, emit=2.5); blue = mat("파랑", (0.25, 0.6, 1.0), 0.4, emit=2.5)
rings = [고리(C[i][0] + 0.015, C[i][1], red) for i in (3, 5, 7)]
face_m = mat("얼굴", (0.12, 0.16, 0.34), 0.6)
W, fc = 0.8, [0, 32, 48, len(P) - 1]                   # 얼굴은 극대점(제어점 4 · 6)에서 자름
plates = [[판("얼굴", P[a:b + 1], s, W, face_m) for a, b in zip(fc, fc[1:])] for s in (-1, 1)]
blines = [bar((s * C[i][0], -0.1, C[i][1]), (s * W, -0.1, C[i][1]), 0.02, blue) for s in (-1, 1) for i in (4, 6)]
cat = 고양이("고양이", (-2.0, -0.8, 0))
white, black = mat("흰자", (0.95, 0.95, 0.95), 0.4), mat("검은자", (0.03, 0.03, 0.04), 0.3)
for s_, ps in zip((-1, 1), plates):                    # 얼굴 판에 눈 — 얼굴로 읽히게
    ball(0.06, white, ps[2], (s_ * 0.6, -0.07, 1.42), (1, 0.25, 0.7)); ball(0.03, black, ps[2], (s_ * 0.57, -0.085, 1.42), (1, 0.3, 1))

cams = {"front": camera("front", (0, -4.0, 1.05), (0, 0, 1.05), 35),
        "close": camera("close", (0, -2.8, 1.2), (0, 0, 1.15), 32),
        "low": camera("low", (0.9, -2.0, 0.35), (0, 0, 1.0), 26),
        "side": camera("side", (1.8, -2.6, 1.3), (0.15, 0, 1.0), 30),
        "wide": camera("wide", (-2.4, -3.8, 1.7), (0, 0, 0.95), 28)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    ring_on = on(1, 0.1, 0.3) * (1 - on(3, 0, 0.2))
    for r in rings:
        r.scale = [ring_on * (1 + 0.06 * math.sin(fr / 3))] * 3; r.keyframe_insert("scale", frame=fr)
    sep = math.sin(math.pi * on(2, 0, 1)) ** 0.5 if fr < T.lines[3][0] else 0
    for k, o in enumerate(parts):
        o.location.z = 0.17 * k * sep; o.rotation_euler.z = 0.6 * k * sep
        o.keyframe_insert("location", frame=fr); o.keyframe_insert("rotation_euler", frame=fr)
    slide = 1.6 * (1 - on(3, 0.1, 0.6))                # 판이 옆에서 미끄러져 들어옴
    fsep = math.sin(math.pi * on(5, 0, 1)) ** 0.5 if fr < T.lines[6][0] else 0
    for s, ps in zip((-1, 1), plates):
        for k, o in enumerate(ps):
            o.location = (s * (slide + 0.12 * fsep), 0, 0.17 * k * fsep); o.keyframe_insert("location", frame=fr)
    bl_on = on(4, 0.1, 0.3) * (1 - on(5, 0.0, 0.15)) + on(6, 0, 0.3)
    for k, b in enumerate(blines):
        b.scale = (1, 1, max(bl_on, 0.001)) if False else (max(bl_on, 1e-3), max(bl_on, 1e-3), 1); b.keyframe_insert("scale", frame=fr)
    for r in rings if fr >= T.lines[6][0] else []:
        r.scale = [on(6, 0.2, 0.4)] * 3; r.keyframe_insert("scale", frame=fr)
    x = -2.0 + 1.05 * on(0, 0.1, 0.8); walk = 0 < on(0, 0.1, 0.8) < 1
    cat[0].location = (x, -0.8, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.45 - 0.3 * sep, 0.35 * math.sin(fr / 11)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    for n in ("front", "close"):                        # 느린 밀기
        c = cams[n][0]; c.location.y = (-4.0 if n == "front" else -2.8) + 0.25 * math.sin(fr / 40); c.keyframe_insert("location", frame=fr)
끝(T, cams)
