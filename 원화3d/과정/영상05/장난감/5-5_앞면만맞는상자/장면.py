"""5-5 판 뒤 두 상자 실패(Tse 1999 그림5) — 앞면은 일직선인데 오른쪽은 윗면이 뒤로 낮아지는 쐐기. 판이 들리면 고양이가 건너뛰다 비탈에서 미끄러짐."""
import bpy, bmesh, math
from 장난감_공용 import *

def wedge(x0, x1, y0, y1, zf, zb, m):           # 앞면 높이 zf · 뒷면 높이 zb
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0), (x0, y0, zf), (x1, y0, zf), (x1, y1, zb), (x0, y1, zb)]]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]: bm.faces.new([v[i] for i in f])
    me = bpy.data.meshes.new("쐐기"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("쐐기", me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m)
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.03, 3; return o

T = 시작(); 무대(ARGS[1])
ZF, ZB, Y1 = 1.2, 0.45, 1.2
top = lambda y: ZF + (ZB - ZF) * y / Y1
wedge(-1.7, -0.15, 0, Y1, ZF, ZF, mat("왼쪽", (0.98, 0.55, 0.35), 0.6))
wedge(0.15, 1.7, 0, Y1, ZF, ZB, mat("오른쪽", (0.98, 0.55, 0.35), 0.6))
board = box((0.75, 0.08, 2.8), mat("판", (0.55, 0.7, 0.95), 0.7), loc=(0, -0.35, 1.4), bevel=0.03)
glow = mat("선", (1.0, 0.45, 0.08), 0.5, emit=2.2, alpha=True); ga = alpha_of(glow)
fl = [bar((-1.75, -0.45, z), (1.75, -0.45, z), 0.02, glow) for z in (0.02, ZF)]
cat = 고양이("고양이", (-1.0, 0.45, ZF))

cams = {"front": camera("front", (0, -4.8, 2.5), (0, 0.4, 0.9), 25),
        "close": camera("close", (0.3, -3.2, 1.6), (0, 0.3, 1.0), 26),
        "low": camera("low", (2.0, -2.2, 0.3), (0, 0.5, 1.0), 21),
        "top": camera("top", (2.4, -1.8, 4.2), (0.2, 0.5, 0.8), 25),
        "catcam": camera("catcam", (-2.6, -0.9, 1.9), (0.3, 0.6, 1.1), 24)}

for fr in range(1, T.end + 1):
    a = 0.9 * T.u(1, 0.1, 0.4, fr) if T.lines[1][0] <= fr < T.lines[2][0] else 0
    ga.default_value = a; ga.keyframe_insert("default_value", frame=fr)
    for l in fl: l.hide_render = a < 0.02; l.keyframe_insert("hide_render", frame=fr)
    lift = T.u(4, 0, 0.3, fr) if fr >= T.lines[4][0] else 0
    board.location.z = 1.4 + 3.8 * lift; board.keyframe_insert("location", frame=fr)
    # 고양이
    x, y, z, rz, ry, walk = -1.0, 0.45, ZF, 0.0, 0.0, False
    if fr >= T.lines[4][0]:
        w = T.u(4, 0.3, 0.5, fr); x = -1.0 + 0.7 * w; walk = 0 < w < 1
        j = T.u(4, 0.5, 0.65, fr); x += 0.85 * j; z = ZF + (top(y) - ZF) * j + 0.35 * math.sin(math.pi * j)
        s = T.u(4, 0.68, 0.9, fr)
        if s > 0:
            y = 0.45 + (Y1 - 0.45) * s; z = top(y); rz = math.pi / 2 * min(1, s * 4); ry = 0.56 * min(1, s * 4)
            d = T.u(4, 0.9, 1.0, fr); y += 0.25 * d; z = top(Y1) * (1 - d * d) if d > 0 else z
    cat[0].location = (x, y, z); cat[0].rotation_euler = (0, ry, rz)
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0, -0.2, 0.5 * math.sin(fr / 12)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    tc, _ = cams["top"]; tc.location.x = 2.4 - 1.2 * math.sin(fr / 35); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.4 * math.sin(fr / 45); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
