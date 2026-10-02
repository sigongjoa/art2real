"""11-6 ShapeAssembly(Jones 외 2020) — 칠판에 코드가 한 줄씩 적히면 상자가 날아와 붙는다: 판 → 다리 넷 → 등받이 → 숫자 하나 바꾸면 등받이가 길어짐 · 고양이가 판에 올라앉음."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def text(s, loc, size, m):
    bpy.ops.object.text_add(location=loc, rotation=(math.pi / 2, 0, 0)); t = bpy.context.object
    t.data.body = s; t.data.size = size; t.data.extrude = 0.004; t.data.materials.append(m); return t

T = 시작(); 무대(ARGS[1])
board = box((2.0, 0.06, 1.9), mat("칠판", (0.16, 0.24, 0.3), 0.8), loc=(-1.45, 0.3, 1.45), bevel=0.03)
for x in (-2.2, -0.7): cyl(0.035, 0.6, mat("다리판", (0.6, 0.45, 0.3), 0.8), loc=(x, 0.3, 0.3))
chalk = mat("글씨", (1, 1, 1), 0.5, emit=1.6); hot = mat("바뀐글씨", (1.0, 0.6, 0.2), 0.5, emit=2.0)
X0, Y0 = -2.35, 0.26
L = ["seat = Cuboid(1.0, 0.1, 1.0)", "leg = Cuboid(0.1, 0.8, 0.1)", "attach(leg, seat, corners)", "back = Cuboid(1.0, 0.9, 0.1)", "attach(back, seat, rear)"]
texts = [text(s, (X0, Y0, 2.2 - 0.3 * i), 0.1, chalk) for i, s in enumerate(L)]
alt = text("back = Cuboid(1.0, 1.6, 0.1)", (X0, Y0, 2.2 - 0.3 * 3), 0.1, hot)

SX, SZ = 0.75, 0.85                                           # 의자 자리 · 판 높이
cols = {"판": (0.98, 0.72, 0.3), "다리": (0.45, 0.78, 0.6), "등": (0.6, 0.75, 0.95)}
seat = box((1.0, 1.0, 0.1), mat("판", cols["판"], 0.55), loc=(SX, 0, SZ), bevel=0.02)
legs = [box((0.1, 0.1, 0.8), mat("다리", cols["다리"], 0.55), loc=(SX + x, y, 0.4), bevel=0.015) for x in (-0.42, 0.42) for y in (-0.42, 0.42)]
back = box((1.0, 0.1, 0.9), mat("등", cols["등"], 0.55), loc=(SX, 0.45, SZ + 0.5), bevel=0.02)
cat = 고양이("고양이", (SX + 1.1, -0.7, 0)); cat[0].rotation_euler.z = math.radians(150)

cams = {"front": camera("front", (-0.35, -6.0, 1.4), (-0.35, 0, 1.25), 25),
        "close": camera("close", (1.2, -3.2, 1.7), (SX, 0, 1.1), 27),
        "code": camera("code", (-1.2, -2.6, 1.6), (-1.45, 0.3, 1.5), 28),
        "top": camera("top", (2.2, -2.6, 4.0), (0.3, 0, 1.0), 24)}

def u_(li, a, b, fr): return T.u(li, a, b, fr) if fr >= T.lines[li][0] else 0.0
for fr in range(1, T.end + 1):
    shows = [u_(1, 0, 0.2, fr), u_(2, 0, 0.15, fr), u_(2, 0.1, 0.25, fr), u_(3, 0, 0.2, fr), u_(3, 0.1, 0.3, fr)]
    sw = u_(4, 0.15, 0.3, fr) > 0.5
    for i, (t, g) in enumerate(zip(texts, shows)):
        t.hide_render = g <= 0 or (i == 3 and sw); t.keyframe_insert("hide_render", frame=fr)
    alt.hide_render = not sw; alt.keyframe_insert("hide_render", frame=fr)
    # 판: 1줄에 위에서 내려옴
    g = u_(1, 0.15, 0.55, fr); seat.location = (SX, 0, SZ + 2.5 * (1 - g)); seat.hide_render = g <= 0
    seat.keyframe_insert("location", frame=fr); seat.keyframe_insert("hide_render", frame=fr)
    for k, lg in enumerate(legs):
        g = u_(2, 0.25 + 0.15 * k, 0.45 + 0.15 * k, fr)
        lg.location = Vector((SX + (-0.42, -0.42, 0.42, 0.42)[k], (-0.42, 0.42, -0.42, 0.42)[k], 0.4)) + Vector(((-1 if k < 2 else 1) * 1.5 * (1 - g), 0, 1.0 * (1 - g)))
        lg.hide_render = g <= 0; lg.keyframe_insert("location", frame=fr); lg.keyframe_insert("hide_render", frame=fr)
    g = u_(3, 0.3, 0.7, fr); hb = 0.9 + 0.7 * u_(4, 0.3, 0.7, fr)
    back.scale = (1.0, 0.1, hb); back.location = (SX, 0.45 + 1.5 * (1 - g), SZ + 0.05 + hb / 2); back.hide_render = g <= 0
    back.keyframe_insert("scale", frame=fr); back.keyframe_insert("location", frame=fr); back.keyframe_insert("hide_render", frame=fr)
    # 고양이: 5줄에 판 위로 폴짝
    j = u_(5, 0.1, 0.4, fr)
    cat[0].location = (SX + 1.1 - 1.1 * j, -0.7 + 0.65 * j, (SZ + 0.05) * j + 0.5 * math.sin(math.pi * j)); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.4 + 0.1 * math.sin(fr / 9), 0.4 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    tc, _ = cams["top"]; tc.location.x = 2.2 - 1.0 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    cc, _ = cams["code"]; cc.location.x = -1.2 + 0.2 * math.sin(fr / 30); cc.keyframe_insert("location", frame=fr)
끝(T, cams)
