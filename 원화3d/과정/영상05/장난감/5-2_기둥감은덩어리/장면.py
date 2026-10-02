"""5-2 원기둥을 휘감은 덩어리(Tse 1999 그림4) — 유리 기둥에 울퉁불퉁 고리가 한 바퀴 감김 → 기둥을 칠해 뒤를 가려도 고리 하나로 보임 → 고양이가 뒤로 돌아가 확인."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
glass = mat("기둥", (0.55, 0.72, 0.98), 0.3, alpha=True); ga = alpha_of(glass)
pole = cyl(0.42, 3.4, glass, loc=(0, 0, 1.7), bevel=0.05)
paint = cyl(0.43, 3.4, mat("칠", (0.62, 0.78, 0.98), 0.7), loc=(0, 0, 1.7), bevel=0.05)
cap = mat("받침", (0.85, 0.8, 0.7), 0.8); cyl(0.7, 0.12, cap, loc=(0, 0, 0.06), bevel=0.03)

blob_m = mat("덩어리", (0.95, 0.42, 0.55), 0.55)
bpy.ops.mesh.primitive_torus_add(major_radius=0.66, minor_radius=0.24, major_segments=96, minor_segments=32)
blob = bpy.context.object
for v in blob.data.vertices:
    a = math.atan2(v.co.y, v.co.x); s = 1 + 0.07 * math.sin(3 * a + 1)
    v.co.x *= s; v.co.y *= s; v.co.z = v.co.z * (1 + 0.35 * math.sin(2 * a + 0.5) ** 2) + 0.22 * math.sin(a + 0.3)
bpy.ops.object.shade_smooth(); put(blob, blob_m, loc=(0, 0, 1.75))

cat = 고양이("고양이", (0.95, -1.15, 0))
cams = {"front": camera("front", (0, -5.0, 1.55), (0, 0, 1.55), 27),
        "close": camera("close", (0.5, -2.9, 1.75), (0, 0, 1.7), 30),
        "low": camera("low", (1.5, -2.3, 0.3), (0, 0, 1.4), 22),
        "top": camera("top", (0.4, -2.6, 4.6), (0, 0, 1.4), 26),
        "back": camera("back", (0.6, 4.6, 1.6), (0, 0, 1.4), 25),
        "catcam": camera("catcam", (2.4, 1.6, 0.45), (0, 0.4, 1.3), 24)}

for fr in range(1, T.end + 1):
    # 기둥: 0~1줄 유리(0.15) → 2줄에서 칠해짐(1.0)
    sp = max(0.001, T.u(2, 0.1, 0.8, fr) if fr >= T.lines[2][0] else 0)   # 칠이 아래에서 위로 차오름
    paint.scale.z = sp; paint.location.z = 1.7 * sp; paint.hide_render = sp < 0.01
    paint.keyframe_insert("scale", frame=fr); paint.keyframe_insert("location", frame=fr); paint.keyframe_insert("hide_render", frame=fr)
    pole.hide_render = sp > 0.99; pole.keyframe_insert("hide_render", frame=fr)
    ga.default_value = 0.15
    blob.rotation_euler.z = 0.15 * math.sin(fr / 20); blob.location.z = 1.75 + 0.05 * math.sin(fr / 13)
    blob.keyframe_insert("rotation_euler", frame=fr); blob.keyframe_insert("location", frame=fr)
    # 고양이: 4줄에서 기둥 둘레를 반 바퀴 돌아 뒤로
    walking = False
    if fr >= T.lines[4][0]:
        u = T.u(4, 0, 0.7, fr); walking = 0 < u < 1
        ang = math.radians(-50 + 140 * u); r = 1.25
        cat[0].location = (r * math.cos(ang), r * math.sin(ang), 0); cat[0].rotation_euler.z = ang + math.pi / 2 + (math.pi / 2 if u >= 1 else 0) * T.u(4, 0.7, 0.85, fr)
    else:
        cat[0].location = (1.0, -0.9, 0.12 * abs(math.sin(math.pi * T.u(3, 0.1, 0.3, fr))) if fr >= T.lines[3][0] else 0)
        cat[0].rotation_euler.z = math.radians(140)
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0, -0.55 + (0.4 if walking else 0), 0.35 * math.sin(fr / 11)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walking)
    # 카메라 조금씩 움직임
    tc, _ = cams["top"]; tc.location.x = 0.4 + 1.2 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.5 * math.sin(fr / 50); fc.keyframe_insert("location", frame=fr)
    bc, _ = cams["back"]; bc.location.x = 0.6 - 1.0 * (T.u(4, 0, 1, fr) if fr >= T.lines[4][0] else 0); bc.keyframe_insert("location", frame=fr)
끝(T, cams)
