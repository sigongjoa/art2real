"""9-3 띠 두른 달걀 — Vanderpoel 1907 p77. 받침 위 흉곽 달걀 · 위도 띠가 하나씩 감기며 돈다 · 등에 견갑골 판 둘이 내려앉고 · 팔을 들면 판이 미끄러져 돈다 · 앞에 쇄골 막대가 어깨까지 자란다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

bone, band_m = mat("뼈", (0.96, 0.9, 0.8), 0.6), mat("띠", (1.0, 0.5, 0.4), 0.5, emit=0.4)
blade_m, clav_m, wood = mat("견갑", (0.5, 0.68, 0.98), 0.5), mat("쇄골", (1.0, 0.82, 0.3), 0.5), mat("나무", (0.93, 0.85, 0.7), 0.6)
stand = mat("받침", (0.45, 0.38, 0.35), 0.5)
cyl(0.035, 1.0, stand, loc=(0, 0.0, 0.5)); cyl(0.3, 0.04, stand, loc=(0, 0, 0.02), bevel=0.015)
A, B, C = 0.27, 0.21, 0.34                     # 달걀 반폭 · 반깊이 · 반높이
E = empty("흉곽", loc=(0, 0, 1.32))
egg = ball(1, bone, E, (0, 0, 0), (A, B, C))
bands = []
for zf in (-0.6, -0.35, -0.1, 0.15, 0.4, 0.62):
    s = math.sqrt(1 - zf * zf) * 1.015
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.014, major_segments=96, minor_segments=8)
    t = put(bpy.context.object, band_m, E, (0, 0, zf * C)); t["s"] = (A * s, B * s); t.scale = (A * s, B * s, 1); bands.append(t)
# 견갑골: 등에 얹힌 세모 판(조금 휜) — 어깨 쪽 empty 에 매단다
def blade(sx):
    P = empty("견갑", E, (sx * 0.12, B * 0.88, 0.12))
    me = bpy.data.meshes.new("판"); me.from_pydata([(sx * -0.04, 0, 0.12), (sx * 0.13, 0.0, 0.1), (sx * 0.02, 0.0, -0.16)], [], [(0, 1, 2)]); me.update()
    o = bpy.data.objects.new("판", me); bpy.context.scene.collection.objects.link(o); put(o, blade_m, P)
    o.modifiers.new("t", "SOLIDIFY").thickness = 0.025; P.rotation_euler = (-0.25, 0, 0); return P
blades = [blade(-1), blade(1)]
# 쇄골: 복장뼈 위 → 어깨, 막대 두 마디
clav = []
for sx in (-1, 1):
    p0, p1, p2 = Vector((sx * 0.03, -B * 0.85, 0.27)), Vector((sx * 0.16, -B * 0.95, 0.31)), Vector((sx * 0.3, -0.02, 0.3))
    clav.append([bar(p0, p1, 0.018, clav_m), bar(p1, p2, 0.018, clav_m)])
    for b in clav[-1]: b.parent = E; b.location += Vector((0, 0, 0)); b["ends"] = 0
# 팔: 어깨에서 늘어진 나무 원기둥
arms = []
for sx in (-1, 1):
    S = empty("어깨", E, (sx * 0.31, 0.0, 0.26)); ball(0.06, wood, S); cyl(0.045, 0.55, wood, S, (0, 0, -0.3)); arms.append(S)
for o in clav[0] + clav[1]: o["base"] = list(o.scale)

cams = {"front": camera("front", (0, -2.5, 1.3), (0, 0, 1.15), 32),
        "close": camera("close", (0.3, -1.5, 1.45), (0, 0, 1.32), 32),
        "side": camera("side", (2.0, -0.6, 1.4), (0, 0, 1.25), 32),
        "low": camera("low", (0.5, -1.6, 0.6), (0, 0, 1.2), 28),
        "back": camera("back", (0.5, 1.7, 1.6), (0, 0, 1.3), 32),
        "orbit": camera("orbit", (0, -2.0, 1.45), (0, 0, 1.3), 32)}

for fr in range(1, T.end + 1):
    t = fr / 24
    E.rotation_euler = (0, 0, 0.3 * math.sin(t * 0.5)); key(E, fr, "rotation_euler")
    for i, b in enumerate(bands):                 # 2 줄: 띠가 아래에서 위로 하나씩 감긴다(돌며 커진다)
        k = T.u(2, 0.05 + 0.1 * i, 0.3 + 0.1 * i, fr); sx, sy = b["s"]
        b.scale = (max(0.001, sx * k), max(0.001, sy * k), 1); b.rotation_euler.z = 3 * (1 - k); b.hide_render = k < 0.02
        key(b, fr, "scale", "rotation_euler", "hide_render")
    lift = T.u(4, 0.05, 0.6, fr) * (1 - T.u(6, 0.2, 0.7, fr))
    for j, (P, S) in enumerate(zip(blades, arms)):
        sx = -1 if j == 0 else 1
        d = T.u(3, 0.1 + 0.2 * j, 0.5 + 0.2 * j, fr)    # 3 줄: 판이 위에서 내려앉는다
        P.location = (sx * (0.12 + 0.05 * lift), B * 0.88 + 0.5 * (1 - d), 0.12 + 0.6 * (1 - d) + 0.05 * lift)
        P.rotation_euler = (-0.25, 0.25 * (1 - d) * sx, -sx * 0.5 * lift); P.scale = (max(0.001, d),) * 3; key(P, fr, "location", "rotation_euler", "scale")
        S.rotation_euler = (0, sx * -1.9 * lift, 0); key(S, fr, "rotation_euler")
    for j, pair in enumerate(clav):
        for m, o in enumerate(pair):
            k = T.u(5, 0.1 + 0.25 * m, 0.4 + 0.25 * m, fr); o.scale = Vector(o["base"]) * max(0.001, k); o.hide_render = k < 0.02; key(o, fr, "scale", "hide_render")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 70 * math.sin(t * 0.45)); oc.location = (2.0 * math.cos(a), 2.0 * math.sin(a), 1.5); key(oc, fr, "location")
    bc, _ = cams["back"]; bc.location.x = 0.5 * math.cos(t * 0.5); key(bc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.3 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
