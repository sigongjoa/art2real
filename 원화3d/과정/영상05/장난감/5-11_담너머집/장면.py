"""5-11 벽 위 면이 건물 부피냐(Tse 1999 그림22) — 담 너머 두 집: 위쪽은 똑같다. 담이 빠지면 왼쪽은 상자 집, 오른쪽은 접힌 판 한 장 · 고양이가 치면 판이 넘어감."""
import bpy, bmesh, math
from 장난감_공용 import *

def prism(w, d, h, m, parent=None, loc=(0, 0, 0)):   # 박공 지붕: xz 삼각형을 y 로 d 만큼
    bm = bmesh.new(); v = []
    for y in (-d / 2, d / 2): v += [bm.verts.new((-w / 2, y, 0)), bm.verts.new((w / 2, y, 0)), bm.verts.new((0, y, h))]
    for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: bm.faces.new([v[i] for i in f])
    me = bpy.data.meshes.new("지붕"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("지붕", me); bpy.context.scene.collection.objects.link(o); return put(o, m, parent, loc)

T = 시작(); 무대(ARGS[1])
wall_m, cream, roof_m, win_m = mat("담", (0.85, 0.62, 0.5), 0.85), mat("벽", (0.98, 0.92, 0.78), 0.7), mat("지붕", (0.9, 0.38, 0.32), 0.6), mat("창", (0.35, 0.55, 0.85), 0.3)
wall = box((3.6, 0.3, 1.15), wall_m, loc=(0, -0.45, 0.575), bevel=0.03)
# 왼쪽: 상자 집
A = empty("집A", loc=(-0.9, 0, 0))
box((1.2, 1.2, 1.6), cream, A, (0, 0.6, 0.8)); prism(1.45, 1.45, 0.75, roof_m, A, (0, 0.6, 1.6))
for x in (-0.28, 0.28): box((0.26, 0.04, 0.26), win_m, A, (x, -0.01, 1.32))
# 오른쪽: 접힌 판 — 앞판 + 얇은 박공 + 뒤 버팀대 · 앞 아래 모서리에서 뒤로 넘어간다
B = empty("집B", loc=(0.9, 0, 0))
box((1.2, 0.04, 1.6), cream, B, (0, 0.02, 0.8)); prism(1.45, 0.06, 0.75, roof_m, B, (0, 0.03, 1.6))
for x in (-0.28, 0.28): box((0.26, 0.04, 0.26), win_m, B, (x, -0.01, 1.32))
SP = empty("버팀축", loc=(0.9, 0.75, 0))
strut = bar((0.9, 0.04, 1.1), (0.9, 0.75, 0.0), 0.03, mat("버팀", (0.6, 0.45, 0.3), 0.8)); strut.parent = SP; strut.location -= SP.location
cat = 고양이("고양이", (2.2, 1.0, 0)); cat[0].rotation_euler.z = math.pi

cams = {"front": camera("front", (0, -5.6, 1.6), (0, 0, 1.3), 25),
        "close": camera("close", (0.3, -3.6, 1.5), (0, 0, 1.4), 26),
        "low": camera("low", (0.5, -2.7, 0.3), (0, 0, 1.3), 22),
        "top": camera("top", (-1.8, -3.0, 4.4), (0, 0.4, 0.8), 24),
        "orbit": camera("orbit", (0, -5.6, 1.6), (0, 0.4, 1.0), 25),
        "catcam": camera("catcam", (2.6, -1.0, 0.8), (0.9, 0.6, 0.6), 24)}

for fr in range(1, T.end + 1):
    lift = T.u(3, 0, 0.35, fr) if fr >= T.lines[3][0] else 0
    wall.location.z = 0.575 - 1.3 * lift; wall.keyframe_insert("location", frame=fr)
    oc, _ = cams["orbit"]; u = T.u(3, 0, 1, fr) if fr >= T.lines[3][0] else 0
    ang = math.radians(-90 + 60 * u); oc.location = (5.6 * math.cos(ang), 5.6 * math.sin(ang), 1.6 + 2.6 * u); oc.keyframe_insert("location", frame=fr)
    # 고양이: 처음엔 뒤에서 어슬렁 · 4줄 앞부분 버팀대 쪽으로 걸어가 툭 → 판이 앞으로 넘어감
    w = T.u(4, 0, 0.35, fr) if fr >= T.lines[4][0] else 0
    cat[0].location = (2.2 - 1.05 * w, 1.0 - 0.2 * w, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.2, 0.4 * math.sin(fr / 12) * (1 - w)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < w < 1)
    t = T.u(4, 0.35, 0.7, fr) if fr >= T.lines[4][0] else 0
    B.rotation_euler.x = (math.pi / 2) * t * t + 0.04 * math.sin(math.pi * T.u(4, 0.7, 0.8, fr)) * (t >= 1)
    B.keyframe_insert("rotation_euler", frame=fr)
    SP.rotation_euler.x = 0.98 * min(1, t * 1.3); SP.keyframe_insert("rotation_euler", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.8 + 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.4 * math.sin(fr / 45); fc.keyframe_insert("location", frame=fr)
끝(T, cams)
