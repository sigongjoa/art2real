"""9-10 손 각기둥 — Bridgman 1920 p47. 받침에서 솟은 아래팔 끝에 손목 기둥(좁고 두툼) · 손등 기둥(넓고 납작)이 차례로 끼고 · 둘이 꺾이고 비틀리며 돈다 · 끝에 손가락 마디가 손등 끝에서 자라 오므린다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

wood = mat("나무", (0.92, 0.84, 0.7), 0.6)
wm, hm, fm = mat("손목", (1.0, 0.6, 0.48), 0.55), mat("손등", (0.5, 0.68, 1.0), 0.55), mat("손가락", (1.0, 0.85, 0.42), 0.55)
cyl(0.3, 0.3, mat("받침", (0.93, 0.9, 0.84), 0.8), loc=(0, 0, 0.15), bevel=0.03)
A = empty("팔", loc=(0, 0, 0.3))
box((0.2, 0.16, 0.6), wood, A, (0, 0, 0.3), bevel=0.04)
W = empty("손목", A, (0, 0, 0.62))
wrist = box((0.22, 0.16, 0.18), wm, W, (0, 0, 0.09), bevel=0.025)
H = empty("손", W, (0, 0, 0.19))
hand = box((0.36, 0.1, 0.4), hm, H, (0, 0, 0.21), bevel=0.025)
fingers = []
for i, (x, L) in enumerate(((-0.13, 0.26), (-0.045, 0.3), (0.045, 0.29), (0.13, 0.24))):
    par, z, chain = H, 0.42, []
    for k in range(3):
        e = empty("마디", par, (x if k == 0 else 0, 0, z)); box((0.075, 0.08, L / 3 - 0.01), fm, e, (0, 0, L / 6), bevel=0.015); chain.append(e); par, z = e, L / 3
    fingers.append(chain)
th, z, tchain = H, 0.06, []                          # 엄지: 손등 옆에서 비스듬히
for k in range(2):
    e = empty("엄지", th, (0.2 if k == 0 else 0, -0.02 if k == 0 else 0, z)); box((0.08, 0.085, 0.12), fm, e, (0, 0, 0.06), bevel=0.015); tchain.append(e); th, z = e, 0.13
tchain[0].rotation_euler = (0, -0.7, 0)
bits = [c for ch in fingers for c in ch] + tchain
for b in bits: b["s"] = list(b.scale)

cams = {"front": camera("front", (0.3, -2.7, 1.0), (0, 0, 0.95), 30),
        "close": camera("close", (0.45, -1.5, 1.2), (0, 0, 1.15), 32),
        "side": camera("side", (2.0, -0.8, 1.1), (0, 0, 1.0), 30),
        "low": camera("low", (0.5, -1.7, 0.4), (0, 0, 1.0), 26),
        "orbit": camera("orbit", (0, -2.3, 1.1), (0, 0, 1.0), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    # 0 줄: 손등 · 손목이 공중에서 맴돌다 · 1 줄에 내려와 끼운다
    land_w = T.u(1, 0.1, 0.5, fr); land_h = T.u(1, 0.35, 0.8, fr)
    W.location.z = 0.62 + 0.6 * (1 - land_w); W.rotation_euler.z = 3 * (1 - land_w) * math.sin(t)
    H.location.z = 0.19 + 0.5 * (1 - land_h); H.rotation_euler.z = -2.5 * (1 - land_h) * math.sin(t * 1.2)
    # 2 · 3 줄: 각 기둥이 통 부푼다 · 4–5 줄: 꺾고 · 비틀고 · 기울인다
    for o, base, j in ((wrist, (0.22, 0.16, 0.18), 2), (hand, (0.36, 0.1, 0.4), 3)):
        k = 1 + 0.2 * math.sin(math.pi * T.u(j, 0.1, 0.6, fr)); o.scale = Vector(base) * k; key(o, fr, "scale")
    m = T.u(4, 0.0, 1.0, fr) + T.u(5, 0.0, 1.0, fr)
    bend = 0.7 * math.sin(math.pi * m) * (1 - T.u(6, 0.2, 0.6, fr)); dev = 0.35 * math.sin(2 * math.pi * T.u(5, 0, 1, fr))
    A.rotation_euler.z = 0.3 * math.sin(t * 0.5) + 1.2 * math.sin(math.pi * T.u(4, 0.1, 0.9, fr)) + 0.5 * T.u(6, 0, 0.5, fr)
    W.rotation_euler.x = bend * 0.5; H.rotation_euler.x = H.rotation_euler.x if False else bend * 0.6; H.rotation_euler.y = dev
    key(A, fr, "rotation_euler"); key(W, fr, "location", "rotation_euler"); key(H, fr, "location", "rotation_euler")
    # 6 줄: 손가락이 자라 살짝 오므린다
    g = T.u(6, 0.05, 0.5, fr); curl = 0.35 * T.u(6, 0.55, 0.95, fr)
    for i, b in enumerate(bits):
        b.scale = Vector(b["s"]) * max(0.001, g); b.hide_render = g < 0.02
        if b not in tchain: b.rotation_euler.x = curl
        key(b, fr, "scale", "hide_render", "rotation_euler")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 70 * math.sin(t * 0.5)); oc.location = (2.3 * math.cos(a), 2.3 * math.sin(a), 1.2); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.45 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
