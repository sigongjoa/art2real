"""9-12 손목뼈 여덟 — Bridgman 1920 Hundred Hands p167. 아래팔뼈 둘과 손허리뼈 다섯 사이 빈 틈으로 각진 조각 여덟이 사방에서 날아와 두 줄(넷 · 넷)로 맞물린다 · 손목 블록이 통째로 꺾인다."""
import bpy, math, random
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1]); random.seed(12)
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def pebble(r, m, parent, loc, scale):               # 각진 조각: 다면체 공
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r); o = bpy.context.object; o.scale = scale
    return put(o, m, parent, loc)

bone = mat("뼈", (0.96, 0.92, 0.82), 0.6)
cyl(0.3, 0.3, mat("받침", (0.93, 0.9, 0.84), 0.8), loc=(0, 0, 0.15), bevel=0.03)
A = empty("팔", loc=(0, 0, 0.3))
cyl(0.075, 0.7, bone, A, (-0.08, 0, 0.35)); cyl(0.05, 0.7, bone, A, (0.11, 0, 0.35))
ball(0.09, bone, A, (-0.08, 0, 0.7), (1.1, 0.9, 0.5)); ball(0.06, bone, A, (0.11, 0, 0.7), (1, 1, 0.6))
W = empty("손목", A, (0, 0, 0.76))
cols = [(1.0, 0.55, 0.45), (1.0, 0.75, 0.35), (0.95, 0.9, 0.4), (0.5, 0.85, 0.55), (0.45, 0.8, 0.9), (0.5, 0.6, 1.0), (0.75, 0.55, 1.0), (1.0, 0.6, 0.8)]
pieces = []
for row in range(2):
    for i in range(4):
        x = -0.16 + 0.105 * i; z = 0.06 + 0.1 * row
        p = pebble(0.06, mat("손목뼈%d" % len(pieces), cols[len(pieces)], 0.5), W, (x, 0, z), (0.95 + 0.15 * random.random(), 0.75, 0.85 + 0.15 * random.random()))
        p.rotation_euler = (random.uniform(-.3, .3), random.uniform(-.3, .3), random.uniform(-.3, .3))
        p["home"] = list(p.location); p["rot"] = list(p.rotation_euler)
        ang = random.uniform(0, 2 * math.pi); p["fly"] = [1.2 * math.cos(ang), -0.6 - 0.6 * random.random(), 0.6 * math.sin(ang) + 0.3]
        pieces.append(p)
# 손허리뼈 다섯(부채꼴)
for i, (x, a) in enumerate(((-0.17, 0.25), (-0.085, 0.08), (0.0, 0.0), (0.085, -0.07), (0.165, -0.18))):
    p0 = Vector((x * 0.9, 0, 0.25)); p1 = p0 + Vector((math.sin(-a) * 0.36 if i else -0.18, 0, 0.36 if i else 0.2))
    if i == 0: p0 = Vector((-0.2, -0.02, 0.18))
    b = bar(p0, p1, 0.025, bone); b.parent = W; ball(0.035, bone, W, p1)

cams = {"front": camera("front", (0.2, -2.4, 1.0), (0, 0, 0.95), 30),
        "close": camera("close", (0.3, -1.3, 1.1), (0, 0, 1.1), 32),
        "side": camera("side", (1.6, -0.8, 1.1), (0, 0, 1.05), 30),
        "low": camera("low", (0.5, -1.4, 0.55), (0, 0, 1.05), 26),
        "orbit": camera("orbit", (0, -1.9, 1.15), (0, 0, 1.05), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    A.rotation_euler.z = 0.3 * math.sin(t * 0.5) + 0.6 * T.u(5, 0, 1, fr) * (1 - T.u(6, 0.5, 1, fr)); key(A, fr, "rotation_euler")
    # 0 줄: 틈은 비어 있고 조각들이 둘레를 맴돈다 · 1–3 줄: 날아와 박힌다(아래 줄 먼저)
    for i, p in enumerate(pieces):
        h, f = Vector(p["home"]), Vector(p["fly"])
        if fr < T.lines[1][0]: k = 0.0
        else: k = T.u(1, 0.1 + 0.1 * i, 0.4 + 0.1 * i, fr) if i < 4 else max(T.u(1, 0.5 + 0.06 * (i - 4), 0.8 + 0.05 * (i - 4), fr), 0)
        if fr >= T.lines[3][0]: k = 1.0
        orbit = Vector((math.cos(t * 1.5 + i), 0, math.sin(t * 1.5 + i))) * 0.08 * (1 - k)
        p.location = h + f * (1 - k) + orbit
        r = p["rot"]; p.rotation_euler = (r[0] + 4 * (1 - k), r[1] + 3 * (1 - k), r[2])
        key(p, fr, "location", "rotation_euler")
    bend = math.sin(2 * math.pi * T.u(6, 0.05, 0.95, fr)) * 0.6 + 0.4 * math.sin(math.pi * T.u(4, 0.2, 1, fr))
    W.rotation_euler = (bend, 0, 0); key(W, fr, "rotation_euler")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 60 * math.sin(t * 0.5)); oc.location = (1.9 * math.cos(a), 1.9 * math.sin(a), 1.2); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.3 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
