"""7-2 GBR 머리 셋(Belhumeur 외 1999 그림 2) — 깊이만 0.45 · 1 · 1.8 배로 바꾼 지온 머리 셋. 정면에선 같고 받침을 돌리면 납작 · 보통 · 길쭉."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def 키(o, fr, *props):
    for q in props: o.keyframe_insert(q, frame=fr)

def 머리(loc, d, skin, hair, dark):
    e = empty("머리", loc=loc); h = empty("깊이", e)
    ball(0.32, skin, h, (0, 0, 0), (1, 1.1, 1.25))
    bpy.ops.mesh.primitive_cone_add(radius1=0.075, depth=0.18, vertices=24, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, skin, h, (0, -0.4, -0.04))
    for s in (-1, 1):
        ball(0.05, dark, h, (s * 0.12, -0.32, 0.08)); ball(0.08, skin, h, (s * 0.33, 0, 0), (0.45, 1, 1.3))
    ball(0.335, hair, h, (0, 0.05, 0.13), (1.03, 1.1, 0.9))
    h.scale = (1, d, 1); return e

T = 시작(); 무대(ARGS[1])
skin, hair, dark = mat("살", (0.96, 0.76, 0.6), 0.6), mat("머리칼", (0.42, 0.28, 0.2), 0.7), mat("눈", (0.05, 0.05, 0.06), 0.2)
postm, plate = mat("기둥", (0.9, 0.85, 0.75), 0.7), mat("판", (0.55, 0.75, 0.95), 0.6)
heads = []
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, mat("벽", (0.97, 0.95, 0.9), 1.0, emit=1.35), loc=(0.2, 1.6, 1.3)).scale = (5.5, 2.6, 1)
for x, d in ((-0.95, 0.45), (0, 1.0), (1.35, 1.8)):
    cyl(0.08, 1.0, postm, loc=(x, 0, 0.5)); t = cyl(0.3, 0.08, plate, loc=(x, 0, 1.04), bevel=0.02)
    hd = 머리((x, 0, 1.45), d, skin, hair, dark); hd.parent = None; heads.append((hd, t))
cat = 고양이("고양이", (-2.0, -0.7, 0))
cams = {"front": camera("front", (0.2, -7.5, 1.45), (0.2, 0, 1.4), 48),
        "close": camera("close", (0.2, -5.5, 1.5), (0.2, 0, 1.45), 55),
        "low": camera("low", (1.3, -2.0, 0.3), (0, 0, 1.2), 22),
        "side": camera("side", (-0.1, -6.2, 1.5), (0.2, 0, 1.4), 40),
        "sclose": camera("sclose", (1.9, -3.0, 1.6), (1.2, 0, 1.45), 32),
        "top": camera("top", (0.2, -2.4, 3.6), (0, 0, 1.4), 26),
        "wide": camera("wide", (2.3, -4.6, 0.6), (0, 0, 1.2), 24)}
L = T.lines
for fr in range(1, T.end + 1):
    spin = math.radians(-90) * T.u(2, 0.2, 0.9, fr) * (1 - T.u(5, 0.05, 0.4, fr)) + math.radians(-90) * T.u(5, 0.6, 0.95, fr)
    for hd, t in heads:
        hd.rotation_euler.z = spin; t.rotation_euler.z = spin; 키(hd, fr, "rotation_euler"); 키(t, fr, "rotation_euler")
    w = T.u(0, 0.2, 0.8, fr); w2 = T.u(3, 0.1, 0.8, fr)
    hop = 0.15 * abs(math.sin(fr / 3.5)) * (T.u(3, 0.05, 0.1, fr) - T.u(3, 0.8, 0.85, fr))
    cat[0].location = (-2.0 + 1.0 * w + 2.0 * w2, -0.7, hop); cat[0].rotation_euler.z = 0.3 + 0.9 * T.u(0, 0.8, 1, fr) - 0.9 * T.u(3, 0, 0.1, fr) + 0.9 * T.u(3, 0.8, 0.9, fr)
    cat[1].rotation_euler = (0.35 * math.sin(fr / 6) * (T.u(1, 0, 0.2, fr) - T.u(2, 0, 0.2, fr)), -0.7, 0)
    키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler"); 고양이_키(cat, fr, (0 < w < 1) or (0 < w2 < 1))
    c = cams["front"][0]; c.location.y = -7.5 + 0.8 * fr / T.end; 키(c, fr, "location")
    c = cams["side"][0]; c.location.x = -0.1 + 0.6 * math.sin(fr / 40); 키(c, fr, "location")
    c = cams["wide"][0]; c.location.x = 2.3 - 1.2 * fr / T.end; 키(c, fr, "location")
끝(T, cams)
