"""8-5 개와 사람 — Vanderpoel 1907 p59. 받침 둘 위에 같은 상자 둘 · 사람 쪽은 위로 세우고 개 쪽은 앞으로 늘여 기울인다 · 모서리 조각이 떨어지고 안에서 사람 머리 · 개 머리가 나온다."""
import bpy, math, random
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1]); random.seed(5)
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def clean(m):
    m.show_transparent_back = False; m.use_backface_culling = True; m.shadow_method = "HASHED"; return m
def wedge(m, parent, loc, s=1.0):
    me = bpy.data.meshes.new("코"); me.from_pydata([(0, 0, 0.1 * s), (-0.07 * s, 0, -0.12 * s), (0.07 * s, 0, -0.12 * s), (0, -0.14 * s, -0.12 * s)], [], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
    o = bpy.data.objects.new("코", me); bpy.context.scene.collection.objects.link(o); return put(o, m, parent, loc)

stone, skin, fur = mat("받침", (0.93, 0.9, 0.84), 0.8), mat("살", (0.98, 0.76, 0.62), 0.7), mat("개털", (0.85, 0.62, 0.38), 0.8)
dark = mat("눈", (0.05, 0.05, 0.06), 0.3)
heads = {}
for nm, x in (("사람", -0.62), ("개", 0.62)):
    cyl(0.3, 0.9, stone, loc=(x, 0, 0.45), bevel=0.03)
    bm_ = clean(mat("상자" + nm, (0.74, 0.76, 0.97), 0.6, alpha=True))
    R = empty(nm, loc=(x, 0, 1.25))
    B = box((1, 1, 1), bm_, R, (0, 0, 0), bevel=0.02)
    I = empty(nm + "속", R)                       # 깎고 나면 남는 머리
    heads[nm] = dict(R=R, B=B, I=I, a=alpha_of(bm_), x=x)
# 사람: 달걀 + 눈썹 · 코 · 턱 · 귀
h = heads["사람"]["I"]; cyl(0.11, 0.35, skin, loc=(-0.62, 0.03, 1.0))
ball(0.3, skin, h, (0, 0.02, 0.18), (0.82, 0.95, 1.15))
box((0.3, 0.07, 0.05), skin, h, (0, -0.28, 0.27), bevel=0.015)
for s in (-1, 1): ball(0.035, dark, h, (s * 0.1, -0.26, 0.2)); ball(0.07, skin, h, (s * 0.25, 0.04, 0.17), (0.4, 0.8, 1.2))
wedge(skin, h, (0, -0.28, 0.12), 0.8); box((0.18, 0.1, 0.09), skin, h, (0, -0.24, -0.08), bevel=0.02)
# 개: 머리통 상자 + 주둥이 상자 + 코 + 귀
d = heads["개"]["I"]; cyl(0.12, 0.35, fur, loc=(0.62, 0.12, 1.0))
box((0.4, 0.42, 0.38), fur, d, (0, 0.12, 0.12), bevel=0.08)
box((0.24, 0.4, 0.2), fur, d, (0, -0.25, 0.0), bevel=0.06)
ball(0.05, dark, d, (0, -0.46, 0.06))
for s in (-1, 1):
    ball(0.035, dark, d, (s * 0.12, -0.09, 0.2)); cone(0.08, 0.2, fur, d, (s * 0.15, 0.18, 0.37), (0.2, s * 0.35, 0))

# 상자 크기: 처음 같은 상자 → 사람은 세로로 · 개는 앞으로 길게
SIZE0 = Vector((0.6, 0.6, 0.6)); SIZE = {"사람": Vector((0.6, 0.62, 0.8)), "개": Vector((0.48, 1.0, 0.5))}
OFF = {"사람": Vector((0, 0, 0.12)), "개": Vector((0, -0.08, 0.1))}
chips = []
for nm, H in heads.items():
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                c = box((0.16, 0.16, 0.16), H["B"].data.materials[0], H["R"], (0, 0, 0)); c.rotation_euler = (0.6, 0.6, 0.6)
                chips.append((c, nm, Vector((sx, sy, sz)), Vector((sx * random.uniform(.5, 1), sy * random.uniform(.3, .8) - 0.3, random.uniform(.6, 1.2)))))

cams = {"front": camera("front", (0, -3.3, 1.3), (0, 0, 1.15), 30),
        "close": camera("close", (0, -2.3, 1.45), (0, 0, 1.25), 32),
        "low": camera("low", (0.3, -2.4, 0.5), (0, 0, 1.2), 26),
        "hum": camera("hum", (-0.35, -1.55, 1.45), (-0.62, 0, 1.3), 35),
        "dog": camera("dog", (1.9, -1.0, 1.4), (0.62, -0.1, 1.25), 35),
        "side": camera("side", (2.6, -1.8, 1.5), (0, 0, 1.2), 30),
        "top": camera("top", (0.6, -2.0, 3.0), (0, 0, 1.2), 30),
        "orbit": camera("orbit", (0, -3.0, 1.4), (0, 0, 1.2), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    for i, (nm, H) in enumerate(heads.items()):
        drop = T.u(0, 0.05 + 0.3 * i, 0.35 + 0.3 * i, fr); bounce = 0.1 * math.sin(math.pi * T.u(0, 0.35 + 0.3 * i, 0.5 + 0.3 * i, fr))
        grow = T.u(2, 0.1, 0.7, fr) if nm == "사람" else T.u(3, 0.05, 0.6, fr)
        H["R"].location = (H["x"], 0, 1.25 + 1.8 * (1 - drop) ** 2 + bounce)
        tilt = 0.18 * T.u(3, 0.4, 0.9, fr) if nm == "개" else 0
        H["R"].rotation_euler = (tilt, 0, 0.25 * math.sin(t * 1.2 + i * 2) * (1 - T.u(4, 0, 0.3, fr)) + 0.5 * math.sin(t * 0.9 + i) * T.u(6, 0, 0.4, fr))
        key(H["R"], fr, "location", "rotation_euler")
        H["B"].scale = SIZE0 + (SIZE[nm] - SIZE0) * grow; H["B"].location = OFF[nm] * grow; key(H["B"], fr, "scale", "location")
        H["a"].default_value = 1 - T.u(4, 0.3, 0.75, fr); H["a"].keyframe_insert("default_value", frame=fr)
        k = T.u(4, 0.3, 0.7, fr) if nm == "사람" else T.u(4, 0.3, 0.7, fr)
        H["I"].scale = (max(0.001, 0.85 + 0.15 * k),) * 3; H["I"].hide_render = k <= 0; key(H["I"], fr, "scale", "hide_render")
        for o in H["I"].children:
            o.hide_render = k <= 0; o.keyframe_insert("hide_render", frame=fr)
    # 깎기: 4 줄에 모서리 조각이 튕겨 떨어진다
    for c, nm, sg, v in chips:
        grow = T.u(2, 0.1, 0.7, fr) if nm == "사람" else T.u(3, 0.05, 0.6, fr)
        size = SIZE0 + (SIZE[nm] - SIZE0) * grow
        tt = max(0.0, (fr - T.lines[4][0]) / 24 - 0.2)
        p = OFF[nm] * grow + Vector((sg.x * size.x, sg.y * size.y, sg.z * size.z)) * 0.46 + v * tt * 1.2 + Vector((0, 0, -2.5 * tt * tt))
        c.location = p; c.scale = (max(0.001, 1 - T.u(4, 0.5, 0.9, fr)) * 0.13,) * 3; c.hide_render = fr < T.lines[4][0] + 3 or T.u(4, 0.5, 0.9, fr) > 0.97; c.keyframe_insert("hide_render", frame=fr); c.rotation_euler = (0.6 + 4 * tt, 0.6 + 3 * tt, 0.6)
        key(c, fr, "location", "scale", "rotation_euler")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 40 * math.sin(t * 0.6)); oc.location = (3.0 * math.cos(a), 3.0 * math.sin(a), 1.5); key(oc, fr, "location")
    fc, _ = cams["front"]; fc.location.x = 0.2 * math.sin(t * 0.5); key(fc, fr, "location")
끝(T, cams)
