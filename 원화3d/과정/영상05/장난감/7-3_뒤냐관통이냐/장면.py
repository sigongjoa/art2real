"""7-3 상자 뒤 지나감 vs 관통(Kellman & Shipley 1991 그림 19) — 정면(망원)에선 똑같은 두 상자 + 막대. 위 · 옆에서 보면 왼쪽은 뒤로, 오른쪽은 상자를 뚫고 지난다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def 키(o, fr, *props):
    for q in props: o.keyframe_insert(q, frame=fr)

T = 시작(); 무대(ARGS[1])
boxm, rodm, postm = mat("상자", (0.98, 0.7, 0.42), 0.7), mat("막대", (0.35, 0.55, 0.95), 0.45), mat("기둥", (0.85, 0.85, 0.85), 0.6)
H = 0.5
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, mat("벽", (0.97, 0.95, 0.9), 1.0, emit=1.35), loc=(0, 1.6, 1.0)).scale = (5.0, 2.0, 1)
for x, dy in ((-0.8, 0.42), (0.8, 0.0)):
    box((0.62, 0.5, 0.8), boxm, loc=(x, 0, 0.4), bevel=0.04)
    cyl(0.06, 1.45, rodm, loc=(x, dy, H), rot=(0, math.pi / 2, 0))
    for s in (-1, 1): cyl(0.02, H, postm, loc=(x + s * 0.62, dy, H / 2))
cat = 고양이("고양이", (-2.2, -0.9, 0))
cams = {"front": camera("front", (0, -14, 0.5), (0, 0, 0.5), 85),
        "close": camera("close", (-0.8, -12, 0.5), (-0.8, 0, 0.5), 110),
        "top": camera("top", (0, -0.25, 5.6), (0, 0.15, 0.4), 30),
        "low": camera("low", (1.4, -2.0, 0.25), (0, 0, 0.6), 22),
        "sideA": camera("sideA", (-2.4, -1.2, 1.6), (-0.8, 0.2, 0.45), 28),
        "sideB": camera("sideB", (2.4, -1.4, 1.5), (0.8, 0, 0.45), 28),
        "wide": camera("wide", (2.4, -4.2, 1.2), (0, 0, 0.5), 24)}
L = T.lines
for fr in range(1, T.end + 1):
    # 오른쪽 상자는 「관통」 줄에서 반투명으로 비치는 대신 살짝 들썩
    w1 = T.u(0, 0.3, 0.9, fr); w2 = T.u(3, 0.0, 0.7, fr); w3 = T.u(5, 0.0, 0.8, fr)
    # 고양이: 앞으로 와서(0), 왼쪽 상자 뒤로 돌아 막대 옆에서 킁킁(3), 다시 앞으로(5)
    x = -2.2 + 1.0 * w1 - 0.55 * w2 + 0.55 * w3; y = -0.9 + 1.65 * w2 - 1.65 * w3
    cat[0].location = (x, y, 0)
    cat[0].rotation_euler.z = 1.75 * T.u(3, 0, 0.1, fr) - 1.75 * T.u(3, 0.7, 0.8, fr) - 1.4 * T.u(5, 0, 0.1, fr) + 1.4 * T.u(5, 0.8, 0.9, fr)
    sniff = 0.15 * math.sin(fr / 2.5) * (T.u(3, 0.7, 0.75, fr) - T.u(4, 0.9, 1.0, fr))
    cat[1].rotation_euler = (0, 0.3 + sniff, 0.0)
    키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler")
    고양이_키(cat, fr, (0 < w1 < 1) or (0 < w2 < 1) or (0 < w3 < 1))
    c = cams["top"][0]; c.location.z = 5.6 - 0.8 * T.u(2, 0, 1, fr) ; 키(c, fr, "location")
    c = cams["front"][0]; c.location.x = 0.15 * math.sin(fr / 50); 키(c, fr, "location")
    c = cams["wide"][0]; c.location.x = 2.4 - 1.4 * fr / T.end; 키(c, fr, "location")
    c = cams["sideA"][0]; c.location.y = -1.2 + 0.6 * T.u(3, 0, 1, fr); 키(c, fr, "location")
    c = cams["sideB"][0]; c.location.y = -1.4 + 0.8 * T.u(4, 0, 1, fr); 키(c, fr, "location")
끝(T, cams)
