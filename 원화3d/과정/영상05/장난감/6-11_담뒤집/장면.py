"""6-11 담 뒤 집(pix2gestalt 2024 그림8) — 담 위로 지붕과 벽 윗부분만 보인다. 담이 내려갈 때마다 아랫벽이 다르다: 창 둘 · 문 하나 · 창 하나+문."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

wall_m, roof_m = mat("집벽", (0.98, 0.88, 0.7), 0.8), mat("지붕", (0.85, 0.38, 0.32), 0.7)
win_m, door_m = mat("창", (0.35, 0.55, 0.85), 0.3), mat("문", (0.55, 0.35, 0.22), 0.7)
box((2.0, 1.4, 1.8), wall_m, loc=(0, 0.8, 0.9), bevel=0.03)
bpy.ops.mesh.primitive_cone_add(radius1=1.55, depth=0.9, vertices=4, rotation=(0, 0, math.pi / 4)); r = bpy.context.object
r.scale = (1.0, 0.75, 1); put(r, roof_m, loc=(0, 0.8, 2.25))
for x in (-0.5, 0.5): box((0.36, 0.04, 0.3), win_m, loc=(x, 0.09, 1.55))        # 윗창(늘 보임)
FY = 0.08
def 안(parts):
    g = empty("안")
    for kind, x in parts:
        if kind == "창": box((0.42, 0.04, 0.42), win_m, g, (x, FY, 0.65))
        else: box((0.45, 0.04, 0.85), door_m, g, (x, FY, 0.43))
    return g
cands = [안([("창", -0.5), ("창", 0.5)]), 안([("문", 0.0)]), 안([("창", -0.5), ("문", 0.45)])]
wall = box((3.6, 0.25, 1.25), mat("담", (0.72, 0.72, 0.76), 0.85), loc=(0, -0.4, 0.62), bevel=0.03)

cat = 고양이("고양이", (-0.8, -0.4, 1.25)); cat[0].scale = (1.3, 1.3, 1.3)        # 담 위를 걷는 고양이
cams = {"front": camera("front", (0, -4.6, 1.3), (0, 0, 1.35), 30),
        "close": camera("close", (0.15, -3.5, 1.4), (0, 0, 1.3), 28),
        "low": camera("low", (-0.4, -3.4, 0.3), (0, 0, 1.3), 22),
        "side": camera("side", (1.8, -3.8, 1.8), (0, 0.3, 1.1), 26),
        "wide": camera("wide", (0, -5.8, 1.8), (0, 0, 1.3), 28)}
base = {k: c[0].location.copy() for k, c in cams.items()}

def down(fr):                                    # 담 내려감 정도 0..1
    d = T.u(2, 0.1, 0.5, fr)
    for ln in (3, 4):
        d *= 1 - T.u(ln, 0.0, 0.25, fr); d += T.u(ln, 0.4, 0.7, fr) * (1 - d) if fr >= T.lines[ln][0] else 0
    return d * (1 - T.u(6, 0.2, 0.6, fr))
for fr in range(1, T.end + 1):
    d = down(fr); wall.location.z = 0.62 - 1.3 * d; wall.keyframe_insert("location", frame=fr)
    mid = lambda ln: T.lines[ln][0] + 0.32 * (T.lines[ln][1] - T.lines[ln][0])
    k = 0 if fr < mid(3) else (1 if fr < mid(4) else 2)
    for i, g in enumerate(cands):
        for ch in [g] + list(g.children): ch.hide_render = i != k; ch.keyframe_insert("hide_render", frame=fr)
    # 고양이: 담 위를 걷다 담이 내려가면 같이 내려감(담 꼭대기에 붙어 있음)
    x = -0.8 + 1.6 * (0.5 - 0.5 * math.cos(fr / 40))
    cat[0].location = (x, -0.4, max(0.0, 1.25 - 1.3 * d)); cat[0].rotation_euler.z = 0 if math.sin(fr / 40) >= 0 else math.pi
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0, -0.2, 0.3 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, abs(math.sin(fr / 40)) > 0.08)
    for kk, (c, _) in cams.items():
        p = base[kk].copy(); p.x += 0.2 * math.sin(fr / 37 + len(kk)); p.y += 0.25 * math.sin(fr / 47)
        c.location = p; c.keyframe_insert("location", frame=fr)
끝(T, cams)
