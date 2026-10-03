"""6-5 순환 가림(Zhan 외 그림7) — 띠 넷이 바람개비로 겹친다: 파랑>빨강, 노랑>파랑, 초록>노랑, 빨강>초록. 띠마다 살짝 기울어 맨 앞이 없다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 0.6, 1.55)).scale = (3.8, 3.0, 1)
root = empty("바람개비", loc=(0, 0, 1.55))
cols = [(0.95, 0.3, 0.3), (0.3, 0.5, 0.95), (1.0, 0.82, 0.25), (0.35, 0.78, 0.4)]   # 빨 · 파 · 노 · 초
strips = []
for k, c in enumerate(cols):
    e = empty("띠축%d" % k, root); e.rotation_euler.y = -k * math.pi / 2          # 반시계로 90° 씩
    h = empty("띠%d" % k, e, (0.3, 0, 0.6)); h.rotation_euler.z = -0.13              # +x 끝이 앞(-y) · -x 끝이 뒤
    box((1.95, 0.03, 0.36), mat("띠%d" % k, c, 0.6), h, bevel=0.01); strips.append(h)

cat = 고양이("고양이", (-1.3, -1.0, 0)); cat[0].scale = (1.5, 1.5, 1.5)
cams = {"front": camera("front", (0, -4.1, 1.5), (0, 0, 1.55), 28),
        "close": camera("close", (0.1, -3.0, 1.6), (0, 0, 1.55), 26),
        "low": camera("low", (-0.3, -3.0, 0.3), (0, 0, 1.5), 22),
        "orbit": camera("orbit", (0, -4.1, 1.5), (0, 0, 1.55), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}
order = [(1, 1, 0.0), (1, 2, 0.5), (2, 3, 0.0), (2, 0, 0.5)]      # (줄, 「위」인 띠, 줄 안 시작) — 이름 부를 때 그 띠가 톡 튐

for fr in range(1, T.end + 1):
    root.rotation_euler.y = -0.25 * math.sin(fr / 60); root.keyframe_insert("rotation_euler", frame=fr)
    for k, h in enumerate(strips):
        pop = 0.0
        for ln, kk, a in order:
            if kk == k: pop = max(pop, math.sin(math.pi * T.u(ln, a, a + 0.4, fr)))
        h.scale = (1 + 0.08 * pop,) * 3; h.keyframe_insert("scale", frame=fr)
    # 고양이: 판 앞을 돌며 「맨 위」를 찾는 듯 고개를 이리저리
    x = -1.3 + 2.4 * (0.5 - 0.5 * math.cos(fr / 45))
    cat[0].location.x = x; cat[0].rotation_euler.z = 0 if math.sin(fr / 45) >= 0 else math.pi
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0.35 * math.sin(fr / 7), -0.5, 0.2); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, abs(math.sin(fr / 45)) > 0.08)
    for kk, (cm, _) in cams.items():
        p = base[kk].copy(); p.x += 0.2 * math.sin(fr / 37 + len(kk)); p.y += 0.25 * math.sin(fr / 47)
        if kk == "orbit":
            a = math.radians(-90 + 70 * T.u(3, 0, 0.8, fr)); p = Vector((4.1 * math.cos(a), 4.1 * math.sin(a), 1.8))
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
