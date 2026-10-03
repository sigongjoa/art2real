"""3-9 돌리면 고리 — 빛나는 옆선과 빨간 오목점 · 선이 축을 돌며 면을 쓸면 점이 고리가 된다 · 위 덩어리가 고리에서 떨어져 돈다 · 팽이 · 병도 고리에서."""
import bpy, bmesh, math
from 장난감_공용 import *

def link(o): bpy.context.scene.collection.objects.link(o); return o
def 매끈(pts, n=8):
    out = []
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        for k in range(n):
            u = 0.5 - 0.5 * math.cos(math.pi * k / n); out.append((r0 + (r1 - r0) * u, z0 + (z1 - z0) * k / n))
    return out + [pts[-1]]
def 선메시(name, vs, m):                        # 점들을 잇는 선 메시 + 회전(Screw) — 각도 애니
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [(i, i + 1) for i in range(len(vs) - 1)], []); o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(m); sc = o.modifiers.new("돌림", "SCREW"); sc.angle = 0; sc.steps = sc.render_steps = 96; sc.use_smooth_shade = True
    sc.use_merge_vertices = True; return o, sc
def lathe(name, prof, m, seg=48, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)] for r, z in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m); o.location = loc; return o

T = 시작(); 무대(ARGS[1])
C = [(0.0, 0.3), (0.38, 0.32), (0.5, 0.6), (0.27, 1.0), (0.46, 1.32), (0.32, 1.62), (0.0, 1.68)]
P = 매끈(C); ic = 24; rc, zc = C[3]
clay = mat("점토", (0.95, 0.6, 0.45), 0.55)
low_o, s1 = 선메시("아래", [(r, 0, z) for r, z in P[:ic + 1]], clay)
up_o, s2 = 선메시("위", [(r, 0, z) for r, z in P[ic:]], clay)
cyl(0.45, 0.3, mat("받침대", (0.85, 0.82, 0.78), 0.8), loc=(0, 0, 0.15), bevel=0.03)
pen = mat("선", (1.0, 0.85, 0.2), 0.4, emit=2.5); red = mat("빨강", (1, 0.15, 0.12), 0.4, emit=3.0)
segs = [bar((r0, -0.005, z0), (r1, -0.005, z1), 0.015, pen) for (r0, z0), (r1, z1) in zip(P[::2], P[2::2])]
dot = ball(0.045, red, loc=(rc + 0.01, 0, zc))
ring_o, s3 = 선메시("고리", [(rc + 0.03 + 0.028 * math.cos(2 * math.pi * k / 10), 0, zc + 0.028 * math.sin(2 * math.pi * k / 10)) for k in range(11)], red)
# 다른 돌린 물건: 팽이 · 병 (오목 고리 포함)
toy = mat("팽이", (0.4, 0.7, 0.95), 0.5); bot = mat("병", (0.55, 0.85, 0.5), 0.5)
TP = [(0.01, 0.0), (0.3, 0.25), (0.33, 0.33), (0.1, 0.42), (0.14, 0.52), (0.06, 0.62), (0.01, 0.64)]
BP = [(0.25, 0.0), (0.28, 0.35), (0.12, 0.6), (0.09, 0.72), (0.13, 0.78), (0.01, 0.8)]
extras = []
for x, prof, m, ringz in ((-1.0, TP, toy, (0.42,)), (1.0, BP, bot, (0.72,))):
    root = empty("물건", loc=(x, -0.5, 0)); o = lathe("돌린것", 매끈(prof), m); o.parent = root
    for (r, z) in [p for p in prof if p[1] in ringz]:
        bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.012, minor_radius=0.018, major_segments=48, minor_segments=8, location=(0, 0, z))
        t = bpy.context.object; t.data.materials.append(red); t.parent = root
    root.scale = (0, 0, 0); extras.append(root)
cat = 고양이("고양이", (-1.8, -0.9, 0)); cat[0].rotation_euler.z = 0.4

cams = {"front": camera("front", (0, -3.6, 1.0), (0, 0, 0.95), 35),
        "close": camera("close", (0.25, -2.3, 1.2), (0.15, 0, 1.0), 32),
        "top": camera("top", (0.4, -1.6, 3.0), (0, 0, 0.9), 28),
        "side": camera("side", (2.2, -2.2, 1.4), (0, 0, 0.95), 30),
        "low": camera("low", (-0.7, -1.7, 0.3), (0, 0, 1.0), 26),
        "wide": camera("wide", (0, -4.2, 1.2), (0, 0, 0.75), 28)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    draw = T.u(0, 0.05, 0.6, fr)                               # 선이 아래에서 위로 그려짐
    for k, b in enumerate(segs): b.hide_render = k / len(segs) > draw; b.keyframe_insert("hide_render", frame=fr)
    d = on(1, 0.1, 0.4) * (1 + 0.3 * math.sin(fr / 2)); dot.scale = [max(d, 1e-3)] * 3; dot.keyframe_insert("scale", frame=fr)
    ang = 2 * math.pi * on(2, 0.05, 0.95)
    for s in (s1, s2): s.angle = ang; low_o.keyframe_insert('modifiers["돌림"].angle', frame=fr); up_o.keyframe_insert('modifiers["돌림"].angle', frame=fr)
    s3.angle = 2 * math.pi * on(3, 0.05, 0.8); ring_o.keyframe_insert('modifiers["돌림"].angle', frame=fr)
    lift = math.sin(math.pi * on(4, 0.05, 0.95)) ** 0.6
    up_o.location.z = 0.35 * lift; up_o.rotation_euler.z = 2.5 * on(4, 0.05, 0.95)
    up_o.keyframe_insert("location", frame=fr); up_o.keyframe_insert("rotation_euler", frame=fr)
    for k, e in enumerate(extras):
        u = on(5, 0.05 + 0.3 * k, 0.35 + 0.3 * k); s = u * (1 + 0.2 * math.sin(math.pi * u)); e.scale = (s, s, s)
        e.rotation_euler.z = 3 * fr / 24 * (k == 0); e.keyframe_insert("scale", frame=fr); e.keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.x = -1.8 + 0.25 * on(0, 0.1, 0.9) - 0.0; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.4 - 0.4 * lift, 0.2 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.1, 0.9) < 1)
끝(T, cams)
