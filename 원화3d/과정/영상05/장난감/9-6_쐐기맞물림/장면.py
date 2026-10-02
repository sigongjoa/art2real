"""9-6 쐐기 맞물림 — Bridgman 1920 p79. 받침 위에 세운 큰 팔: 위팔 블록 → 아래팔 블록이 내려와 비스듬한 끝에 쐐기로 끼고 → 손목 · 손 블록이 끼운다 · 아래팔 위/아래 단면 테두리(두툼 → 납작) · 아래팔이 돌아도 마디는 각지게 남는다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def taper(name, L, top, bot, m, parent, loc, slant=0.0):
    """가늘어지는 각기둥: 윗면 (폭, 깊이) · 아랫면 (폭, 깊이) · 위아래 끝면이 x 쪽으로 slant 만큼 기운 쐐기."""
    (w1, d1), (w2, d2) = top, bot
    v = [(x, y, L / 2 + slant * x) for x, y in ((-w1 / 2, -d1 / 2), (w1 / 2, -d1 / 2), (w1 / 2, d1 / 2), (-w1 / 2, d1 / 2))] + \
        [(x, y, -L / 2 + slant * x) for x, y in ((-w2 / 2, -d2 / 2), (w2 / 2, -d2 / 2), (w2 / 2, d2 / 2), (-w2 / 2, d2 / 2))]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.015, 2
    return put(o, m, parent, loc)
def frame_rect(w, d, m, parent, loc):               # 단면 테두리(빛나는 네모)
    E = empty("단면", parent, loc)
    for p, q in [((-w, -d), (w, -d)), ((w, -d), (w, d)), ((w, d), (-w, d)), ((-w, d), (-w, -d))]:
        b = bar((p[0] / 2, p[1] / 2, 0), (q[0] / 2, q[1] / 2, 0), 0.008, m); b.parent = E
    return E

stone = mat("받침", (0.93, 0.9, 0.84), 0.8)
cyl(0.32, 0.5, stone, loc=(0, 0, 0.25), bevel=0.03)
cols = [(1.0, 0.82, 0.35), (0.45, 0.8, 0.6), (0.5, 0.65, 1.0), (1.0, 0.6, 0.5)]
A = empty("팔", loc=(0, 0, 0.5))
upper = taper("위팔", 0.5, (0.24, 0.2), (0.2, 0.18), mat("위팔", cols[0], 0.55), A, (0, 0, 0.25), slant=0.35)
F = empty("아래팔돌림", A, (0, 0, 0.49))
fore = taper("아래팔", 0.52, (0.2, 0.08), (0.26, 0.2), mat("아래팔", cols[1], 0.55), F, (0, 0, 0.27), slant=0.35)
W = empty("손목", F, (0, 0, 0.53))
wrist = taper("손목", 0.12, (0.2, 0.07), (0.2, 0.08), mat("손목", cols[2], 0.55), W, (0, 0, 0.06), slant=0.3)
hand = taper("손", 0.24, (0.19, 0.04), (0.2, 0.06), mat("손", cols[3], 0.55), W, (0, 0, 0.25), slant=-0.1)
glow = mat("테두리", (1.0, 0.4, 0.15), 0.5, emit=1.0)
rects = [frame_rect(0.3, 0.24, glow, F, (0, 0, 0.06)), frame_rect(0.24, 0.12, glow, F, (0, 0, 0.5))]
drops = [(F, 0.52), (W, 0.55)]

cams = {"front": camera("front", (0.1, -3.0, 1.15), (0, 0, 1.05), 30),
        "close": camera("close", (0.4, -1.6, 1.15), (0, 0, 1.05), 32),
        "side": camera("side", (2.2, -1.2, 1.2), (0, 0, 1.05), 30),
        "low": camera("low", (0.5, -1.8, 0.35), (0, 0, 1.1), 26),
        "orbit": camera("orbit", (0, -2.4, 1.2), (0, 0, 1.05), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    A.rotation_euler.z = 0.4 * math.sin(t * 0.5); key(A, fr, "rotation_euler")
    # 0 줄: 셋이 떠서 돈다 · 1 줄: 쌓인다 · 2 줄: 아래팔이 들렸다 쐐기로 끼고 · 3 줄: 손목이 낀다
    float_ = 1 - T.u(1, 0.1, 0.7, fr)
    lift_f = 0.35 * math.sin(math.pi * T.u(2, 0.0, 0.7, fr)); lift_w = 0.3 * math.sin(math.pi * T.u(3, 0.0, 0.7, fr))
    F.location.z = 0.49 + 0.5 * float_ + lift_f; W.location.z = 0.53 + 0.4 * float_ + lift_w
    F.rotation_euler.z = 1.5 * float_ * math.sin(t) + 1.0 * T.u(5, 0.1, 0.9, fr) * (1 - T.u(6, 0.4, 1, fr))
    W.rotation_euler.z = -1.2 * float_ * math.sin(t * 1.3)
    W.rotation_euler.x = 0.4 * T.u(5, 0.3, 0.9, fr) * (1 - T.u(6, 0.4, 1, fr))
    key(F, fr, "location", "rotation_euler"); key(W, fr, "location", "rotation_euler")
    for i, r in enumerate(rects):
        k = T.u(4, 0.1 + 0.4 * i, 0.4 + 0.4 * i, fr) * (1 - T.u(5, 0.6, 1, fr))
        r.scale = (max(0.001, k),) * 3; key(r, fr, "scale")
        for b in r.children: b.hide_render = k < 0.02; b.keyframe_insert("hide_render", frame=fr)
    oc, _ = cams["orbit"]; a = math.radians(-90 + 60 * math.sin(t * 0.5)); oc.location = (2.4 * math.cos(a), 2.4 * math.sin(a), 1.3); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.4 * math.cos(t * 0.6); cc.location.z = 1.0 + 0.25 * math.sin(t * 0.4); key(cc, fr, "location")
끝(T, cams)
