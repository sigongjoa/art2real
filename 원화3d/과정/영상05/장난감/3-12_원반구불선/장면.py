"""3-12 원반 구불선 — 세운 원반이 구불선을 따라 둘로 벌어짐 · 왼쪽 조각의 파인 점(빨강)과 오른쪽 조각의 파인 점(파랑)이 엇갈린다 · 고양이가 틈으로 지나감."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
R, ZC, A, LAM = 0.9, 1.25, 0.12, 0.5
xw = lambda z: A * math.sin(2 * math.pi * z / LAM)          # z 는 원반 중심 기준
def 끝점(sgn):
    z = sgn * R
    for _ in range(20): z = sgn * math.sqrt(R * R - xw(z) ** 2)
    return z
zt, zb = 끝점(1), 끝점(-1)
line = [(xw(zt + (zb - zt) * i / 120), zt + (zb - zt) * i / 120) for i in range(121)]   # 위 → 아래
pt, pb = math.atan2(zt, xw(zt)), math.atan2(zb, xw(zb))
arcL = [(R * math.cos(a), R * math.sin(a)) for a in [pb - (2 * math.pi - (pt - pb)) * i / 90 for i in range(1, 90)]]  # 아래 → 왼쪽 → 위
arcR = [(R * math.cos(a), R * math.sin(a)) for a in [pt - (pt - pb) * i / 90 for i in range(1, 90)]]                  # 위 → 오른쪽 → 아래
def 조각(name, pts, rgb, sx):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bm.faces.new([bm.verts.new((x, 0, z)) for x, z in pts]); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = (0, 0, ZC)
    o.data.materials.append(mat(name, rgb, 0.6)); s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.2; s.offset = 0
    zb_ = -math.sqrt(R * R - 0.16); cyl(0.03, ZC + zb_, mat("막대", (0.6, 0.42, 0.26), 0.8), o, (sx, 0, -(ZC + zb_) / 2 + zb_))
    return o
left = 조각("왼", line + arcL, (0.98, 0.72, 0.5), -0.4)
right = 조각("오", line[::-1] + arcR, (0.55, 0.78, 0.95), 0.4)
red, blue = mat("빨강", (1, 0.15, 0.12), 0.4, emit=1.5), mat("파랑", (0.15, 0.4, 1), 0.4, emit=1.5)
rd = [ball(0.045, red, left, (-A - 0.01, -0.11, z)) for z in (-0.125, 0.375, -0.625)]
bd = [ball(0.045, blue, right, (A + 0.01, -0.11, z)) for z in (0.125, -0.375, 0.625)]
seam = mat("선", (0.15, 0.12, 0.2), 0.5); seams = [bar((x0, -0.105, ZC + z0), (x1, -0.105, ZC + z1), 0.012, seam) for (x0, z0), (x1, z1) in zip(line[::4], line[4::4])]
cat = 고양이("고양이", (-1.9, -0.9, 0)); cat[0].rotation_euler.z = 0.3

cams = {"front": camera("front", (0, -4.0, 1.25), (0, 0, 1.15), 32),
        "close": camera("close", (0, -2.7, 1.35), (0, 0, 1.25), 32),
        "side": camera("side", (2.4, -2.6, 1.5), (0, 0, 1.1), 28),
        "low": camera("low", (-0.6, -1.9, 0.3), (0, 0, 1.0), 24),
        "wide": camera("wide", (-1.5, -4.4, 1.9), (0, 0, 0.9), 28)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    sep = on(1, 0.1, 0.8) * (1 - 0.5 * on(6, 0.1, 0.6))
    left.location.x = -0.55 * sep; right.location.x = 0.55 * sep
    left.rotation_euler.z = 0.25 * on(4, 0, 0.6) * (1 - on(6, 0.1, 0.6)); right.rotation_euler.z = -left.rotation_euler.z
    for o in (left, right): o.keyframe_insert("location", frame=fr); o.keyframe_insert("rotation_euler", frame=fr)
    for b in seams: b.hide_render = fr >= T.lines[1][0] + 3; b.keyframe_insert("hide_render", frame=fr)
    pr = on(2, 0.1, 0.5) * (1 + 0.25 * math.sin(fr / 2.2) * (fr < T.lines[3][0]))
    pbv = on(3, 0.1, 0.5) * (1 + 0.25 * math.sin(fr / 2.2) * (fr < T.lines[4][0]))
    for o in rd: o.scale = [max(pr, 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    for o in bd: o.scale = [max(pbv, 1e-3)] * 3; o.keyframe_insert("scale", frame=fr)
    # 고양이: 처음엔 걸어 들어오고, 5 줄에서 벌어진 틈으로 지나간다
    if fr < T.lines[4][0]: x, y, rz, wk = -1.9 + 0.4 * on(0, 0.1, 0.9), -0.9, 0.3, 0 < on(0, 0.1, 0.9) < 1
    else:
        u = on(4, 0, 0.95); x, y, rz, wk = -1.5 + 1.5 * min(u * 2, 1), -0.9 + 1.9 * max(u * 2 - 1, 0), 0.3 + 1.27 * min(u * 3, 1), 0 < u < 1
    cat[0].location = (x, y, 0); cat[0].rotation_euler.z = rz; cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0, -0.5, 0.25 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, wk)
끝(T, cams)
