"""11-5 Tulsiani 외(2017) 상자 추상화 — 둥글둥글한 의자 부품마다 반투명 상자가 내려와 씌워짐 → 의자를 치워도 상자 여섯 개가 의자 · 고양이도 몸통 · 머리 · 다리 상자."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
wood, cush = mat("나무", (0.75, 0.55, 0.38), 0.7), mat("방석", (0.6, 0.75, 0.95), 0.8)
chair = []
SZ = 0.95
chair.append(box((1.0, 1.0, 0.12), wood, loc=(0, 0, SZ), bevel=0.05))
chair.append(ball(0.42, cush, loc=(0, -0.02, SZ + 0.1), scale=(1.1, 1.1, 0.18)))
for x in (-0.4, 0.4):
    for y in (-0.4, 0.4):
        chair.append(cone(0.065, SZ, wood, loc=(x, y, SZ / 2), rot=(math.pi, 0, 0)))
for x in (-0.42, 0.42): chair.append(cyl(0.05, 1.15, wood, loc=(x, 0.43, SZ + 0.6)))
chair.append(cyl(0.07, 0.95, wood, loc=(0, 0.43, SZ + 1.15), rot=(0, math.pi / 2, 0), bevel=0.02))
for x in (-0.2, 0, 0.2): chair.append(cyl(0.03, 1.0, wood, loc=(x, 0.43, SZ + 0.6)))
croot = empty("의자")
for o in chair: o.parent = croot

boxm = mat("상자", (1.0, 0.55, 0.15), 0.4, alpha=True); alpha_of(boxm).default_value = 0.55
if hasattr(boxm, "show_transparent_back"): boxm.show_transparent_back = False
BOX = [((1.04, 1.04, 0.32), (0, 0, SZ + 0.08))] + [((0.16, 0.16, SZ - 0.05), (x, y, (SZ - 0.05) / 2)) for x in (-0.4, 0.4) for y in (-0.4, 0.4)] + [((1.0, 0.16, 1.2), (0, 0.43, SZ + 0.65))]
boxes = [(box(s, boxm, loc=l), Vector(s), Vector(l)) for s, l in BOX]
cat = 고양이("고양이", (1.35, -0.5, 0)); cat[0].rotation_euler.z = math.radians(160)
cb = []                                         # 고양이 상자(부위에 붙음)
for par, s, l in [(cat[0], (0.46, 0.25, 0.25), (0, 0, 0.24)), (cat[1], (0.24, 0.22, 0.26), (0.07, 0, 0.06))] + [(lg, (0.07, 0.07, 0.17), (0, 0, -0.08)) for lg in cat[2]]:
    b = box(s, boxm, par, l); cb.append((b, Vector(s)))

cams = {"front": camera("front", (0.5, -5.6, 1.3), (0.4, 0, 1.15), 25),
        "close": camera("close", (-0.6, -3.4, 1.6), (0, 0, 1.2), 26),
        "low": camera("low", (1.0, -2.4, 0.25), (0, 0, 1.0), 21),
        "top": camera("top", (-1.6, -2.8, 4.0), (0.2, 0, 1.0), 24),
        "catcam": camera("catcam", (1.9, -1.8, 0.55), (1.3, -0.45, 0.25), 28)}

def u_(li, a, b, fr): return T.u(li, a, b, fr) if fr >= T.lines[li][0] else 0.0
for fr in range(1, T.end + 1):
    for k, (b, s, l) in enumerate(boxes):
        g = u_(2, k * 0.12, k * 0.12 + 0.2, fr)                       # 위에서 떨어져 씌워짐
        b.location = l + Vector((0, 0, 2.5 * (1 - g))); b.hide_render = g <= 0
        b.keyframe_insert("location", frame=fr); b.keyframe_insert("hide_render", frame=fr)
    gone = u_(3, 0.1, 0.5, fr)                                        # 의자가 바닥으로 꺼짐
    croot.scale = [max(1 - gone, 0.001)] * 3; croot.hide_render = gone > 0.98; croot.keyframe_insert("scale", frame=fr)
    for o in chair: o.hide_render = gone > 0.98; o.keyframe_insert("hide_render", frame=fr)
    for k, (b, s) in enumerate(cb):
        g = u_(4, k * 0.1, k * 0.1 + 0.25, fr); b.scale = s * max(g, 0.001); b.hide_render = g <= 0
        b.keyframe_insert("scale", frame=fr); b.keyframe_insert("hide_render", frame=fr)
    cat[1].rotation_euler = (0, -0.3 + 0.1 * math.sin(fr / 9), 0.4 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    tc, _ = cams["top"]; tc.location.x = -1.6 + 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.5 + 0.4 * math.sin(fr / 45); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
