"""5-9 소라 나선(Tse 1999 그림7) — 우뚝 선 소라: 보이는 건 입구와 바깥 줄뿐인데 눈은 감겨 올라가는 굴을 짓는다. 카메라가 입구로 들어갔다 나오면 껍질이 유리가 되어 안쪽 나선 굴이 빛난다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

TURNS, N = 4.2, 300
R = lambda t: 0.72 * (1 - 0.85 * t)
Z = lambda t: 0.48 + 2.7 * t
r = lambda t: 0.4 * (1 - 0.82 * t)
def P(t):
    a = 2 * math.pi * TURNS * t; return Vector((R(t) * math.cos(a), R(t) * math.sin(a), Z(t)))
def tube(rad, m, scale=1.0):
    cu = bpy.data.curves.new("소라", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 8; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(N)
    for k, p in enumerate(sp.points):
        t = k / N; p.co = (*P(t), 1); p.radius = rad(t) * scale
    o = bpy.data.objects.new("소라", cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
shell = tube(r, mat("껍질", (0.98, 0.66, 0.72), 0.45))
gm = mat("유리껍질", (0.85, 0.9, 1.0), 0.2, alpha=True); alpha_of(gm).default_value = 0.16
gshell = tube(r, gm)
core_m = mat("굴", (1.0, 0.45, 0.08), 0.5, emit=2.5)
ES = next(n for n in core_m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Emission Strength"]
core = tube(lambda t: r(t) * 0.55, core_m)
d0 = (P(0.002) - P(0)).normalized()
hole = cyl(0.33, 0.02, mat("입구", (0.12, 0.06, 0.05), 0.9), loc=P(0) - d0 * 0.01)
hole.rotation_mode = "QUATERNION"; hole.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d0)
lip = bpy.ops.mesh.primitive_torus_add(major_radius=0.37, minor_radius=0.05); lip = bpy.context.object
put(lip, mat("입술", (1.0, 0.85, 0.6), 0.5), loc=P(0) - d0 * 0.01); lip.rotation_mode = "QUATERNION"; lip.rotation_quaternion = hole.rotation_quaternion
cat = 고양이("고양이", (-0.55, -1.0, 0)); cat[0].rotation_euler.z = math.radians(30)

o0 = P(0)
cams = {"front": camera("front", (0.3, -5.6, 1.7), (0.1, 0, 1.6), 26),
        "close": camera("close", (0.9, -3.0, 1.0), (0.4, 0, 1.2), 26),
        "low": camera("low", (1.8, -1.9, 0.2), (0.2, 0, 1.4), 21),
        "top": camera("top", (-1.6, -2.4, 4.4), (0, 0, 1.6), 24),
        "dive": camera("dive", (o0.x, -4.0, o0.z + 0.5), (o0.x, 0.6, o0.z), 26),
        "orbit": camera("orbit", (0.3, -5.6, 1.9), (0, 0, 1.6), 26)}

for fr in range(1, T.end + 1):
    # 카메라 다이브: 3줄 동안 입구로 쭉 들어감
    dc, dt = cams["dive"]; u = T.u(3, 0, 1, fr) if fr >= T.lines[3][0] else 0
    dc.location = (o0.x, -4.0 + (4.0 - 0.45) * u ** 1.3, o0.z + 0.5 * (1 - u)); dc.keyframe_insert("location", frame=fr)
    # 4줄: 껍질이 유리로 바뀜 + 안쪽 굴이 빛남
    g = fr >= T.lines[4][0] + 3
    shell.hide_render = g; gshell.hide_render = not g; core.hide_render = not g
    for o in (shell, gshell, core): o.keyframe_insert("hide_render", frame=fr)
    ES.default_value = 2.5 + 1.0 * math.sin(fr / 4)
    ES.keyframe_insert("default_value", frame=fr)
    # 소라는 천천히 돈다(입구는 정면 근처에서 왔다갔다)
    # 고양이: 입구 쪽 킁킁(고개 숙였다 들었다) · 4줄 펄쩍
    hop = 0.3 * math.sin(math.pi * T.u(4, 0.05, 0.25, fr)) if fr >= T.lines[4][0] else 0
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, 0.3 * math.sin(fr / 6) - 0.2, 0.3 * math.sin(fr / 17)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    oc, _ = cams["orbit"]; v = T.u(4, 0, 1, fr) if fr >= T.lines[4][0] else 0
    ang = math.radians(-87 + 70 * v); oc.location = (5.6 * math.cos(ang), 5.6 * math.sin(ang), 1.9 + 0.8 * v); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.6 + 1.2 * math.sin(fr / 35); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
