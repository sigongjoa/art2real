"""9-11 주먹 상자 — Bridgman 1920 Hundred Hands p64. 손 앞 허공에 빛나는 꺾인 직선이 손 윤곽을 한 획씩 긋고 · 그 안에서 손바닥 상자 · 손가락 마디 상자가 솟고 · 마디마다 접혀 모서리 있는 주먹 상자가 된다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

wood = mat("나무", (0.92, 0.84, 0.7), 0.6)
hm, fm = mat("손등", (0.5, 0.68, 1.0), 0.55), mat("손가락", (1.0, 0.72, 0.5), 0.55)
cyl(0.3, 0.3, mat("받침", (0.93, 0.9, 0.84), 0.8), loc=(0, 0, 0.15), bevel=0.03)
A = empty("팔", loc=(0, 0, 0.3)); box((0.2, 0.16, 0.6), wood, A, (0, 0, 0.3), bevel=0.04)
box((0.22, 0.16, 0.18), wood, A, (0, 0, 0.71), bevel=0.025)
H = empty("손", A, (0, 0, 0.81))
palm = box((0.36, 0.11, 0.4), hm, H, (0, 0, 0.21), bevel=0.02)
fingers = []
for x, L in ((-0.13, 0.26), (-0.045, 0.3), (0.045, 0.29), (0.13, 0.24)):
    par, z, chain = H, 0.42, []
    for k in range(3):
        e = empty("마디", par, (x if k == 0 else 0, 0, z)); box((0.078, 0.09, L / 3 - 0.008), fm, e, (0, 0, L / 6), bevel=0.012); chain.append(e); par, z = e, L / 3
    fingers.append(chain)
th, z, tchain = H, 0.05, []
for k in range(2):
    e = empty("엄지", th, (-0.2 if k == 0 else 0, 0, z)); box((0.085, 0.09, 0.13), fm, e, (0, 0, 0.065), bevel=0.012); tchain.append(e); th, z = e, 0.14
segs = [palm] + [c for ch in fingers for c in ch] + tchain
for o in segs: o["s"] = list(o.scale)
# 꺾인 직선 윤곽(손 앞 허공 · 손 좌표)
P = [(0.15, 0), (-0.17, 0), (-0.19, 0.22), (-0.34, 0.33), (-0.35, 0.45), (-0.2, 0.42), (-0.19, 0.7), (-0.05, 0.75), (0.1, 0.73), (0.19, 0.65), (0.19, 0.3), (0.15, 0)]
glow = mat("선", (1.0, 0.4, 0.15), 0.5, emit=1.2)
lines = []
for p, q in zip(P, P[1:]):
    b = bar((p[0], -0.16, p[1]), (q[0], -0.16, q[1]), 0.011, glow); b.parent = H; b["s"] = list(b.scale); lines.append(b)
    b.location = Vector(b.location)                     # 손 좌표 그대로(부모 원점 기준)

cams = {"front": camera("front", (0.2, -2.6, 1.1), (0, 0, 1.05), 30),
        "close": camera("close", (0.35, -1.5, 1.2), (0, 0, 1.15), 32),
        "side": camera("side", (1.9, -1.0, 1.15), (0, 0, 1.05), 30),
        "low": camera("low", (0.5, -1.7, 0.45), (0, 0, 1.05), 26),
        "orbit": camera("orbit", (0, -2.3, 1.2), (0, 0, 1.05), 30)}
n = len(lines)
for fr in range(1, T.end + 1):
    t = fr / 24
    # 1–2 줄: 한 획씩 긋는다(막대가 길이 방향으로 자란다)
    for i, b in enumerate(lines):
        u = T.u(1, i / n * 0.9, (i + 1) / n * 0.9, fr) if fr < T.lines[2][0] else 1.0
        u *= 1 - T.u(4, 0.0, 0.4, fr)
        s = Vector(b["s"]); s.z *= max(0.001, u); b.scale = s; b.hide_render = u < 0.02; key(b, fr, "scale", "hide_render")
    # 0 줄: 맨 처음엔 주먹을 쥔 채 · 1 줄에 손이 사라지고 선만 · 3 줄: 상자가 선 안에서 솟는다
    grow = T.u(3, 0.0, 0.7, fr) if fr >= T.lines[1][0] else 1.0
    hide = fr >= T.lines[1][0] and grow < 0.02
    for i, o in enumerate(segs):
        k = min(1.0, max(0.0, grow * 1.6 - i * 0.04)) if fr >= T.lines[1][0] else 1.0
        o.scale = Vector(o["s"]) * max(0.001, k); o.hide_render = k < 0.02; key(o, fr, "scale", "hide_render")
    # 접기: 0 줄 주먹 → 1 줄 펴짐 · 4–5 줄 다시 접힘
    fold = (1 - T.u(0, 0.6, 0.95, fr)) if fr < T.lines[1][0] else T.u(4, 0.15, 0.95, fr)
    for ch in fingers:
        for k, e in enumerate(ch): e.rotation_euler.x = fold * (1.45, 1.6, 1.3)[k]; key(e, fr, "rotation_euler")
    tchain[0].rotation_euler = (fold * 0.9, -0.5 + 0.3 * fold, -0.6 * fold); tchain[1].rotation_euler = (fold * 0.8, 0, 0)
    key(tchain[0], fr, "rotation_euler"); key(tchain[1], fr, "rotation_euler")
    A.rotation_euler.z = 0.25 * math.sin(t * 0.6) + 0.9 * T.u(5, 0.1, 0.8, fr) * (1 - T.u(6, 0.2, 0.8, fr)); key(A, fr, "rotation_euler")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 60 * math.sin(t * 0.5)); oc.location = (2.3 * math.cos(a), 2.3 * math.sin(a), 1.25); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.35 * math.cos(t * 0.6); key(cc, fr, "location")
끝(T, cams)
