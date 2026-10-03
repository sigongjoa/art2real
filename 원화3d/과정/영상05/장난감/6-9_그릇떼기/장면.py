"""6-9 그릇 떼기(Zhan 외 2020 그림1) — 앞뒤로 겹친 그릇 셋. 맨 앞부터 하나씩 떠올라 옆으로 비키면 가렸던 그릇이 온전히 드러난다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

def 그릇(r, h, c, loc):                         # 뒤집힌 원뿔대 그릇 + 안쪽 어두운 면
    e = empty("그릇", loc=loc)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 0.55, radius2=r, depth=h, vertices=48); o = bpy.context.object
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.03, 3; bpy.ops.object.shade_smooth(); put(o, mat("그릇", c, 0.5), e, (0, 0, h / 2))
    cyl(r * 0.92, 0.01, mat("속", tuple(v * 0.6 for v in c), 0.7), e, (0, 0, h + 0.002))
    return e
table = box((3.2, 2.0, 0.5), mat("탁자", (0.85, 0.68, 0.48), 0.8), loc=(0, 0.4, 0.25), bevel=0.04)
spec = [((-0.2, -0.3, 0.5), 0.55, 0.5, (0.95, 0.45, 0.4)),       # 앞 · 빨강 (낮고 큼)
        ((0.35, 0.3, 0.5), 0.55, 0.75, (0.4, 0.65, 0.95)),       # 가운데 · 파랑
        ((-0.05, 0.9, 0.5), 0.6, 1.05, (0.98, 0.85, 0.35))]      # 뒤 · 노랑 (높음)
bowls = [그릇(r, h, c, loc) for loc, r, h, c in spec]
away = [(-1.9, -0.6), (1.9, -0.6), None]
when = [(3, 0.0, 0.8), (4, 0.0, 0.6), None]

cat = 고양이("고양이", (1.1, -0.35, 0.5)); cat[0].scale = (1.2, 1.2, 1.2); cat[0].rotation_euler.z = math.pi * 0.8
cams = {"front": camera("front", (0, -4.0, 1.25), (0, 0.3, 1.0), 30),
        "close": camera("close", (0.1, -3.0, 1.2), (0, 0.3, 0.95), 28),
        "low": camera("low", (-0.4, -3.0, 0.55), (0, 0.3, 1.0), 24),
        "side": camera("side", (1.7, -3.4, 1.6), (0, 0.3, 0.9), 26),
        "wide": camera("wide", (0, -5.2, 1.7), (0, 0.3, 1.0), 28)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    for i, b in enumerate(bowls):
        (x, y, z), *_ = spec[i]
        if away[i]:
            ln, a, bb = when[i]; u = T.u(ln, a, bb, fr)
            up = math.sin(math.pi * u) * 0.9
            x, y, z = x + (away[i][0] - x) * u, y + (away[i][1] - y) * u, z + up + (-0.5 * u if i == 0 else -0.5 * u)
            b.rotation_euler.y = 0.3 * math.sin(math.pi * u) * (1 if i else -1)
            b.keyframe_insert("rotation_euler", frame=fr)
        b.location = (x, y, max(z, 0)); b.keyframe_insert("location", frame=fr)
    # 고양이: 탁자 위에서 그릇이 뜰 때마다 고개로 따라봄 · 마지막엔 남은 그릇에 다가감
    t = T.u(3, 0, 0.8, fr) - T.u(4, 0, 0.6, fr)
    cat[1].rotation_euler = (0, -0.4 - 0.4 * abs(t), 0.6 * t + 0.2 * math.sin(fr / 11)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    w = T.u(5, 0.1, 0.8, fr); cat[0].location = (1.1 - 0.45 * w, -0.35 + 0.5 * w, 0.5); cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, 0 < w < 1)
    for k, (c, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        c.location = p; c.keyframe_insert("location", frame=fr)
끝(T, cams)
