"""6-6 겹친 동물(Zhu 외 2017 그림1) — 고양이 셋이 겹쳐 서 있다 · 보이는 건 머리와 다리 몇 개. 한 마리씩 걸어 나오면 몸이 다 있다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

S = 2.0
spec = [((0.05, -0.35), 0.0, (0.95, 0.58, 0.25)),          # 앞 · 주황 (+x 봄)
        ((-0.1, 0.05), math.pi, (0.55, 0.55, 0.6)),        # 가운데 · 회색 (-x 봄)
        ((0.25, 0.45), 0.0, (0.97, 0.95, 0.9))]            # 뒤 · 흰색
cats = []
for i, ((x, y), rz, c) in enumerate(spec):
    ct = 고양이("고양이%d" % i, (x, y, 0), c); ct[0].scale = (S, S, S); ct[0].rotation_euler.z = rz; cats.append(ct)
# 걸어 나갈 곳 · 언제(줄, 시작, 끝)
dest = [(1.05, -0.35), (-1.05, 0.05), None]
when = [(3, 0.4, 1.0), (4, 0.0, 0.4), None]
cams = {"front": camera("front", (0, -3.3, 0.75), (0, 0, 0.55), 30),
        "close": camera("close", (0.1, -2.4, 0.8), (0, 0, 0.6), 28),
        "low": camera("low", (-0.4, -2.6, 0.2), (0, 0, 0.6), 22),
        "side": camera("side", (1.4, -2.8, 1.0), (0, 0, 0.5), 26),
        "wide": camera("wide", (0, -4.2, 1.1), (0, 0, 0.6), 28)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    for i, ct in enumerate(cats):
        (x, y), rz, _ = spec[i]; z = 0.0; walk = False; rot = rz
        if dest[i]:
            ln, a, b = when[i]; u = T.u(ln, a, b, fr); walk = 0 < u < 1
            x = x + (dest[i][0] - x) * u; y = y + (dest[i][1] - y) * u
            if 0 < u < 1: rot = 0 if dest[i][0] > spec[i][0][0] else math.pi
        else:                                            # 셋째는 제자리에서 폴짝
            j = T.u(4, 0.4, 0.75, fr); z = 0.35 * math.sin(math.pi * j)
        ct[0].location = (x, y, z); ct[0].rotation_euler.z = rot
        ct[0].keyframe_insert("location", frame=fr); ct[0].keyframe_insert("rotation_euler", frame=fr)
        ct[1].rotation_euler = (0, -0.25, 0.4 * math.sin(fr / (9 + 2 * i) + i)); ct[1].keyframe_insert("rotation_euler", frame=fr)
        고양이_키(ct, fr, walk, ph=i)
    for k, (cm, _) in cams.items():
        p = base[k].copy(); p.x += 0.15 * math.sin(fr / 37 + len(k)); p.y += 0.2 * math.sin(fr / 47)
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
