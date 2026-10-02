"""1-6 미쇼트 삼각형(Gerbino 그림1) — 선 삼각형의 가운데 띠를 뺀 두 조각(꺾쇠 · 사다리꼴). 고양이를 태운 막대가 틈을 덮으면 삼각형 하나 · 옆에서 보면 뒤는 비었다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 0.4, 1.55)).scale = (3.6, 3.0, 1)
ink = mat("선", (0.05, 0.05, 0.07), 0.5)
A, B, C = Vector((-1.1, 0, 0.5)), Vector((1.1, 0, 0.5)), Vector((0, 0, 2.6))
lo, hi = 1.22, 1.78                               # 빠진 띠
at = lambda P, Q, z: P + (Q - P) * ((z - P.z) / (Q.z - P.z))
segs = [(A, B), (A, at(A, C, lo)), (B, at(B, C, lo)), (at(A, C, hi), C), (at(B, C, hi), C)]
for p, q in segs:
    bar(p, q, 0.045, ink); ball(0.045, ink, loc=p); ball(0.045, ink, loc=q)

plank = box((3.4, 0.14, 0.78), mat("막대", (0.25, 0.42, 0.75), 0.6), loc=(5, -0.2, 1.5), bevel=0.04)
cat = 고양이("고양이", (5, -0.2, 1.89)); cat[0].rotation_euler.z = math.pi     # 막대 위에 탄 고양이(-x 를 봄)
cams = {"front": camera("front", (0, -3.6, 1.5), (0, 0, 1.55), 28),
        "close": camera("close", (0, -2.9, 1.6), (0, 0, 1.6), 24),
        "low": camera("low", (-0.5, -2.9, 0.3), (0, 0, 1.5), 22),
        "slide": camera("slide", (1.2, -3.4, 1.4), (0.3, 0, 1.55), 26),
        "side": camera("side", (2.9, -1.6, 1.7), (0, 0.1, 1.5), 26),
        "orbit": camera("orbit", (0, -3.6, 1.5), (0, 0.1, 1.55), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    u = T.u(2, 0.05, 0.85, fr); x = 5 - 5 * u                       # 막대 미끄러져 들어옴
    out = T.u(4, 0.1, 0.6, fr) * (1 - T.u(5, 0, 0.3, fr))             # 옆 보기 줄: 막대가 앞으로 나와 뒤가 빈 것을 보임
    y = -0.2 - 1.0 * out
    plank.location = (x, y, 1.5); plank.keyframe_insert("location", frame=fr)
    bob = 0.03 * abs(math.sin(fr / 4)) * (0 < u < 1)
    cat[0].location = (x + 0.75, y, 1.89 + bob); cat[0].keyframe_insert("location", frame=fr)
    look = T.u(3, 0, 0.3, fr)                                           # 삼각형이 보이는 줄에 고개 들어 위를 봄
    cat[1].rotation_euler = (0, -0.6 * look, 0.4 * math.sin(fr / 10)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    for k, (c, _) in cams.items():
        p = base[k].copy(); p.x += 0.15 * math.sin(fr / 37 + len(k)); p.y += 0.2 * math.sin(fr / 50)
        if k == "orbit":
            a = math.radians(-90 + 75 * T.u(4, 0, 1, fr)); p = Vector((3.6 * math.cos(a), 3.6 * math.sin(a), 1.6))
        c.location = p; c.keyframe_insert("location", frame=fr)
끝(T, cams)
