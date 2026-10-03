"""8-4 머리 면 — Bridgman 1920 p129. 매끈한 달걀 얼굴이 판 조각 70 여 개로 터졌다가 다시 모여 각진 머리가 되고 · 해를 돌리면 면마다 밝기가 갈린다."""
import bpy, bmesh, math, random
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1]); random.seed(4)
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

stone, skin = mat("받침", (0.93, 0.9, 0.84), 0.8), mat("살", (0.98, 0.76, 0.62), 0.7)
dark = mat("눈", (0.06, 0.05, 0.06), 0.3)
cyl(0.34, 0.9, stone, loc=(0, 0, 0.45), bevel=0.03); cyl(0.14, 0.4, skin, loc=(0, 0.04, 1.1))
H = empty("머리", loc=(0, 0, 1.55))

def shape(v):                                   # 공 → 얼굴: 앞은 눌러 판판 · 턱은 좁게 · 뒤통수는 크게
    x, y, z = v
    x *= 0.8 * (1 - 0.3 * max(0.0, -z) / 0.4); y *= 0.95; z *= 1.08
    if y < -0.22: y = -0.22 + (y + 0.22) * 0.45
    if y > 0: y *= 1.1
    return Vector((x, y, z))
smooth = ball(0.4, skin, H, (0, 0, 0)); smooth.data.vertices.foreach_set("co", [c for v in smooth.data.vertices for c in shape(v.co)]); smooth.data.update()
s_feats = [ball(0.04, dark, H, (s * 0.12, -0.3, 0.06)) for s in (-1, 1)]

bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=7, radius=0.4)
pieces = []
for f in bm.faces:
    pts = [shape(v.co) for v in f.verts]; c = sum(pts, Vector()) / len(pts)
    me = bpy.data.meshes.new("조각"); me.from_pydata([(p - c) * 0.97 for p in pts], [], [list(range(len(pts)))]); me.update()
    o = bpy.data.objects.new("조각", me); bpy.context.scene.collection.objects.link(o); put(o, skin, H, c)
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.02
    n = c.normalized(); o["home"] = list(c); o["fly"] = list(n * random.uniform(0.3, 0.55) + Vector((random.uniform(-.1, .1), -0.15, random.uniform(-.1, .15))))
    o["spin"] = [random.uniform(-2, 2) for _ in range(3)]; pieces.append(o)
bm.free()
# 코 쐐기 · 눈썹 판 · 눈 — 조각과 같이 날아온다
nm = bpy.data.meshes.new("코"); nm.from_pydata([(0, 0, 0.1), (-0.07, 0, -0.12), (0.07, 0, -0.12), (0, -0.14, -0.12)], [], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
nose = bpy.data.objects.new("코", nm); bpy.context.scene.collection.objects.link(nose); put(nose, skin, H, (0, -0.3, -0.02))
brow = box((0.34, 0.08, 0.06), skin, H, (0, -0.3, 0.15))
eyes = [ball(0.04, dark, H, (s * 0.12, -0.3, 0.06)) for s in (-1, 1)]
for o, d in [(nose, (0, -1.0, 0.1)), (brow, (0, -0.9, 0.5)), (eyes[0], (-0.6, -0.8, 0)), (eyes[1], (0.6, -0.8, 0))]:
    o["home"] = list(o.location); o["fly"] = list(d); o["spin"] = [1, -1, 0.5]; pieces.append(o)
for o in pieces: o["s0"] = list(o.scale)
sun = next(o for o in bpy.data.objects if o.type == "LIGHT")

cams = {"front": camera("front", (0, -2.4, 1.45), (0, 0, 1.3), 35),
        "close": camera("close", (0.3, -1.7, 1.6), (0, 0, 1.5), 35),
        "low": camera("low", (0.7, -1.7, 0.7), (0, 0, 1.35), 30),
        "side": camera("side", (2.0, -1.3, 1.6), (0, 0, 1.4), 35),
        "top": camera("top", (1.0, -1.4, 2.75), (0, 0, 1.4), 32),
        "orbit": camera("orbit", (0, -2.3, 1.5), (0, 0, 1.4), 35)}

for fr in range(1, T.end + 1):
    t = fr / 24
    H.rotation_euler = (0, 0, -0.35 + 0.3 * math.sin(t * 0.8)); key(H, fr, "rotation_euler")
    show_smooth = 1 - T.u(1, 0.05, 0.2, fr)
    for o in [smooth] + s_feats:
        o.scale = (max(0.001, show_smooth),) * 3; key(o, fr, "scale")
    out = T.u(1, 0.1, 0.6, fr) * (1 - T.u(3, 0.0, 0.7, fr))     # 터짐 → 2 줄 떠 있음 → 3 줄 모임
    for o in pieces:
        h, d, sp = Vector(o["home"]), Vector(o["fly"]), o["spin"]
        bob = 0.04 * math.sin(t * 2 + h.x * 9) * out
        o.location = h + d * out + Vector((0, 0, bob))
        o.rotation_euler = (sp[0] * out, sp[1] * out, sp[2] * out)
        o.scale = Vector(o["s0"]) * max(0.001, 1 - show_smooth); key(o, fr, "location", "rotation_euler", "scale")
    # 4–5 줄: 해가 한 바퀴 쓸고 지나간다
    a = T.u(4, 0.2, 1, fr) - 0.5 * T.u(5, 0.3, 1, fr)
    sun.rotation_euler = (math.radians(50 + 10 * a), 0, math.radians(-30 + 110 * a)); key(sun, fr, "rotation_euler")
    oc, _ = cams["orbit"]; b = math.radians(-90 + 50 * math.sin(t * 0.5)); oc.location = (2.3 * math.cos(b), 2.3 * math.sin(b), 1.6); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.y = -1.7 + 0.15 * math.sin(t * 0.8); key(cc, fr, "location")
끝(T, cams)
