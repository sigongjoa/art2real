"""6-1 홀쭉 vs 뚱뚱(Tse 1999 그림10) — 카드 셋 뒤 기둥 셋. 위아래 끝은 똑같은데, 카드를 걷으면 곧은 · 홀쭉 · 뚱뚱."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

def 회전체(rf, z0, z1, m, loc, n=48, k=60):     # 반지름 함수 rf(z) 를 z 축으로 돌린 덩어리
    me = bpy.data.meshes.new("lathe"); bm = bmesh.new(); rings = []
    for i in range(k + 1):
        z = z0 + (z1 - z0) * i / k; r = rf(z)
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / n), r * math.sin(2 * math.pi * j / n), z)) for j in range(n)])
    for a, b in zip(rings, rings[1:]):
        for j in range(n): bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("기둥", me); bpy.context.scene.collection.objects.link(o); o.location = loc
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m); return o

R, lo, hi = 0.17, 0.78, 2.02                      # 카드가 가리는 높이 0.7–2.1
bump = lambda z: math.sin(math.pi * min(max((z - lo) / (hi - lo), 0), 1)) ** 1.5
shapes = [lambda z: R, lambda z: R - 0.12 * bump(z), lambda z: R + 0.17 * bump(z)]
cols = [(0.95, 0.45, 0.4), (0.4, 0.7, 0.95), (0.95, 0.8, 0.35)]
xs = [-1.05, 0, 1.05]
for x, f, c in zip(xs, shapes, cols): 회전체(f, 0.15, 2.65, mat("기둥%.1f" % x, c, 0.5), (x, 0.2, 0))
card_m = mat("카드", (0.97, 0.95, 0.9), 0.8)
cards = [box((0.8, 0.04, 1.4), card_m, loc=(x, -0.25, 1.4), bevel=0.02) for x in xs]

cat = 고양이("고양이", (-2.2, -0.9, 0)); cat[0].scale = (1.5, 1.5, 1.5)
cams = {"front": camera("front", (0, -4.1, 1.4), (0, 0, 1.4), 28),
        "close": camera("close", (0.2, -3.0, 1.6), (0, 0, 1.4), 24),
        "close2": camera("close2", (-0.9, -2.6, 1.0), (0.2, 0, 1.4), 24),
        "low": camera("low", (0.3, -3.0, 0.3), (0, 0, 1.4), 22),
        "side": camera("side", (1.6, -3.4, 1.8), (0, 0, 1.35), 26),
        "wide": camera("wide", (0, -5.2, 2.0), (0, 0, 1.8), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    for i, cd in enumerate(cards):                      # 카드가 차례로 날아오름
        u = T.u(3, 0.1 + 0.2 * i, 0.55 + 0.2 * i, fr)
        cd.location = (xs[i] + 0.4 * u, -0.25 - 0.3 * u, 1.4 + 3.2 * u); cd.rotation_euler = (0.5 * u, 0.6 * u * (1 if i % 2 else -1), 0)
        cd.keyframe_insert("location", frame=fr); cd.keyframe_insert("rotation_euler", frame=fr)
    # 고양이: 처음엔 카드 앞을 걷다가 · 걷힌 뒤 기둥 앞을 지나며 올려다봄
    u1 = T.u(1, 0, 0.8, fr); u2 = T.u(4, 0, 0.9, fr)
    x = -2.2 + 1.2 * u1 + 2.0 * u2; walk = 0 < u1 < 1 or 0 < u2 < 1
    cat[0].location = (x, -0.9, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.7 * T.u(3, 0.3, 0.6, fr), 0.35 * math.sin(fr / 11)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    for k, (cm, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
