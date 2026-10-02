"""8-1 상자 머리 — Bridgman 1920 p119. 받침 위 각진 상자 머리가 떨어져 앉고 · 앞/옆/윗면이 켜지고 · 눈썹 · 코 · 턱이 붙고 · 상자가 녹아 달걀 얼굴이 된다."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])

def mesh(name, verts, faces, m, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return put(o, m, parent, loc)
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

def clean(m):                                   # 반투명이어도 뒷면 안 비침(속 빈 상자로 보이던 것)
    m.show_transparent_back = False; m.use_backface_culling = True; m.shadow_method = "HASHED"; return m
stone, skin = mat("받침", (0.93, 0.9, 0.84), 0.8), mat("살", (0.98, 0.76, 0.62), 0.7)
boxm = clean(mat("상자", (0.72, 0.74, 0.96), 0.6, alpha=True))
dark, lip = mat("눈", (0.06, 0.05, 0.06), 0.3), mat("입", (0.9, 0.45, 0.45), 0.6)
cyl(0.34, 0.9, stone, loc=(0, 0, 0.45), bevel=0.03)
cyl(0.14, 0.4, skin, loc=(0, 0.04, 1.1))

H = empty("머리", loc=(0, 0, 1.55))
B = box((0.62, 0.72, 0.8), boxm, H, bevel=0.025)
plates = [box(s, clean(mat("면%d" % i, c, 0.6, emit=0.3, alpha=True)), H, l) for i, (s, c, l) in enumerate([
    ((0.56, 0.012, 0.74), (1.0, 0.55, 0.45), (0, -0.362, 0)),
    ((0.012, 0.66, 0.74), (0.45, 0.85, 0.6), (0.312, 0, 0)),
    ((0.56, 0.66, 0.012), (1.0, 0.85, 0.3), (0, 0, 0.402))])]
egg = ball(0.4, skin, H, (0, 0.02, 0.01), (0.8, 0.95, 1.05))
# 눈썹 · 코(쐐기) · 턱 · 눈 · 입 · 귀
brow = box((0.36, 0.09, 0.06), skin, H, (0, -0.37, 0.13), bevel=0.02)
nose = mesh("코", [(0, 0, 0.1), (-0.07, 0, -0.12), (0.07, 0, -0.12), (0, -0.15, -0.12)], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)], skin, H, (0, -0.37, 0.0))
chin = box((0.22, 0.12, 0.12), skin, H, (0, -0.33, -0.33), bevel=0.03)
eyes = [ball(0.042, dark, H, (s * 0.12, -0.355, 0.05)) for s in (-1, 1)]
mouth = box((0.16, 0.03, 0.025), lip, H, (0, -0.375, -0.2), bevel=0.01)
ears = [ball(0.1, skin, H, (s * 0.33, 0.04, 0.02), (0.35, 0.8, 1.2)) for s in (-1, 1)]
feats = [brow, nose, chin] + eyes + [mouth] + ears
# 상자 면 위 자리 → 달걀 면 위 자리(y): 녹을 때 함께 들어간다
egg_y = {brow.name: -0.35, nose.name: -0.36, chin.name: -0.25, mouth.name: -0.31, eyes[0].name: -0.33, eyes[1].name: -0.33, ears[0].name: 0.04, ears[1].name: 0.04}
box_y = {o.name: o.location.y for o in feats}
egg_x = {ears[0].name: -0.3, ears[1].name: 0.3}; box_x = {o.name: o.location.x for o in feats}
base = {o.name: o.scale.copy() for o in feats + plates}

cams = {"front": camera("front", (0, -2.3, 1.45), (0, 0, 1.3), 35),
        "close": camera("close", (0.25, -1.7, 1.6), (0, 0, 1.52), 35),
        "low": camera("low", (0.7, -1.7, 0.7), (0, 0, 1.35), 30),
        "side": camera("side", (2.0, -1.2, 1.6), (0, 0, 1.35), 35),
        "top": camera("top", (1.0, -1.3, 2.75), (0, 0, 1.4), 32),
        "orbit": camera("orbit", (0, -2.3, 1.5), (0, 0, 1.35), 35)}
ba, sa, pas = alpha_of(boxm), alpha_of(skin), [alpha_of(p.data.materials[0]) for p in plates]

for fr in range(1, T.end + 1):
    # 0 줄: 상자가 떨어져 받침에 앉는다(콩)
    d = T.u(0, 0, 0.35, fr); bounce = 0.12 * math.sin(math.pi * T.u(0, 0.35, 0.55, fr))
    H.location.z = 1.55 + 1.6 * (1 - d) ** 2 + bounce
    # 돌기: 1 줄 기울기, 5 줄 크게 돌기, 6 줄 3/4 로
    rz = 0.35 * math.sin(fr / 20) * (1 - T.u(3, 0, 0.3, fr)) + T.u(2, 0, 1, fr) * -0.5 * (1 - T.u(3, 0, 0.3, fr))
    rz += -1.1 * T.u(5, 0, 0.45, fr) + 1.9 * T.u(5, 0.5, 1, fr) - 0.4 * T.u(6, 0, 0.5, fr)
    rx = -0.25 * math.sin(math.pi * T.u(1, 0, 1, fr))
    H.rotation_euler = (rx, 0, rz); key(H, fr, "location", "rotation_euler")
    # 2 줄: 면 셋이 차례로 켜진다 · 4 줄에서 사라진다
    for i, p in enumerate(plates):
        k = T.u(2, 0.12 + 0.25 * i, 0.3 + 0.25 * i, fr); p.scale = base[p.name] * max(0.001, k) if k < 1 else base[p.name]
        key(p, fr, "scale"); pas[i].default_value = 1 - T.u(3, 0, 0.3, fr); pas[i].keyframe_insert("default_value", frame=fr)
    # 3 줄: 눈썹 → 코 → 턱 → 눈 · 입 · 귀
    order = [0, 1, 2, 3, 3, 3, 4, 4]
    for o, j in zip(feats, order):
        k = T.u(3, 0.1 + 0.18 * j, 0.25 + 0.18 * j, fr) if j < 3 else T.u(4, 0.0, 0.25, fr)
        o.scale = base[o.name] * max(0.001, k * (1 + 0.25 * math.sin(math.pi * k)))
        m_ = T.u(4, 0.15, 0.7, fr); o.location.y = box_y[o.name] + (egg_y[o.name] - box_y[o.name]) * m_
        o.location.x = box_x[o.name] + (egg_x.get(o.name, box_x[o.name]) - box_x[o.name]) * m_; key(o, fr, "scale", "location")
    # 4 줄: 상자가 녹고 달걀 얼굴이 남는다 · 6 줄 끝에 상자 유령이 다시 깜빡
    ghost = 0.35 * T.u(6, 0.4, 0.7, fr)
    ba.default_value = max(1 - T.u(4, 0.15, 0.7, fr), ghost); ba.keyframe_insert("default_value", frame=fr)
    egg.scale = Vector((0.8, 0.95, 1.05)) * max(0.001, T.u(4, 0.15, 0.6, fr)); key(egg, fr, "scale")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 70 * T.u(2, 0, 1, fr) - 70 * T.u(4, 0, 1, fr) + 40 * T.u(4, 0.3, 1, fr))
    oc.location = (2.3 * math.cos(a), 2.3 * math.sin(a), 1.5); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.y = -1.7 + 0.2 * math.sin(fr / 30); key(cc, fr, "location")
끝(T, cams)
