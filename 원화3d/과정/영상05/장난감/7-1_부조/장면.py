"""7-1 부조 모호성(Belhumeur 외 1999 그림 1) — 대리석 고양이 머리가 정면에선 둥글지만 옆에서 보면 두께 1/5. 옆에 진짜 둥근 머리가 솟아 정면에선 둘이 비슷하다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def 키(o, fr, *props):
    for q in props: o.keyframe_insert(q, frame=fr)

def 머리(loc, m, eye, flat):
    e = empty("머리", loc=loc)
    ball(0.45, m, e)
    for s in (-1, 1):
        ball(0.17, m, e, (s * 0.1, -0.38, -0.14)); ball(0.065, eye, e, (s * 0.17, -0.39, 0.08))
        cone(0.16, 0.32, m, e, (s * 0.25, 0, 0.45), (0, s * 0.4, 0))
    ball(0.06, eye, e, (0, -0.53, -0.04))
    e.scale = (1, flat, 1); return e

T = 시작(); 무대(ARGS[1])
marble, eye, post = mat("대리석", (0.93, 0.9, 0.85), 0.35), mat("눈", (0.55, 0.55, 0.6), 0.35), mat("받침", (0.75, 0.6, 0.45), 0.8)
rel = 머리((-0.6, 0, 1.45), marble, eye, 0.2)
cyl(0.1, 1.0, post, loc=(-0.6, 0, 0.5))
full = 머리((0.7, 0, 1.45), marble, eye, 1.0); fpost = cyl(0.1, 1.0, post, loc=(0.7, 0, 0.5))
cat = 고양이("고양이", (-1.8, -0.9, 0))
cams = {"front": camera("front", (-0.6, -3.4, 1.5), (-0.6, 0, 1.3), 35),
        "close": camera("close", (-0.45, -2.0, 1.6), (-0.6, 0, 1.45), 38),
        "low": camera("low", (0.3, -1.6, 0.3), (-0.6, 0, 1.2), 24),
        "orbit": camera("orbit", (-0.6, -3.0, 1.5), (-0.6, 0, 1.35), 32),
        "peek": camera("peek", (-2.2, -1.6, 0.5), (-0.8, 0, 0.9), 24),
        "side": camera("side", (-3.3, -0.2, 1.5), (-0.6, 0, 1.3), 34),
        "both": camera("both", (0.05, -4.4, 1.4), (0.05, 0, 1.3), 30),
        "close2": camera("close2", (0.05, -2.8, 1.5), (0.05, 0, 1.45), 30),
        "side2": camera("side2", (-3.4, -1.6, 1.8), (0.05, 0, 1.2), 28)}
L = T.lines
for fr in range(1, T.end + 1):
    u = T.u(2, 0, 1, fr); a = math.radians(-90 - 85 * u)
    oc = cams["orbit"][0]; oc.location = (-0.6 + 3.0 * math.cos(a), 3.0 * math.sin(a), 1.5); 키(oc, fr, "location")
    rise = T.u(4, 0.0, 0.45, fr); ov = rise + 0.08 * math.sin(math.pi * rise)
    for o, z0 in ((full, 1.45), (fpost, 0.5)): o.location.z = z0 - 2.0 * (1 - ov); 키(o, fr, "location")
    # 고양이: 정면에서 올려다보다(0-1), 옆으로 돌아가 들여다보고(2-3), 두 머리 사이에 앉는다(4-)
    w1 = T.u(0, 0.3, 0.9, fr); w2 = T.u(2, 0, 0.8, fr); w3 = T.u(4, 0.5, 0.9, fr)
    x = -1.8 + 1.2 * w1 - 0.9 * w2 + 1.55 * w3; y = -0.9 + 0.75 * w2 - 0.6 * w3
    cat[0].location = (x, y, 0)
    cat[0].rotation_euler.z = 1.4 * T.u(0, 0.85, 1, fr) + 1.5 * (T.u(2, 0, 0.1, fr)) - 1.9 * T.u(2, 0.8, 0.95, fr) - 0.6 * T.u(4, 0.45, 0.5, fr) + 0.9 * T.u(4, 0.9, 1, fr)
    cat[1].rotation_euler = (0.35 * math.sin(fr / 6) * (T.u(3, 0, 0.2, fr) - T.u(4, 0, 0.2, fr)), -0.6, 0)
    키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler")
    고양이_키(cat, fr, (0 < w1 < 1) or (0 < w2 < 1) or (0 < w3 < 1))
    c = cams["front"][0]; c.location.y = -3.4 + 0.5 * fr / T.end; 키(c, fr, "location")
    c = cams["both"][0]; c.location.y = -4.4 + 0.5 * T.u(5, 0, 1, fr); 키(c, fr, "location")
    c = cams["side2"][0]; c.location.y = -1.6 + 1.2 * T.u(5, 0, 1, fr) + 0.6 * T.u(6, 0, 1, fr); 키(c, fr, "location")
    c = cams["side"][0]; c.location.y = -0.2 - 0.5 * T.u(3, 0, 1, fr); 키(c, fr, "location")
끝(T, cams)
