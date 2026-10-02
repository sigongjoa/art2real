"""3-10 오목점 잇기 — 땅콩 회전체 윤곽의 오목점 둘에 빨간 점 · 둘을 이은 빛 원판 = 경계 · 위 덩어리가 거기서 떨어짐 · 큰 고양이도 목의 오목점 둘을 이으면 머리가 톡."""
import bpy, bmesh, math
from 장난감_공용 import *

def link(o): bpy.context.scene.collection.objects.link(o); return o
def 매끈(pts, n=8):
    out = []
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        for k in range(n):
            u = 0.5 - 0.5 * math.cos(math.pi * k / n); out.append((r0 + (r1 - r0) * u, z0 + (z1 - z0) * k / n))
    return out + [pts[-1]]
def lathe(name, prof, m, seg=64):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)] for r, z in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new(name, me)); o.data.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
C = [(0.02, 0.28), (0.4, 0.36), (0.52, 0.66), (0.3, 1.02), (0.43, 1.32), (0.33, 1.62), (0.02, 1.72)]
P = 매끈(C); ic = 24; rc, zc = C[3]
nut = mat("땅콩", (0.9, 0.7, 0.42), 0.6)
low_o = lathe("아래", P[:ic + 1], nut); up_o = lathe("위", P[ic:], nut); whole = lathe("통", P, nut)   # 자르기 전엔 이음 없는 통짜
cyl(0.42, 0.3, mat("받침대", (0.85, 0.82, 0.78), 0.8), loc=(0, 0, 0.15), bevel=0.03)
red = mat("빨강", (1, 0.15, 0.12), 0.4, emit=1.5); cutm = mat("자름", (1, 0.75, 0.2), 0.4, emit=1.2, alpha=True); ca = alpha_of(cutm)
dots = [ball(0.065, red, loc=(s * (rc + 0.01), -0.02, zc)) for s in (-1, 1)]
line = bar((-rc, -0.05, zc), (rc, -0.05, zc), 0.02, red)
disk = cyl(rc + 0.04, 0.012, cutm, loc=(0, 0, zc))
big = 고양이("큰고양이", (3.0, 0.3, 0)); big[0].scale = (2.6, 2.6, 2.6); big[0].rotation_euler.z = math.pi
cdots = [ball(0.02, red, big[0], p) for p in ((0.185, 0.12, 0.365), (0.215, 0.12, 0.215))]
cline = bar((0, 0, 0), (0, 0, 1), 0.008, red); cline.parent = big[0]
cline.rotation_mode = "QUATERNION"
from mathutils import Vector
pa, pb = Vector((0.185, 0.12, 0.365)), Vector((0.215, 0.12, 0.215))
cline.location = (pa + pb) / 2; cline.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(pb - pa); cline.scale = (1, 1, (pb - pa).length)
cat = 고양이("고양이", (-1.8, -0.9, 0)); cat[0].rotation_euler.z = 0.4

cams = {"front": camera("front", (0, -3.6, 1.0), (0, 0, 0.95), 35),
        "close": camera("close", (0.2, -2.3, 1.15), (0.0, 0, 1.0), 32),
        "low": camera("low", (-0.7, -1.7, 0.3), (0, 0, 1.0), 26),
        "side": camera("side", (2.0, -2.1, 1.4), (0, 0, 0.95), 30),
        "cat": camera("cat", (2.5, -3.3, 0.8), (2.5, 0, 0.6), 30),
        "catclose": camera("catclose", (2.4, -1.9, 0.85), (2.4, 0, 0.75), 30)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    d = on(1, 0.2, 0.5) * (1 + 0.25 * math.sin(fr / 2.2))
    for o in dots: o.scale = [max(d, 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    l = on(2, 0.05, 0.8); line.scale = (1 if l > 0 else 1e-3, 1 if l > 0 else 1e-3, max(l, 1e-3)); line.keyframe_insert("scale", frame=fr)
    ca.default_value = 0.85 * on(3, 0.05, 0.4) * (1 - 0.3 * math.sin(fr / 3) ** 2); ca.keyframe_insert("default_value", frame=fr)
    lift = math.sin(math.pi * on(4, 0.05, 0.95)) ** 0.6
    cut = fr >= T.lines[4][0]
    whole.hide_render = cut; low_o.hide_render = up_o.hide_render = not cut
    for o in (whole, low_o, up_o): o.keyframe_insert("hide_render", frame=fr)
    up_o.location.z = 0.4 * lift; up_o.rotation_euler.y = 0.25 * lift
    up_o.keyframe_insert("location", frame=fr); up_o.keyframe_insert("rotation_euler", frame=fr)
    disk.location.z = zc + 0.2 * lift; disk.keyframe_insert("location", frame=fr)
    # 큰 고양이: 5 줄에서 점 · 선 · 6 줄에서 머리 톡
    cd = on(5, 0.2, 0.5); cl = on(5, 0.5, 0.9)
    for o in cdots: o.scale = [max(cd * (1 + 0.25 * math.sin(fr / 2.2)), 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    cline.scale = (max(cl, 1e-3), max(cl, 1e-3), (pb - pa).length); cline.keyframe_insert("scale", frame=fr)
    pop = math.sin(math.pi * on(6, 0.1, 0.9)); big[1].location = (0.2 + 0.08 * pop, 0, 0.3 + 0.12 * pop)
    big[1].rotation_euler = (0, -0.4 * pop, 0.15 * math.sin(fr / 8)); big[1].keyframe_insert("location", frame=fr); big[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(big, fr, False)
    cat[0].location.x = -1.8 + 0.25 * on(0, 0.1, 0.9); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.4 - 0.4 * lift, 0.2 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < on(0, 0.1, 0.9) < 1)
끝(T, cams)
