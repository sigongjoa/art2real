"""9-5 팔 블록 넷 — Bridgman 1920 p105. 지온 인형 몸통 옆으로 어깨 · 위팔 · 아래팔 · 손 블록 넷이 차례로 날아와 비스듬히 물린다 · 팔을 들고 굽히면 블록 경계에서 꺾인다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def taper(name, L, top, bot, m, parent, loc, slant=0.0):
    """가늘어지는 각기둥 블록: 윗면 (폭, 깊이) · 아랫면 (폭, 깊이) · 끝면은 x 쪽으로 slant 만큼 비스듬(쐐기)."""
    (w1, d1), (w2, d2) = top, bot
    v = [(x, y, L / 2 + slant * x) for x, y in ((-w1 / 2, -d1 / 2), (w1 / 2, -d1 / 2), (w1 / 2, d1 / 2), (-w1 / 2, d1 / 2))] +         [(x, y, -L / 2 + slant * x) for x, y in ((-w2 / 2, -d2 / 2), (w2 / 2, -d2 / 2), (w2 / 2, d2 / 2), (-w2 / 2, d2 / 2))]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.012, 2
    return put(o, m, parent, loc)

wood, joint = mat("나무", (0.93, 0.85, 0.7), 0.6), mat("마디", (0.8, 0.7, 0.55), 0.6)
stand = mat("받침", (0.45, 0.38, 0.35), 0.5)
cyl(0.03, 0.85, stand, loc=(0, 0, 0.42)); cyl(0.3, 0.04, stand, loc=(0, 0, 0.02), bevel=0.015)
B = empty("몸", loc=(0, 0, 0))
box((0.38, 0.24, 0.24), wood, B, (0, 0, 0.98), bevel=0.04)
box((0.46, 0.28, 0.44), wood, B, (0, 0, 1.36), bevel=0.05)
cyl(0.05, 0.12, joint, B, (0, 0, 1.63)); box((0.2, 0.24, 0.26), wood, B, (0, 0, 1.8), bevel=0.05)
# 왼팔은 밋밋한 원기둥(대조)
L = empty("왼어깨", B, (-0.29, 0, 1.52)); ball(0.06, joint, L); cyl(0.045, 0.6, wood, L, (0, 0, -0.32))
cols = [(1.0, 0.55, 0.45), (1.0, 0.82, 0.35), (0.45, 0.8, 0.6), (0.5, 0.65, 1.0)]
S = empty("어깨", B, (0.25, 0, 1.5))
blocks = [taper("어깨블록", 0.2, (0.2, 0.22), (0.16, 0.18), mat("b0", cols[0], 0.55), S, (0.06, 0, 0.0), slant=0.35)]
blocks.append(taper("위팔", 0.32, (0.13, 0.15), (0.11, 0.12), mat("b1", cols[1], 0.55), S, (0.06, 0, -0.22), slant=-0.3))
E = empty("팔꿈치", S, (0.06, 0, -0.39))
blocks.append(taper("아래팔", 0.3, (0.13, 0.12), (0.08, 0.07), mat("b2", cols[2], 0.55), E, (0, 0, -0.15), slant=0.3))
W = empty("손목", E, (0, 0, -0.31))
blocks.append(taper("손", 0.17, (0.09, 0.05), (0.1, 0.04), mat("b3", cols[3], 0.55), W, (0, 0, -0.09), slant=-0.2))
for b in blocks: b["home"] = list(b.location)
flys = [Vector((0.9, -0.3, 0.8)), Vector((1.0, -0.4, 0.3)), Vector((1.1, -0.2, -0.3)), Vector((0.8, -0.5, -0.6))]

cams = {"front": camera("front", (0.15, -2.7, 1.15), (0.1, 0, 1.05), 30),
        "close": camera("close", (0.6, -1.5, 1.35), (0.25, 0, 1.2), 32),
        "side": camera("side", (2.0, -1.0, 1.3), (0.2, 0, 1.15), 32),
        "low": camera("low", (0.8, -1.7, 0.5), (0.2, 0, 1.15), 28),
        "orbit": camera("orbit", (0.2, -2.3, 1.3), (0.2, 0, 1.15), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    B.rotation_euler.z = 0.25 * math.sin(t * 0.5); key(B, fr, "rotation_euler")
    for i, (b, fv) in enumerate(zip(blocks, flys)):
        k = T.u(1, 0.15 + 0.17 * i, 0.4 + 0.17 * i, fr) if fr < T.lines[2][0] else 1.0
        k = max(k, T.u(2, 0.0, 0.2 + 0.2 * i, fr))
        b.location = Vector(b["home"]) + fv * (1 - k); b.rotation_euler = (1.5 * (1 - k), 2 * (1 - k), 0)
        b.hide_render = k <= 0.0; key(b, fr, "location", "rotation_euler", "hide_render")
    # 3 줄: 물림 강조 — 블록이 살짝 벌어졌다 다시 물린다
    gap = 0.06 * math.sin(math.pi * T.u(3, 0.1, 0.9, fr))
    E.location.z = -0.39 - gap; W.location.z = -0.31 - gap; S.location.x = 0.25 + gap
    raise_ = T.u(4, 0.1, 0.8, fr) * (1 - T.u(6, 0.3, 0.9, fr)); bend = T.u(4, 0.3, 1.0, fr) * (1 - T.u(6, 0.3, 0.9, fr))
    S.rotation_euler = (-0.6 * raise_, 0.5 * raise_ + 0.05 * math.sin(t * 2), 0); E.rotation_euler = (-1.4 * bend, 0, 0); W.rotation_euler = (0.3 * bend, 0, 0)
    key(S, fr, "location", "rotation_euler"); key(E, fr, "location", "rotation_euler"); key(W, fr, "location", "rotation_euler")
    oc, _ = cams["orbit"]; a = math.radians(-80 + 50 * math.sin(t * 0.5)); oc.location = (0.2 + 2.3 * math.cos(a), 2.3 * math.sin(a), 1.35); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.6 + 0.15 * math.sin(t * 0.7); key(cc, fr, "location")
끝(T, cams)
