"""11-1 Barr 초타원체(1981) — 손잡이 두 개(e1 · e2)를 돌리면 공 → 상자 → 원기둥 → 팔면체. 모양은 셰이프 키(같은 정점에 식으로 계산), 손잡이 · 눈금 막대가 같이 움직인다."""
import bpy, math
from 장난감_공용 import *

def sp(c, e): return math.copysign(abs(c) ** e, c)
def superq(v, e1, e2):
    r = v.length; eta = math.asin(max(-1, min(1, v.z / r))); om = math.atan2(v.y, v.x)
    return (sp(math.cos(eta), e1) * sp(math.cos(om), e2), sp(math.cos(eta), e1) * sp(math.sin(om), e2), sp(math.sin(eta), e1))

T = 시작(); 무대(ARGS[1])
C = (0, 0, 2.05); R = 0.85
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=96, ring_count=48); q = bpy.context.object
bpy.ops.object.shade_smooth(); put(q, mat("초타원체", (0.95, 0.5, 0.6), 0.45), loc=C); q.scale = (R, R, R)
q.shape_key_add(name="공")
cyl(0.05, C[2] - R, mat("받침대", (0.85, 0.8, 0.7), 0.8), loc=(0, 0, (C[2] - R) / 2)); cyl(0.4, 0.08, mat("받침", (0.85, 0.8, 0.7), 0.8), loc=(0, 0, 0.04), bevel=0.02)
keys = {}
for name, e1, e2 in (("상자", 0.12, 0.12), ("원기둥", 0.12, 1.0), ("팔면체", 2.0, 2.0)):
    k = q.shape_key_add(name=name, from_mix=False)
    for d, v in zip(k.data, q.data.vertices): d.co = superq(v.co, e1, e2)
    keys[name] = (k, e1, e2)
# 조종대: 손잡이 둘 + 눈금 막대 둘
box((1.6, 0.6, 0.6), mat("조종대", (0.6, 0.75, 0.95), 0.7), loc=(0, -1.35, 0.3), bevel=0.06)
knob_m, bar_m = mat("손잡이", (0.98, 0.72, 0.25), 0.5), mat("눈금", (0.98, 0.45, 0.3), 0.5)
knobs, bars = [], []
for x in (-0.4, 0.4):
    kn = empty("손잡이", loc=(x, -1.5, 0.6)); cyl(0.17, 0.12, knob_m, kn, (0, 0, 0.06), bevel=0.03); box((0.05, 0.22, 0.05), mat("표시", (0.2, 0.2, 0.25), 0.5), kn, (0, -0.08, 0.13))
    knobs.append(kn)
    bars.append(box((0.12, 0.12, 1.0), bar_m, loc=(x + 0.3 * (1 if x > 0 else -1), -1.2, 0.6)))
for x, s in ((-0.4, "e1"), (0.4, "e2")):
    bpy.ops.object.text_add(location=(x - 0.12, -1.66, 0.42), rotation=(math.pi / 2, 0, 0)); t = bpy.context.object
    t.data.body = s; t.data.size = 0.18; t.data.extrude = 0.01; t.data.materials.append(mat("글자", (0.1, 0.1, 0.15), 0.5))
cat = 고양이("고양이", (1.25, -1.55, 0)); cat[0].rotation_euler.z = math.radians(160)

cams = {"front": camera("front", (0, -6.0, 1.6), (0, 0, 1.45), 26),
        "close": camera("close", (0.4, -4.0, 2.2), (0, 0, 1.9), 28),
        "dial": camera("dial", (0.9, -3.0, 1.0), (0, -1.4, 0.55), 26),
        "top": camera("top", (-1.6, -3.4, 4.6), (0, -0.3, 1.4), 24)}

STEPS = [  # (줄, 시작, 끝, 모양)
    (2, 0.1, 0.6, "상자"), (3, 0.0, 0.35, "원기둥"), (3, 0.5, 0.85, "팔면체"),
    (4, 0.0, 0.25, "상자"), (4, 0.3, 0.55, "원기둥"), (4, 0.6, 0.9, None)]
for fr in range(1, T.end + 1):
    cur = {n: 0.0 for n in keys}; prev = None
    for li, a, b, shape in STEPS:
        if fr < T.lines[li][0]: break
        u = T.u(li, a, b, fr)
        new = {n: (1.0 if n == shape else 0.0) for n in keys}
        cur = {n: cur[n] * (1 - u) + new[n] * u for n in keys}
    e1 = 1 + sum(cur[n] * (keys[n][1] - 1) for n in keys); e2 = 1 + sum(cur[n] * (keys[n][2] - 1) for n in keys)
    for n, (k, _, _) in keys.items(): k.value = cur[n]; k.keyframe_insert("value", frame=fr)
    q.rotation_euler.z = fr / 40; q.keyframe_insert("rotation_euler", frame=fr)
    for kn, b, e in ((knobs[0], bars[0], e1), (knobs[1], bars[1], e2)):
        kn.rotation_euler.z = -(e - 1) * 2.2; kn.keyframe_insert("rotation_euler", frame=fr)
        h = 0.25 + 0.45 * e; b.scale.z = h; b.location.z = 0.6 + h / 2; b.keyframe_insert("scale", frame=fr); b.keyframe_insert("location", frame=fr)
    turning = any(T.lines[li][0] <= fr and 0 < T.u(li, a, b, fr) < 1 for li, a, b, _ in STEPS)
    cat[1].rotation_euler = (0, -0.6 if not turning else 0.1, 0.5 * math.sin(fr / 4) if turning else 0.3 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    tc, _ = cams["top"]; tc.location.x = -1.6 + 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.4 * math.sin(fr / 45); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
