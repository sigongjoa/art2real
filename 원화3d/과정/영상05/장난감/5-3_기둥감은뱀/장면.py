"""5-3 원기둥을 감은 팔(Tse 1999 그림14) — 지온 뱀이 기둥을 세 바퀴 감음 · 옆 기둥엔 납작한 띠 · 기둥이 들리면 이어진 나선."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

def tube(pts, r, m):
    cu = bpy.data.curves.new("관", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new("관", cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return o
def helix(r, z0, z1, turns, n=240):
    return [Vector((r * math.cos(2 * math.pi * turns * k / n), r * math.sin(2 * math.pi * turns * k / n), z0 + (z1 - z0) * k / n)) for k in range(n + 1)]

T = 시작(); 무대(ARGS[1])
wood = mat("기둥", (0.72, 0.52, 0.34), 0.8)
P1, P2 = Vector((-0.75, 0, 0)), Vector((0.85, 0.2, 0))
posts = [cyl(0.32, 3.4, wood, loc=P1 + Vector((0, 0, 1.7)), bevel=0.04), cyl(0.32, 3.4, wood, loc=P2 + Vector((0, 0, 1.7)), bevel=0.04)]
# 뱀: 나선 관 + 머리 공(맨 위 끝)
snake_m = mat("뱀", (0.55, 0.38, 0.88), 0.55)
root = empty("뱀", loc=P1)
pts = helix(0.46, 0.5, 2.7, 3); snake = tube(pts, 0.13, snake_m); snake.parent = root
head = ball(0.17, snake_m, root, pts[-1] + Vector((0, 0, 0.05)), scale=(1.3, 1, 0.8))
eye = mat("눈", (0.05, 0.05, 0.05), 0.2)
for s in (-1, 1): ball(0.035, eye, head, (0.1, s * 0.09, 0.08))
# 띠: 기둥 면을 따라 감긴 납작한 띠(4줄에 아래서 감겨 올라감)
band_m = mat("띠", (1.0, 0.72, 0.2), 0.6)
bm = bmesh.new(); hp = helix(0.36, 0.6, 2.6, 2.5, 200); prev = None
for p in hp:
    a, b = bm.verts.new(p + Vector((0, 0, -0.13))), bm.verts.new(p + Vector((0, 0, 0.13)))
    if prev: bm.faces.new([prev[0], a, b, prev[1]])
    prev = (a, b)
me = bpy.data.meshes.new("띠"); bm.to_mesh(me); bm.free()
band = bpy.data.objects.new("띠", me); bpy.context.scene.collection.objects.link(band); band.location = P2
sol = band.modifiers.new("두께", "SOLIDIFY"); sol.thickness = 0.04; band.data.materials.append(band_m)
cat = 고양이("고양이", (0.1, -1.1, 0)); cat[0].rotation_euler.z = math.radians(110)

cams = {"front": camera("front", (0, -5.4, 1.6), (0, 0, 1.6), 25),
        "close": camera("close", (-0.5, -2.6, 1.7), (-0.75, 0, 1.6), 28),
        "low": camera("low", (1.0, -2.4, 0.3), (-0.2, 0, 1.5), 21),
        "top": camera("top", (-0.4, -2.0, 4.3), (-0.75, 0, 1.4), 26),
        "band": camera("band", (1.2, -2.5, 1.7), (0.85, 0.2, 1.6), 28),
        "orbit": camera("orbit", (0, -5.4, 2.0), (0, 0, 1.6), 25)}

for fr in range(1, T.end + 1):
    # 뱀은 계속 축 둘레로 돎(오르는 듯) · 머리 끄덕
    root.rotation_euler.z = fr / 30; root.keyframe_insert("rotation_euler", frame=fr)
    head.rotation_euler.y = 0.25 * math.sin(fr / 6); head.keyframe_insert("rotation_euler", frame=fr)
    # 띠: 3줄 전엔 숨김 · 3줄에 아래서 위로 커짐(감기는 느낌)
    g = T.u(3, 0, 0.6, fr) if fr >= T.lines[3][0] else 0
    band.hide_render = g < 0.01; band.scale.z = max(g, 0.01); band.rotation_euler.z = -3 * (1 - g)
    band.keyframe_insert("hide_render", frame=fr); band.keyframe_insert("scale", frame=fr); band.keyframe_insert("rotation_euler", frame=fr)
    # 기둥: 4줄에 위로 빠짐 · 5줄 중간에 다시 내려옴
    back = 1 - T.u(5, 0.2, 0.6, fr) if fr >= T.lines[5][0] else 1
    for k, p in enumerate(posts):
        p.location.z = 1.7 + 4.0 * back * (T.u(4, 0.05 + 0.1 * k, 0.45 + 0.1 * k, fr) if fr >= T.lines[4][0] else 0)
        p.keyframe_insert("location", frame=fr)
    # 고양이: 앉아서 고개로 뱀을 따라봄 · 4줄에 펄쩍
    hop = 0.3 * math.sin(math.pi * T.u(4, 0.1, 0.3, fr)) if fr >= T.lines[4][0] else 0
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.5 - 0.3 * math.sin(fr / 15) ** 2, 0.3 * math.sin(fr / 10)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    oc, _ = cams["orbit"]; u = T.u(4, 0, 1, fr) if fr >= T.lines[4][0] else 0
    ang = math.radians(-90 + 50 * u); oc.location = (5.4 * math.cos(ang), 5.4 * math.sin(ang), 2.0); oc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.y = -5.4 + 0.3 * math.sin(fr / 40); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
