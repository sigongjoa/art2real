"""2-4 자리바꿈 — 원통 + 반고리. 고리가 옆에 붙으면 컵, 위로 날아가 걸치면 양동이 · 왔다 갔다(Biederman 1987 그림 3)."""
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
    bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new("고리", me); bpy.context.scene.collection.objects.link(o); me.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
body_m, inner_m, ring_m = mat("통", (0.98, 0.62, 0.35), 0.55), mat("속", (0.45, 0.25, 0.15), 0.8), mat("고리", (0.45, 0.8, 0.55), 0.45)
R, H = 0.35, 0.8
body = cyl(R, H, body_m, loc=(0, 0, H / 2), bevel=0.02)
cyl(R - 0.04, 0.01, inner_m, loc=(0, 0, H + 0.002))                 # 열린 입구처럼
ring = half_ring(0.22, 0.04, ring_m)
SIDE = (Vector((R + 0.0, 0, 0.42)), (0, math.pi / 2, 0), 1.0)          # 컵 손잡이
TOP = (Vector((0, 0, H)), (0, 0, 0), (R + 0.0) / 0.22)                 # 양동이 손잡이
FAR = (Vector((-0.9, -0.3, 0.05)), (math.pi / 2, 0, 0.6), 1.0)         # 처음엔 땅에 따로 놓임

cat = 고양이("고양이", (-1.0, -0.65, 0)); cat[0].rotation_euler.z = 0.35
cams = {"front": camera("front", (0, -3.2, 0.7), (-0.15, 0, 0.55), 40),
        "close": camera("close", (0.6, -2.1, 1.3), (0, 0, 0.5), 38),
        "side": camera("side", (1.6, -2.2, 0.8), (0, 0, 0.55), 38),
        "low": camera("low", (-0.5, -2.2, 0.2), (-0.35, 0, 0.55), 26),
        "top": camera("top", (0.3, -1.7, 2.4), (0, 0, 0.45), 34)}

def blend(a, b, u):
    return a[0].lerp(b[0], u), tuple(x + (y - x) * u for x, y in zip(a[1], b[1])), a[2] + (b[2] - a[2]) * u
L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    # 고리 경로: 땅 → 옆(줄 1) → 위(줄 2) → 옆(줄 3 앞) → 위(줄 3 뒤) → 옆(줄 4) → 위(줄 5)
    st = [(FAR, SIDE, g(1, 0.05, 0.4)), (SIDE, TOP, g(2, 0.05, 0.45)), (TOP, SIDE, g(3, 0.05, 0.3)), (SIDE, TOP, g(3, 0.55, 0.8)),
          (TOP, SIDE, g(4, 0.1, 0.35)), (SIDE, TOP, g(4, 0.6, 0.85))]
    pose = FAR
    for a, b, u in st:
        if u > 0: pose = blend(a, b, u)
        if u >= 1: pose = b
    loc, rot, s = pose; arc = sum(math.sin(math.pi * u) for _, _, u in st)
    ring.location = loc + Vector((0, 0, 0.35 * arc)); ring.rotation_euler = rot; ring.scale = (s, s, s)
    ring.keyframe_insert("location", frame=fr); ring.keyframe_insert("rotation_euler", frame=fr); ring.keyframe_insert("scale", frame=fr)
    # 통: 고리가 붙는 순간 살짝 눌림
    sq = 0.08 * sum(math.sin(math.pi * min(1, max(0, (u - 0.85) / 0.15))) for _, _, u in st)
    body.scale = (1 + sq, 1 + sq, 1 - sq); body.keyframe_insert("scale", frame=fr)
    # 고양이: 바뀔 때마다 고개 갸웃 · 폴짝
    hop = 0.2 * sum(math.sin(math.pi * min(1, max(0, (u - 0.8) / 0.2))) for _, _, u in st)
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.35 * math.sin(fr / 10), -0.35, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
