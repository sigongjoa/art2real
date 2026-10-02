"""9-7 네모 기둥 팔 — Vanderpoel 1907 p122. 왼쪽 받침엔 원기둥 팔(밋밋) · 오른쪽엔 네모 기둥 두 마디 팔이 솟아 · 손 쪽으로 가늘어지고(모양 키) · 네모 띠가 감기고 · 모서리를 갈아(베벨) 매끈해진다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def prism(name, L, top, bot, m, parent, loc):
    """곧은 네모 기둥(윗면 크기) + 모양 키 '가늘게'(아랫면 크기로) — 아래(-z) 가 손 쪽."""
    sq = lambda w, d, z: [(-w / 2, -d / 2, z), (w / 2, -d / 2, z), (w / 2, d / 2, z), (-w / 2, d / 2, z)]
    v = sq(*top, L / 2) + sq(*top, -L / 2)
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); put(o, m, parent, loc)
    o.shape_key_add(name="기본"); k = o.shape_key_add(name="가늘게")
    for i, c in enumerate(sq(*top, L / 2) + sq(*bot, -L / 2)): k.data[i].co = c
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments, b.limit_method = 0.005, 8, "NONE"
    for p in me.polygons: p.use_smooth = True
    return o, k, b

stone, wood = mat("받침", (0.93, 0.9, 0.84), 0.8), mat("나무", (0.9, 0.82, 0.68), 0.6)
c1, c2 = mat("위팔", (1.0, 0.62, 0.5), 0.55), mat("아래팔", (0.5, 0.72, 1.0), 0.55)
for x in (-0.5, 0.5): cyl(0.25, 0.4, stone, loc=(x, 0, 0.2), bevel=0.03)
# 왼쪽: 원기둥 팔
C = empty("원기둥팔", loc=(-0.5, 0, 0.4))
cyl(0.09, 0.5, wood, C, (0, 0, 0.25)); CE = empty("원팔꿈치", C, (0, 0, 0.52)); ball(0.08, wood, CE)
cyl(0.075, 0.46, wood, CE, (0, 0, 0.24)); ball(0.07, wood, CE, (0, 0, 0.5), (1, 0.6, 1.3))
# 오른쪽: 네모 기둥 두 마디(위가 어깨 쪽 · 굵음 → 가늘게)
P = empty("네모팔", loc=(0.5, 0, 0.4))
up, uk, ub = prism("위팔", 0.5, (0.2, 0.2), (0.15, 0.13), c1, P, (0, 0, 0.25))
up.rotation_euler.x = math.pi                       # 아래(가는 쪽)를 팔꿈치(위)로
PE = empty("네모팔꿈치", P, (0, 0, 0.52)); ball(0.075, wood, PE)
fo, fk, fb = prism("아래팔", 0.46, (0.17, 0.15), (0.12, 0.07), c2, PE, (0, 0, 0.24)); fo.rotation_euler.x = math.pi
hand = box((0.12, 0.05, 0.17), wood, PE, (0, 0, 0.56), bevel=0.02)
# 네모 띠(단면): 기둥을 따라 놓인 빛 테두리
glow = mat("띠", (1.0, 0.45, 0.1), 0.5, emit=1.0)
bands = []
def band(parent, z, w, d):
    E = empty("띠", parent, (0, 0, z))
    for p, q in [((-w, -d), (w, -d)), ((w, -d), (w, d)), ((w, d), (-w, d)), ((-w, d), (-w, -d))]:
        b = bar((p[0] / 2, p[1] / 2, 0), (q[0] / 2, q[1] / 2, 0), 0.007, glow); b.parent = E
    bands.append(E)
for z, w, d in ((0.08, 0.2, 0.2), (0.25, 0.18, 0.17), (0.42, 0.16, 0.14)): band(P, z, w + 0.02, d + 0.02)
for z, w, d in ((0.1, 0.17, 0.15), (0.25, 0.15, 0.11), (0.4, 0.13, 0.08)): band(PE, z, w + 0.02, d + 0.02)

cams = {"front": camera("front", (0, -3.0, 0.95), (0, 0, 0.85), 30),
        "close": camera("close", (0.85, -1.5, 1.0), (0.5, 0, 0.9), 32),
        "side": camera("side", (2.2, -0.9, 1.0), (0.4, 0, 0.85), 30),
        "low": camera("low", (0.9, -1.6, 0.3), (0.5, 0, 0.9), 28),
        "orbit": camera("orbit", (0.5, -2.2, 1.1), (0.5, 0, 0.85), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    C.rotation_euler.z = 0.5 * math.sin(t * 0.7); CE.rotation_euler.x = 0.3 + 0.1 * math.sin(t); key(C, fr, "rotation_euler"); key(CE, fr, "rotation_euler")
    rise = T.u(1, 0.05, 0.5, fr)
    P.scale = (max(0.001, rise),) * 3; P.rotation_euler.z = 0.5 * math.sin(t * 0.5 + 1) + 2 * (1 - rise); key(P, fr, "scale", "rotation_euler")
    PE.rotation_euler.x = 0.3 + 0.1 * math.sin(t); key(PE, fr, "rotation_euler")
    tp = T.u(2, 0.1, 0.8, fr)
    for k in (uk, fk): k.value = tp; k.keyframe_insert("value", frame=fr)
    for i, E in enumerate(bands):
        k = T.u(4, 0.05 + 0.1 * i, 0.3 + 0.1 * i, fr) * (1 - T.u(5, 0.0, 0.3, fr))
        E.scale = (max(0.001, k),) * 3; key(E, fr, "scale")
        for b in E.children: b.hide_render = k < 0.02; b.keyframe_insert("hide_render", frame=fr)
    sm = T.u(5, 0.2, 0.9, fr)
    for b, mx in ((ub, 0.06), (fb, 0.045)): b.width = 0.005 + (mx - 0.005) * sm; b.id_data.modifiers["b"].keyframe_insert("width", frame=fr)
    oc, _ = cams["orbit"]; a = math.radians(-90 + 60 * math.sin(t * 0.5)); oc.location = (0.5 + 2.2 * math.cos(a), 2.2 * math.sin(a), 1.1); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.5 + 0.35 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
