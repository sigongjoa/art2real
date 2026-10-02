"""5-10 입구를 바꾸면 나선이 사라짐(Tse 1999 그림8) — 같은 뿔 껍질에 소용돌이 입구 → 고양이가 떼어 내고 → 평평한 동그라미 입구로 교체. 껍질은 그대로, 속 느낌만 바뀐다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def tube(pts, r, m, parent):
    cu = bpy.data.curves.new("관", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 5; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new("관", cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); o.parent = parent; return o

T = 시작(); 무대(ARGS[1])
body = cone(0.85, 3.1, mat("껍질", (0.98, 0.78, 0.62), 0.55), loc=(0, 0, 1.55))
bpy.ops.object.shade_smooth()
dark = mat("구멍", (0.12, 0.06, 0.05), 0.9); lipm = mat("입술", (0.98, 0.55, 0.6), 0.5)
HOME = Vector((0, -0.7, 0.68)); TILT = math.radians(-15)
def lip(kind):
    e = empty("입구" + kind, loc=HOME); e.rotation_euler.x = TILT
    cyl(0.44, 0.05, dark, e, (0, 0.0, 0), (math.pi / 2, 0, 0))
    if kind == "소용돌이":
        n = 120; pts = [Vector(((0.43 - 0.33 * k / n) * math.cos(2 * math.pi * 1.6 * k / n), -0.05 + 0.1 * k / n, (0.43 - 0.33 * k / n) * math.sin(2 * math.pi * 1.6 * k / n))) for k in range(n + 1)]
        tube(pts, 0.065, lipm, e)
    else:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.44, minor_radius=0.065); t = bpy.context.object
        put(t, lipm, e, (0, -0.03, 0)); t.rotation_euler.x = math.pi / 2
    return e
A, B = lip("소용돌이"), lip("동그라미")
cat = 고양이("고양이", (-0.75, -1.25, 0)); cat[0].rotation_euler.z = math.radians(35)

cams = {"front": camera("front", (0.2, -5.4, 1.6), (0, 0, 1.45), 26),
        "close": camera("close", (0.5, -2.6, 0.9), (0, -0.4, 0.8), 26),
        "low": camera("low", (1.5, -2.0, 0.2), (0, -0.3, 1.0), 21),
        "top": camera("top", (-1.4, -2.5, 4.0), (0, -0.2, 1.2), 24),
        "catcam": camera("catcam", (-1.9, -2.5, 0.5), (0, -0.6, 0.6), 24)}

for fr in range(1, T.end + 1):
    # A: 2줄 40% 에 고양이가 쳐서 왼쪽으로 날아가 땅에 떨어짐
    f = T.u(2, 0.4, 0.9, fr) if fr >= T.lines[2][0] else 0
    A.location = HOME + Vector((-1.9 * f, -0.9 * f, 0.9 * math.sin(math.pi * f) - (HOME.z - 0.1) * f))
    A.rotation_euler = (TILT + (math.pi / 2 - TILT) * f * 0 - 1.3 * f, 0, 3.0 * f)
    A.keyframe_insert("location", frame=fr); A.keyframe_insert("rotation_euler", frame=fr)
    # B: 3줄에 위에서 내려와 끼워짐(살짝 튕김)
    d = T.u(3, 0, 0.6, fr) if fr >= T.lines[3][0] else 0
    B.location = HOME + Vector((0, -0.4 * (1 - d), 3.5 * (1 - d) + 0.06 * math.sin(math.pi * T.u(3, 0.6, 0.8, fr)) if fr >= T.lines[3][0] else 0))
    B.hide_render = d <= 0; B.keyframe_insert("location", frame=fr)
    for c in [B] + list(B.children): c.hide_render = d <= 0; c.keyframe_insert("hide_render", frame=fr)
    # 고양이: 2줄 앞부분 점프해 앞발로 침
    j = T.u(2, 0.15, 0.55, fr) if fr >= T.lines[2][0] else 0
    cat[0].location = (-0.75 + 0.25 * math.sin(math.pi * j), -1.25 + 0.2 * math.sin(math.pi * j), 0.55 * math.sin(math.pi * j)); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.45 + 0.2 * math.sin(fr / 8), 0.4 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    tc, _ = cams["top"]; tc.location.x = -1.4 + 1.2 * math.sin(fr / 35); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.2 + 0.4 * math.sin(fr / 45); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
