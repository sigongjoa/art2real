"""5-12 바다괴물 혹 셋(Tse 1999 그림24) — 수조 물 위로 둥근 혹 셋 → 눈은 물속 긴 몸 하나를 짓는다 → 물이 빠지면 굽이치는 몸 하나 · 머리가 쑥 올라와 고양이 깜짝."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
WZ = 0.9
water_m = mat("물", (0.15, 0.45, 0.9), 0.15)
water = box((3.6, 1.6, WZ), water_m, loc=(0, 0, WZ / 2))
rim_m = mat("수조", (0.85, 0.8, 0.7), 0.8)
for x, y, sx, sy in ((0, -0.83, 3.75, 0.08), (0, 0.83, 3.75, 0.08), (-1.84, 0, 0.08, 1.66), (1.84, 0, 0.08, 1.66)):
    box((sx, sy, 0.12), rim_m, loc=(x, y, 0.06))                              # 바닥 테두리
# 몸: 혹 셋 · 꼬리 쪽 가늘게
skin = mat("괴물", (0.95, 0.5, 0.35), 0.5)
cu = bpy.data.curves.new("몸", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 8; cu.use_fill_caps = True
sp = cu.splines.new("POLY"); N = 160; sp.points.add(N)
for k, p in enumerate(sp.points):
    s = k / N; x = -1.65 + 3.1 * s; z = 0.6 + 0.6 * math.sin(6 * math.pi * s - math.pi / 2)
    p.co = (x, 0, max(z, 0.12), 1); p.radius = 0.07 + 0.15 * min(1, s * 3)
body = bpy.data.objects.new("몸", cu); bpy.context.scene.collection.objects.link(body); body.data.materials.append(skin)
END = Vector((1.45, 0, 0.12))
neck = empty("목", loc=END); neck.rotation_euler.y = math.radians(-80)     # 처음엔 앞으로 눕힘(물속)
cyl(0.2, 1.5, skin, neck, (0, 0, 0.75))
head = ball(0.27, skin, neck, (0.12, 0, 1.55), scale=(1.4, 0.9, 0.85))
eye = mat("눈", (0.05, 0.05, 0.05), 0.2); white = mat("흰자", (1, 1, 1), 0.4)
for s in (-1, 1): ball(0.07, white, head, (0.12, s * 0.13, 0.1)); ball(0.035, eye, head, (0.17, s * 0.15, 0.11))
cat = 고양이("고양이", (1.55, -1.25, 0)); cat[0].rotation_euler.z = math.radians(150)

cams = {"front": camera("front", (0.2, -4.4, 1.2), (0.2, 0, 1.0), 23),
        "close": camera("close", (-0.4, -2.8, 1.1), (-0.2, 0, 0.9), 24),
        "low": camera("low", (1.0, -2.4, 0.5), (-0.4, 0, 1.0), 21),
        "top": camera("top", (-1.0, -2.6, 3.6), (0, 0, 0.6), 22),
        "orbit": camera("orbit", (0, -4.4, 1.4), (0, 0, 0.8), 23),
        "catcam": camera("catcam", (2.6, -2.6, 0.5), (1.0, 0, 1.2), 22)}

for fr in range(1, T.end + 1):
    # 물 빠짐(3줄) · 4줄 뒤반쯤 조금 다시 찰 일 없음
    d = T.u(3, 0.05, 0.6, fr) if fr >= T.lines[3][0] else 0
    h = max(WZ * (1 - d), 0.002); water.scale.z = h; water.location.z = h / 2; water.hide_render = d > 0.995
    water.keyframe_insert("scale", frame=fr); water.keyframe_insert("location", frame=fr); water.keyframe_insert("hide_render", frame=fr)
    # 몸이 천천히 꿈틀(앞뒤로 조금)
    body.location.x = 0.05 * math.sin(fr / 10); body.keyframe_insert("location", frame=fr)
    neck.location.x = END.x + body.location.x; neck.keyframe_insert("location", frame=fr)
    up = T.u(4, 0, 0.35, fr) if fr >= T.lines[4][0] else 0
    neck.rotation_euler = (0, math.radians(-80) * (1 - up) + math.radians(15) * up, math.radians(-35) * up + 0.1 * math.sin(fr / 7) * up)
    neck.keyframe_insert("rotation_euler", frame=fr)
    # 고양이: 수조 옆에서 기웃 · 4줄 머리가 오르면 펄쩍 뛰고 뒷걸음
    j = T.u(4, 0.3, 0.5, fr) if fr >= T.lines[4][0] else 0
    back = T.u(4, 0.45, 0.8, fr) if fr >= T.lines[4][0] else 0
    cat[0].location = (1.55 + 0.4 * back, -1.25 - 0.3 * back, 0.45 * math.sin(math.pi * j)); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.3 - 0.4 * up, 0.4 * math.sin(fr / 11) * (1 - up)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < back < 1)
    oc, _ = cams["orbit"]; u = T.u(3, 0, 1, fr) if fr >= T.lines[3][0] else 0
    ang = math.radians(-90 + 45 * u); oc.location = (4.4 * math.cos(ang), 4.4 * math.sin(ang), 1.4 + 1.2 * u); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.4 + 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
