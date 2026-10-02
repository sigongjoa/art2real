"""8-3 구성선 — Bridgman 1920 p127. 고개 돌린 상자 머리 · 눈알 둘이 자리를 못 찾고 떠돈다 → 가운데 세로선 · 가로선 셋이 그어지고 상자와 함께 돈다 → 선이 만나는 곳에 눈 · 코 · 입이 내려앉는다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def mesh(name, verts, faces, m, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return put(o, m, parent, loc)

stone, skin = mat("받침", (0.93, 0.9, 0.84), 0.8), mat("살", (0.98, 0.76, 0.62), 0.7)
boxm, dark, lip = mat("상자", (0.74, 0.76, 0.97), 0.6), mat("눈", (0.06, 0.05, 0.06), 0.3), mat("입", (0.9, 0.45, 0.45), 0.6)
glow, glow2 = mat("세로선", (1.0, 0.25, 0.2), 0.5, emit=0.9), mat("가로선", (1.0, 0.55, 0.05), 0.5, emit=0.9)
cyl(0.34, 0.9, stone, loc=(0, 0, 0.45), bevel=0.03); cyl(0.14, 0.4, skin, loc=(0, 0.04, 1.1))
H = empty("머리", loc=(0, 0, 1.55))
box((0.62, 0.72, 0.8), boxm, H, bevel=0.02)
X, Y, Z, e, w = 0.31, 0.36, 0.4, 0.006, 0.014
# 선: (크기, 자리, 그어지는 축) — 앞면 세로선 + 윗면으로 이어짐 · 가로선 셋은 앞 + 양옆으로 감싼다
lines = [box((w, w, 2 * Z), glow, H, (0, -Y - e, 0)), box((w, 2 * Y, w), glow, H, (0, 0, Z + e))]
lines[0]["ax"] = 2; lines[1]["ax"] = 1
hz = [0.05, -0.12, -0.24]
for z in hz:
    for o, a in ((box((2 * X, w, w), glow2, H, (0, -Y - e, z)), 0), (box((w, 2 * Y, w), glow2, H, (X + e, 0, z)), 1), (box((w, 2 * Y, w), glow2, H, (-X - e, 0, z)), 1)):
        o["ax"] = a; lines.append(o)
base = {o.name: o.scale.copy() for o in lines}
feats = [box((0.34, 0.08, 0.05), skin, H, (0, -Y - 0.03, 0.13), bevel=0.015),
         ball(0.045, dark, H, (-0.12, -Y - 0.01, 0.05)), ball(0.045, dark, H, (0.12, -Y - 0.01, 0.05)),
         mesh("코", [(0, 0, 0.13), (-0.07, 0, -0.12), (0.07, 0, -0.12), (0, -0.15, -0.12)], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)], skin, H, (0, -Y, 0)),
         box((0.16, 0.04, 0.03), lip, H, (0, -Y - 0.01, -0.24), bevel=0.01)]
home = [o.location.copy() for o in feats]
for o in feats: o["s"] = list(o.scale)

cams = {"front": camera("front", (0, -2.3, 1.45), (0, 0, 1.3), 35),
        "close": camera("close", (0.3, -1.7, 1.6), (0, 0, 1.5), 35),
        "low": camera("low", (0.7, -1.7, 0.7), (0, 0, 1.35), 30),
        "side": camera("side", (2.0, -1.2, 1.6), (0, 0, 1.35), 35),
        "top": camera("top", (1.0, -1.3, 2.75), (0, 0, 1.4), 32),
        "orbit": camera("orbit", (0, -2.3, 1.5), (0, 0, 1.35), 35)}

for fr in range(1, T.end + 1):
    t = fr / 24
    turn = -0.7 * (1 - T.u(1, 0, 0.4, fr)) + -0.75 * T.u(4, 0, 0.6, fr) + 1.4 * T.u(6, 0, 0.7, fr)
    tilt = 0.3 * T.u(4, 0.3, 0.9, fr) - 0.5 * T.u(6, 0.2, 0.8, fr) + 0.05 * math.sin(t * 1.3)
    H.rotation_euler = (tilt, 0, turn + 0.08 * math.sin(t * 0.9)); key(H, fr, "rotation_euler")
    # 선 긋기: 2 줄 세로선 둘 · 3 줄 가로선 셋(앞 → 옆)
    for i, o in enumerate(lines):
        k = T.u(2, 0.1 + 0.35 * i, 0.5 + 0.35 * i, fr) if i < 2 else T.u(3, 0.05 + 0.25 * ((i - 2) // 3), 0.35 + 0.25 * ((i - 2) // 3), fr)
        s = base[o.name].copy(); s[o["ax"]] *= max(0.001, k); o.scale = s; o.hide_render = k < 0.02; key(o, fr, "scale", "hide_render")
    # 이목구비: 0 줄 엉뚱한 데서 떠돌고 · 1 줄 사라졌다가 · 5 줄 선 위로 내려앉는다
    for j, o in enumerate(feats):
        land = T.u(5, 0.1 + 0.12 * j, 0.45 + 0.12 * j, fr)
        wander = Vector((0.35 * math.sin(t * 2.1 + j * 1.7), -0.25, 0.3 * math.cos(t * 1.7 + j)))
        show = (1 - T.u(1, 0, 0.3, fr)) if j in (1, 2) else 0.0
        show = max(show, land)
        o.location = home[j] + wander * (1 - land) + Vector((0, 0, 0.5)) * (1 - land) * (fr >= T.lines[5][0])
        o.scale = Vector(o["s"]) * max(0.001, show); o.hide_render = show < 0.02; key(o, fr, "location", "scale", "hide_render")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 45 * math.sin(t * 0.6)); oc.location = (2.3 * math.cos(a), 2.3 * math.sin(a), 1.5 + 0.3 * math.sin(t * 0.4)); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.y = -1.7 + 0.15 * math.sin(t * 0.8); key(cc, fr, "location")
끝(T, cams)
