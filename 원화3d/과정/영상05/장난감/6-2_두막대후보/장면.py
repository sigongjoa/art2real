"""6-2 두 사각형 완성 후보(Kellman & Shipley 1991 그림48) — 남색 판 뒤로 들어간 두 주황 막대. 판을 열 때마다 뒤가 바뀐다: 꺾인 판 · 따로 · 둥근 이음. 보이는 부분은 늘 같다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 0.3, 1.45)).scale = (3.8, 2.9, 1)
org = mat("주황", (1.0, 0.5, 0.15), 0.7)
W, Y = 0.36, 0.12
def 팔(x0, x1, z0, z1, par): return box((x1 - x0, 0.06, z1 - z0), org, par, ((x0 + x1) / 2, Y, (z0 + z1) / 2), bevel=0.01)
cands = []
for k in range(3):
    g = empty("후보%d" % k)
    if k == 0: 팔(-1.5, 0.18, 1.5 - W / 2, 1.5 + W / 2, g); 팔(-W / 2, W / 2, 0.25, 1.68, g)
    if k == 1: 팔(-1.5, -0.25, 1.5 - W / 2, 1.5 + W / 2, g); 팔(-W / 2, W / 2, 0.25, 1.05, g)
    if k == 2: 팔(-1.5, 0, 1.5 - W / 2, 1.5 + W / 2, g); 팔(-W / 2, W / 2, 0.25, 1.5, g); ball(0.45, org, g, (0, Y, 1.5), (1, 0.15, 1))
    cands.append(g)
hinge = empty("경첩", loc=(0, -0.15, 2.1))
box((1.2, 0.05, 1.2), mat("판", (0.18, 0.24, 0.5), 0.7), hinge, (0, 0, -0.6), bevel=0.02)

cat = 고양이("고양이", (0.75, -0.9, 0)); cat[0].scale = (1.5, 1.5, 1.5); cat[0].rotation_euler.z = math.pi * 0.85
cams = {"front": camera("front", (-0.2, -4.1, 1.3), (-0.2, 0, 1.3), 28),
        "close": camera("close", (-0.1, -2.9, 1.5), (-0.1, 0, 1.4), 26),
        "low": camera("low", (0.4, -3.0, 0.3), (-0.2, 0, 1.3), 22),
        "open": camera("open", (-0.9, -3.5, 1.0), (-0.1, 0, 1.4), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}

def opened(fr):                                  # 0 닫힘 · 1 열림
    o = T.u(2, 0.2, 0.5, fr)
    for ln in (3, 4):
        o *= 1 - T.u(ln, 0, 0.2, fr); o += T.u(ln, 0.35, 0.6, fr) * (1 - o) if fr >= T.lines[ln][0] else 0
    o *= 1 - T.u(5, 0, 0.3, fr)                 # 보이는 부분은 같다 — 다시 닫음
    return min(o, 1)
for fr in range(1, T.end + 1):
    o = opened(fr)
    hinge.rotation_euler.x = -1.9 * o; hinge.keyframe_insert("rotation_euler", frame=fr)
    k = 0 if fr < T.lines[3][0] + (T.lines[3][1] - T.lines[3][0]) * 0.27 else (1 if fr < T.lines[4][0] + (T.lines[4][1] - T.lines[4][0]) * 0.27 else 2)
    for i, g in enumerate(cands):
        for ch in [g] + list(g.children):
            ch.hide_render = i != k; ch.keyframe_insert("hide_render", frame=fr)
    # 고양이: 열릴 때마다 고개를 갸웃 · 앞발 들썩
    cat[1].rotation_euler = (0.45 * o * math.sin(fr / 6), -0.5 * o, 0.25 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.z = 0.04 * o * abs(math.sin(fr / 3)); cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, False)
    for kk, (cm, _) in cams.items():
        p = base[kk].copy(); p.x += 0.2 * math.sin(fr / 37 + len(kk)); p.y += 0.25 * math.sin(fr / 47)
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
