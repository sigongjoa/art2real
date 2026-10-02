"""2-5 다섯 물건 — 상자 · 원통 · 고리 몇 개가 날아와 가방 · 서랍 · 컵 · 양동이 · 전화기로 차례로 조립되고, 다 되면 뒤 선반으로 올라간다(MIT 슬라이드 · Biederman)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

def half_ring(R, r, m):
    me = bpy.data.meshes.new("고리"); bm = bmesh.new(); NU, NV = 40, 16; rows = []
    for i in range(NU + 1):
        u = math.pi * i / NU; c = Vector((R * math.cos(u), 0, R * math.sin(u))); n = Vector((math.cos(u), 0, math.sin(u)))
        rows.append([bm.verts.new(c + (n * math.cos(2 * math.pi * j / NV) + Vector((0, 1, 0)) * math.sin(2 * math.pi * j / NV)) * r) for j in range(NV)])
    for i in range(NU):
        for j in range(NV): bm.faces.new([rows[i][j], rows[i][(j + 1) % NV], rows[i + 1][(j + 1) % NV], rows[i + 1][j]])
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1]); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new("고리", me); bpy.context.scene.collection.objects.link(o); me.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
C = {k: mat(k, c, 0.55) for k, c in {"상자": (0.95, 0.5, 0.42), "원통": (0.4, 0.62, 0.95), "고리": (0.45, 0.8, 0.5), "노랑": (0.98, 0.8, 0.3), "보라": (0.75, 0.55, 0.9)}.items()}
wood = mat("선반", (0.7, 0.5, 0.32), 0.8)
box((3.5, 0.55, 0.08), wood, loc=(0, 1.1, 1.2), bevel=0.02)
for x in (-1.6, 1.6): cyl(0.04, 1.2, wood, loc=(x, 1.1, 0.6))

def build(parts):
    root = empty("물건"); objs = []
    for kind, a, b, c in parts:                 # (종류, 크기/반지름, 위치, 회전)
        if kind == "box": o = box(a, C["상자"] if len(objs) == 0 else C["보라"], root, b, bevel=0.03)
        elif kind == "cyl": o = cyl(a[0], a[1], C["원통"], root, b, bevel=0.02)
        elif kind == "ring": o = half_ring(a[0], a[1], C["고리"]); o.parent = root; o.location = b; o.rotation_euler = c; o.scale = (1, 1, a[2])
        elif kind == "ball": o = ball(a, C["노랑"], root, b)
        objs.append((o, Vector(b), o.scale.copy()))
    return root, objs
P2 = math.pi / 2
things = [build([("box", (0.8, 0.25, 0.55), (0, 0, 0.275), 0), ("ring", (0.15, 0.035, 1), (0, 0, 0.55), (0, 0, 0))]),                       # 가방
          build([("box", (0.8, 0.6, 0.5), (0, 0, 0.25), 0), ("ring", (0.12, 0.03, 1), (0, -0.3, 0.3), (P2, 0, 0))]),                          # 서랍
          build([("cyl", (0.3, 0.7), (0, 0, 0.35), 0), ("ring", (0.2, 0.04, 1), (0.3, 0, 0.37), (0, P2, 0))]),                                # 컵
          build([("cyl", (0.33, 0.65), (0, 0, 0.325), 0), ("ring", (0.33, 0.025, 1), (0, 0, 0.65), (0, 0, 0))]),                              # 양동이
          build([("box", (0.7, 0.45, 0.3), (0, 0, 0.15), 0), ("ring", (0.3, 0.06, 0.45), (0, 0, 0.36), (0, 0, 0)),
                 ("ball", 0.09, (0.3, 0, 0.36), 0), ("ball", 0.09, (-0.3, 0, 0.36), 0)])]                                                    # 전화기
SHELF = [Vector((-1.25 + 0.62 * k, 1.1, 1.24)) for k in range(5)]
# 줄 0: 견본 덩어리 다섯이 빙글 돈다
samples = [box((0.3, 0.3, 0.3), C["상자"], bevel=0.03), cyl(0.15, 0.35, C["원통"]), half_ring(0.15, 0.04, C["고리"]), ball(0.15, C["노랑"]), box((0.4, 0.2, 0.12), C["보라"], bevel=0.03)]
sample_sc = [o.scale.copy() for o in samples]

cat = 고양이("고양이", (-1.05, -0.6, 0)); cat[0].rotation_euler.z = 0.3
cams = {"front": camera("front", (0, -3.1, 0.75), (0, 0, 0.55), 36),
        "close": camera("close", (0.5, -2.0, 1.2), (0, 0, 0.4), 34),
        "side": camera("side", (1.4, -2.2, 0.9), (0, 0, 0.45), 34),
        "low": camera("low", (-0.5, -2.2, 0.2), (-0.3, 0, 0.55), 26),
        "wide": camera("wide", (0, -3.9, 0.45), (0, 0.5, 1.0), 26),
        "top": camera("top", (0.4, -2.4, 2.6), (0, 0.4, 0.6), 28),
        "shelf": camera("shelf", (0.3, -1.6, 1.6), (0, 1.1, 1.3), 26)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    gone = g(1, 0, 0.2)
    for k, o in enumerate(samples):
        a = fr / FPS * 1.2 + k * 2 * math.pi / 5; s = max(1e-3, (1 - gone) * min(1, (fr - 1) / 8 + 0.01))
        o.location = (0.55 * math.cos(a), 0.55 * math.sin(a) * 0.5, 0.75 + 0.15 * math.sin(a * 2)); o.rotation_euler = (a, a * 0.7, 0); o.scale = sample_sc[k] * s
        o.keyframe_insert("location", frame=fr); o.keyframe_insert("rotation_euler", frame=fr); o.keyframe_insert("scale", frame=fr)
    for k, (root, objs) in enumerate(things):
        line = k + 1; n = len(objs)
        for j, (o, home, sc) in enumerate(objs):
            u = g(line, 0.03 + 0.5 * j / n, 0.03 + 0.5 * (j + 1) / n)
            o.location = home + Vector((0, 0, 1.6 * (1 - u))); o.scale = sc * max(1e-3, u)
            o.keyframe_insert("location", frame=fr); o.keyframe_insert("scale", frame=fr)
        m = g(line + 1, 0.0, 0.25)                                    # 다음 줄 처음에 선반으로
        p = Vector((0, -0.1, 0)).lerp(SHELF[k], m) + Vector((0, 0, 0.8 * math.sin(math.pi * m)))
        root.location = p; s = 1 - 0.55 * m; root.scale = (s, s, s); root.rotation_euler.z = 0.25 * math.sin(fr / 20) * (1 - m) - 0.3 * (k == 2) * m
        root.keyframe_insert("location", frame=fr); root.keyframe_insert("scale", frame=fr); root.keyframe_insert("rotation_euler", frame=fr)
    hop = 0.18 * sum(math.sin(math.pi * g(i, 0.55, 0.75)) for i in range(1, 6))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.45 - 0.35 * g(6, 0, 0.3), 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
