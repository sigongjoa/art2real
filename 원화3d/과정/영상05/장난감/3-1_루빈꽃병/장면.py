"""3-1 루빈의 꽃병 — 회전체 꽃병과 남색 얼굴 판 둘이 실루엣으로 맞물림 · 옆으로 돌면 판이 벌어지고 고양이가 사이를 지난다 · 경계선이 빛난다."""
import bpy, bmesh, math
from 장난감_공용 import *

def link(o): bpy.context.scene.collection.objects.link(o); return o
def lathe(name, prof, m, seg=64):                     # prof=[(r,z)] 아래→위, 양 끝 뚜껑
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)] for r, z in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m); return o
def 매끈(pts, n=8):                                    # 코사인 보간 — 점마다 접선 평평
    out = []
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        for k in range(n):
            u = 0.5 - 0.5 * math.cos(math.pi * k / n); out.append((r0 + (r1 - r0) * u, z0 + (z1 - z0) * k / n))
    return out + [pts[-1]]

T = 시작(); 무대(ARGS[1])
# 꽃병 옆선 = 얼굴 옆모습(r 작은 곳 = 얼굴이 튀어나온 곳)
P = 매끈([(0.5, 0.25), (0.46, 0.5), (0.22, 0.66), (0.34, 0.76), (0.2, 0.86), (0.28, 0.92), (0.19, 0.98), (0.32, 1.08),
          (0.07, 1.24), (0.32, 1.4), (0.24, 1.52), (0.3, 1.6), (0.22, 1.75), (0.45, 1.98)])
vase_m = mat("꽃병", (0.95, 0.93, 0.86), 0.5); vp = next(n for n in vase_m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
vp.inputs["Emission Color"].default_value = (1, 0.85, 0.4, 1)
vase = lathe("꽃병", P, vase_m)
box((1.7, 0.7, 0.25), mat("받침", (0.85, 0.82, 0.78), 0.8), loc=(0, 0.1, 0.125), bevel=0.03)
face_m = mat("얼굴", (0.12, 0.16, 0.34), 0.6); fp = next(n for n in face_m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fp.inputs["Emission Color"].default_value = (0.3, 0.45, 1, 1)
W = 0.78
faces = []
for s in (-1, 1):                                      # 얼굴 판: x = r(z) .. W, 두께 0.12
    me = bpy.data.meshes.new("얼굴"); bm = bmesh.new()
    pts = [(s * r, z) for r, z in P]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        vs = [bm.verts.new(v) for v in ((x0, -0.06, z0), (s * W, -0.06, z0), (s * W, -0.06, z1), (x1, -0.06, z1))]
        bm.faces.new(vs if s > 0 else vs[::-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new("얼굴", me)); o.data.materials.append(face_m)
    so = o.modifiers.new("두께", "SOLIDIFY"); so.thickness = 0.12; so.offset = -1
    faces.append(o)
    ball(0.055, mat("흰자", (0.95, 0.95, 0.95), 0.4), o, (s * 0.5, -0.075, 1.46), (1, 0.25, 0.7))   # 눈 — 얼굴로 읽히게
    ball(0.028, mat("검은자", (0.03, 0.03, 0.04), 0.3), o, (s * 0.47, -0.09, 1.46), (1, 0.3, 1))
glow = mat("경계", (1.0, 0.45, 0.08), 0.5, emit=2.5, alpha=True); ga = alpha_of(glow)
edge = [bar((s * r0, -0.08, z0), (s * r1, -0.08, z1), 0.014, glow) for s in (-1, 1) for (r0, z0), (r1, z1) in zip(P[::2], P[2::2])]
cat = 고양이("고양이", (-2.2, -0.75, 0))

cams = {"front": camera("front", (0, -4.0, 1.1), (0, 0, 1.1), 35),
        "close": camera("close", (0, -2.9, 1.25), (0, 0, 1.2), 32),
        "side": camera("side", (1.6, -2.4, 0.9), (0.3, 0, 1.15), 30),
        "orbit": camera("orbit", (0, -4.0, 1.1), (0, 0, 1.1), 30),
        "wide": camera("wide", (2.6, -3.6, 1.6), (0, 0, 0.9), 28),
        "low": camera("low", (-1.2, -2.2, 0.3), (0, 0, 1.0), 26)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    vp.inputs["Emission Strength"].default_value = 0.8 * math.sin(math.pi * on(1, 0, 1)); vp.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    fp.inputs["Emission Strength"].default_value = 0.5 * math.sin(math.pi * on(2, 0, 1)); fp.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    talk = 0.04 * math.sin(fr / 2.5) * math.sin(math.pi * on(2))       # 얼굴이 말하듯 들썩
    apart = 0.75 * on(3, 0.3, 1) * (1 - on(5, 0, 0.5))
    for s, o in zip((-1, 1), faces):
        o.location = (s * (apart + abs(talk)), 0, 0); o.keyframe_insert("location", frame=fr)
    # 고양이: 처음 걸어 들어와 앉아 보다가, 판이 벌어지면 사이를 지나간다
    x = -2.2 + 1.2 * on(0, 0.1, 0.9); walk = 0 < on(0, 0.1, 0.9) < 1
    if fr >= T.lines[4][0]: u = on(4, 0, 0.9); x = -1.0 + 2.6 * u; walk = 0 < u < 1
    cat[0].location = (x, -0.75, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.5, 0.4 * math.sin(fr / 10)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    oc = cams["orbit"][0]; u = on(3, 0, 1) + 0 * fr
    a = math.radians(-90 + 70 * u); oc.location = (4.0 * math.cos(a), 4.0 * math.sin(a), 1.1 + 0.5 * u); oc.keyframe_insert("location", frame=fr)
    ga.default_value = 0.95 * on(5, 0.15, 0.5); ga.keyframe_insert("default_value", frame=fr)
    for e in edge: e.hide_render = fr < T.lines[5][0]; e.keyframe_insert("hide_render", frame=fr)
끝(T, cams)
