"""3-3 부품 이름표 — 술잔 부품에 이름표가 하나씩 튀어나옴(골과 골 사이) · 얼굴 판이 들어오면 코 · 입술 · 턱 이름표가 다른 자리에."""
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
def 판(name, pts, s, W, m):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        vs = [bm.verts.new(v) for v in ((s * r0, -0.06, z0), (s * W, -0.06, z0), (s * W, -0.06, z1), (s * r1, -0.06, z1))]
        bm.faces.new(vs if s > 0 else vs[::-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m)
    so = o.modifiers.new("두께", "SOLIDIFY"); so.thickness = 0.12; so.offset = -1; return o
def 글(s, m, loc, size=0.13, parent=None):
    bpy.ops.object.text_add(location=loc, rotation=(math.pi / 2, 0, 0)); o = bpy.context.object
    o.data.body = s; o.data.font = FONT; o.data.size = size; o.data.align_x = "CENTER"; o.data.align_y = "CENTER"; o.data.extrude = 0.008
    o.data.materials.append(m); o.parent = parent; return o

T = 시작(); 무대(ARGS[1])
FONT = bpy.data.fonts.load("C:/Windows/Fonts/malgunbd.ttf")   # 시작() 이 공장 설정으로 되돌리니 그 뒤에
C = [(0.45, 0.25), (0.45, 0.32), (0.12, 0.42), (0.08, 0.6), (0.18, 0.75), (0.07, 0.9), (0.42, 1.25), (0.3, 1.55), (0.45, 1.8)]
P = 매끈(C)
gold = mat("술잔", (0.95, 0.75, 0.3), 0.35)
cuts = [0, 24, 40, 56, len(P) - 1]
parts = [lathe("술잔%d" % k, P[a:b + 1], gold) for k, (a, b) in enumerate(zip(cuts, cuts[1:]))]
box((1.7, 0.7, 0.25), mat("받침대", (0.85, 0.82, 0.78), 0.8), loc=(0, 0.1, 0.125), bevel=0.03)
face_m = mat("얼굴", (0.12, 0.16, 0.34), 0.6)
W, fc = 0.85, [0, 32, 48, len(P) - 1]
plates = [[판("얼굴", P[a:b + 1], s, W, face_m) for a, b in zip(fc, fc[1:])] for s in (-1, 1)]
white, black = mat("흰자", (0.95, 0.95, 0.95), 0.4), mat("검은자", (0.03, 0.03, 0.04), 0.3)
for s, ps in zip((-1, 1), plates):
    ball(0.06, white, ps[2], (s * 0.62, -0.07, 1.42), (1, 0.25, 0.7)); ball(0.03, black, ps[2], (s * 0.59, -0.085, 1.42), (1, 0.3, 1))
ink, card, chalk = mat("글씨", (0.1, 0.1, 0.14), 0.5), mat("이름판", (1, 1, 1), 0.7, emit=0.6), mat("분필", (1, 1, 1), 0.5, emit=1.2)
# 술잔 이름표: 오른쪽 판때기 + 지시선
tags = []
for name, z, rr in (("입술", 1.68, 0.42), ("잔", 1.2, 0.42), ("마디", 0.75, 0.18), ("받침", 0.37, 0.4)):
    t = empty("표", loc=(0.92, -0.25, z))
    box((0.44, 0.03, 0.2), card, t, (0, 0.02, 0), bevel=0.02); 글(name, ink, (0, -0.01, 0), 0.13, t)
    bar((0.7, -0.25, z), (rr + 0.02, -0.1, z), 0.008, ink).parent = t; t.scale = (0, 0, 0); tags.append(t)
for o in tags:   # 지시선은 부모 기준이라 위치 보정
    for ch in o.children:
        if ch.type == "MESH" and ch.data.materials[0] == ink and ch.name.startswith("Cylinder"):
            ch.location = ch.location - o.location
# 얼굴 이름표: 오른쪽 판 위 흰 글씨
ftags = [글(n, chalk, (0.62, -0.075, z), 0.12) for n, z in (("코", 1.62), ("입술", 0.95), ("턱", 0.52))]
for o in ftags: o.scale = (0, 0, 0)
cat = 고양이("고양이", (-2.0, -0.8, 0))

cams = {"front": camera("front", (0.1, -4.0, 1.05), (0.1, 0, 1.05), 35),
        "close": camera("close", (0.2, -2.8, 1.2), (0.2, 0, 1.15), 32),
        "low": camera("low", (-0.9, -2.0, 0.35), (0, 0, 1.0), 26),
        "side": camera("side", (1.8, -2.6, 1.3), (0.3, 0, 1.0), 30),
        "wide": camera("wide", (-2.4, -3.8, 1.7), (0, 0, 0.95), 28)}
pop = lambda u: 0 if u <= 0 else (1 + 0.25 * math.sin(math.pi * u)) if u < 1 else 1

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    hide = 1 - on(3, 0, 0.25)
    for k, t in enumerate(tags):                         # 위에서부터 하나씩 튀어나옴
        u = on(1, 0.05 + 0.22 * k, 0.25 + 0.22 * k); s = pop(u) * hide
        t.scale = (s, s, s); t.keyframe_insert("scale", frame=fr)
        p = parts[3 - k]; p.location.z = 0.06 * math.sin(math.pi * u) + 0.03 * math.sin(fr / 6) * (k == 0) * on(2)
        p.keyframe_insert("location", frame=fr)
    slide = 1.7 * (1 - on(3, 0.15, 0.75))
    for s, ps in zip((-1, 1), plates):
        for o in ps: o.location.x = s * slide; o.keyframe_insert("location", frame=fr)
    for k, t in enumerate(ftags):
        s = pop(on(4, 0.05 + 0.25 * k, 0.25 + 0.25 * k)); t.scale = (s, s, s); t.keyframe_insert("scale", frame=fr)
        t.location.z = (1.62, 0.95, 0.52)[k] + 0.02 * math.sin(fr / 5 + k) * on(5); t.keyframe_insert("location", frame=fr)
    x = -2.0 + 1.05 * on(0, 0.1, 0.8) - 0.0; walk = 0 < on(0, 0.1, 0.8) < 1
    cat[0].location = (x, -0.8, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.5 - 0.2 * math.sin(fr / 13), 0.3 * math.sin(fr / 11)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    for n, y0 in (("front", -4.0), ("close", -2.8)):
        c = cams[n][0]; c.location.y = y0 + 0.25 * math.sin(fr / 40); c.keyframe_insert("location", frame=fr)
끝(T, cams)
