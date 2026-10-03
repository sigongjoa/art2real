"""3-14 L 블록 세 칼 — ㄴ자 블록을 가로 · 세로 · 비스듬히 잘라 조각이 벌어졌다 붙음 · 세 선이 모두 오목 모서리(빨간 점)에서 나온다 · 고양이가 받침에 뛰어오름."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
D = 0.6
def 기둥판(name, pts, m):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bm.faces.new([bm.verts.new((x, 0, z)) for x, z in pts]); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m)
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = D; s.offset = 0
    return o
A_, B_ = mat("조각1", (0.98, 0.7, 0.45), 0.6), mat("조각2", (0.55, 0.78, 0.95), 0.6)
cuts = [  # (조각1, 조각2, 조각2 이동 방향)
    ([(-0.9, 0), (0.9, 0), (0.9, 0.5), (-0.9, 0.5)], [(-0.9, 0.5), (-0.4, 0.5), (-0.4, 1.7), (-0.9, 1.7)], (0, 0, 0.6)),
    ([(-0.9, 0), (-0.4, 0), (-0.4, 1.7), (-0.9, 1.7)], [(-0.4, 0), (0.9, 0), (0.9, 0.5), (-0.4, 0.5)], (0.6, 0, 0)),
    ([(-0.9, 0), (-0.4, 0.5), (-0.4, 1.7), (-0.9, 1.7)], [(-0.9, 0), (0.9, 0), (0.9, 0.5), (-0.4, 0.5)], (0.55, 0, 0))]
sets = [(기둥판("가", a, A_), 기둥판("나", b, B_), Vector(v)) for a, b, v in cuts]
glow = mat("칼선", (1, 0.75, 0.2), 0.4, emit=1.6)
lines = [bar((-0.9, -0.32, 0.5), (-0.4, -0.32, 0.5), 0.02, glow), bar((-0.4, -0.32, 0.0), (-0.4, -0.32, 0.5), 0.02, glow), bar((-0.9, -0.32, 0.0), (-0.4, -0.32, 0.5), 0.02, glow)]
dot = ball(0.06, mat("빨강", (1, 0.15, 0.12), 0.4, emit=1.5), loc=(-0.4, -0.31, 0.5))
cat = 고양이("고양이", (1.25, -0.75, 0)); cat[0].rotation_euler.z = math.pi

cams = {"front": camera("front", (0, -3.5, 0.9), (0, 0, 0.75), 30),
        "close": camera("close", (-0.4, -2.9, 1.0), (-0.3, 0, 0.85), 30),
        "side": camera("side", (0.9, -3.6, 1.9), (0, 0, 0.7), 28),
        "low": camera("low", (0.1, -2.1, 0.25), (-0.3, 0, 0.7), 26),
        "orbit": camera("orbit", (0, -4.0, 1.4), (0, 0, 0.8), 30)}

for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    cur = 0 if fr < T.lines[2][0] else 1 if fr < T.lines[3][0] else 2
    for k, (a, b, v) in enumerate(sets):
        vis = (k == cur) if fr < T.lines[4][0] else (k == 2)
        for o in (a, b): o.hide_render = not vis; o.keyframe_insert("hide_render", frame=fr)
        sep = math.sin(math.pi * on(k + 1, 0.3, 0.95)) if k == cur and fr < T.lines[4][0] else 0
        b.location = v * sep; b.location.y = 0; a.location = -v * 0.3 * sep; a.location.y = 0
        b.keyframe_insert("location", frame=fr); a.keyframe_insert("location", frame=fr)
    for k, l in enumerate(lines):
        if fr < T.lines[4][0]: v = on(k + 1, 0.05, 0.3) * (1 - on(k + 1, 0.85, 1.0)) if k == cur else 0
        elif fr < T.lines[5][0]: v = on(4, 0.1 + 0.15 * k, 0.3 + 0.15 * k)
        else: v = 0.6 + 0.4 * math.sin(fr / 4 + 2.1 * k) if fr < T.lines[6][0] else 1 - on(6, 0, 0.3)
        l.scale = (max(v, 1e-3), max(v, 1e-3), 1); l.keyframe_insert("scale", frame=fr)
    dv = on(4, 0.0, 0.2) * (1 + 0.3 * math.sin(fr / 2.2)) * (1 - on(6, 0, 0.3)); dot.scale = [max(dv, 1e-3)] * 3; dot.keyframe_insert("scale", frame=fr)
    oc = cams["orbit"][0]; u = on(5, 0, 1); a_ = math.radians(-90 + 35 * u)
    oc.location = (4.0 * math.cos(a_), 4.0 * math.sin(a_), 1.4 + 1.0 * u); oc.keyframe_insert("location", frame=fr)
    j = on(6, 0.2, 0.8); hop = math.sin(math.pi * j)
    cat[0].location = (1.25 - 0.75 * j, -0.75 + 0.75 * j, 0.5 * j + 0.4 * hop); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.4, 0.3 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
