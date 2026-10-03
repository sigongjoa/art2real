"""9-1 가슴 · 골반 상자 — Bridgman 1920 p19. 지온 인형 하나가 곧게 섰다가 가슴 · 골반 상자에 색이 켜지고 · 한 다리에 무게를 실어 골반과 가슴이 반대로 기울고 · 위에서 보면 엇갈려 비틀린다 · 끝에 자세가 다른 인형 넷."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def color(m, c, fr):
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Base Color"].default_value = (*c, 1)
    p.inputs["Base Color"].keyframe_insert("default_value", frame=fr)
lerp = lambda a, b, k: tuple(x + (y - x) * k for x, y in zip(a, b))

WOOD, CH, PE = (0.93, 0.85, 0.7), (1.0, 0.55, 0.45), (0.45, 0.62, 0.95)
wood = mat("나무", WOOD, 0.6); joint = mat("마디", (0.8, 0.7, 0.55), 0.6)
def 인형(name, x, chest_m, pelvis_m):
    """골반 empty P(높이 1.0) → 가슴 C → 목 N · 엉덩이 hip[2] → 무릎 knee[2] · 어깨 sh[2] → 팔꿈치."""
    R = empty(name, loc=(x, 0, 0)); P = empty(name + "골반", R, (0, 0, 1.0))
    box((0.4, 0.26, 0.26), pelvis_m, P, (0, 0, 0), bevel=0.04)
    C = empty(name + "가슴", P, (0, 0, 0.13)); ball(0.09, joint, C, (0, 0, 0.0))
    box((0.48, 0.3, 0.46), chest_m, C, (0, 0, 0.27), bevel=0.05)
    N = empty(name + "목", C, (0, 0, 0.5)); cyl(0.05, 0.12, joint, N, (0, 0, 0.04))
    box((0.2, 0.24, 0.26), wood, N, (0, 0, 0.21), bevel=0.05)
    hips, knees, shs = [], [], []
    for s in (-1, 1):
        h = empty(name + "엉", P, (s * 0.11, 0, -0.1)); ball(0.065, joint, h)
        cyl(0.06, 0.4, wood, h, (0, 0, -0.22)); k = empty(name + "무릎", h, (0, 0, -0.43)); ball(0.055, joint, k)
        cyl(0.05, 0.38, wood, k, (0, 0, -0.2)); box((0.1, 0.2, 0.06), wood, k, (0, -0.05, -0.41), bevel=0.02)
        a = empty(name + "어깨", C, (s * 0.3, 0, 0.42)); ball(0.06, joint, a); cyl(0.045, 0.28, wood, a, (0, 0, -0.16))
        e = empty(name + "팔꿈치", a, (0, 0, -0.31)); ball(0.045, joint, e); cyl(0.04, 0.26, wood, e, (0, 0, -0.15)); ball(0.05, wood, e, (0, 0, -0.31))
        hips.append(h); knees.append(k); shs.append(a)
    return dict(R=R, P=P, C=C, N=N, hips=hips, knees=knees, shs=shs)

def pose(m, fr, tilt=0.0, twist=0.0, lean=0.0, arm=0.0):
    """tilt>0: 왼(−x) 다리에 무게 · 골반은 왼쪽이 올라가고 가슴은 반대로 · twist: 골반 · 가슴 엇갈림."""
    m["P"].rotation_euler = (lean * 0.3, tilt, twist * 0.5)
    m["P"].location.x = -0.04 * tilt / 0.2 if tilt else 0.0
    m["C"].rotation_euler = (lean, -2.0 * tilt, -twist); m["N"].rotation_euler = (-lean * 0.6, tilt * 1.2, twist * 0.5)
    for i, (h, k) in enumerate(zip(m["hips"], m["knees"])):
        free = (i == 1) == (tilt >= 0)                 # 무게 안 실린 다리는 무릎을 굽힌다
        bend = abs(tilt) / 0.2 * (1 if free else 0)
        h.rotation_euler = (-0.3 * bend - lean * 0.3, -tilt, -twist * 0.5); k.rotation_euler = (0.55 * bend, 0, 0)
    for i, a in enumerate(m["shs"]):
        s = -1 if i == 0 else 1
        a.rotation_euler = (0.15 * arm * s, tilt * 1.0 + s * 0.08, 0)
    for o in [m["P"], m["C"], m["N"]] + m["hips"] + m["knees"] + m["shs"]: key(o, fr, "rotation_euler", "location")

cm, pm = mat("가슴", WOOD, 0.6), mat("골반", WOOD, 0.6)
hero = 인형("주인공", 0, cm, pm)
others = [인형("인형%d" % i, x, mat("가슴%d" % i, CH, 0.6), mat("골반%d" % i, PE, 0.6)) for i, x in enumerate((-1.12, 0.37, 1.12))]
poses = [dict(tilt=-0.2, twist=0.0), dict(tilt=0.1, twist=0.5, arm=0.5), dict(tilt=0.0, lean=0.35, twist=-0.2)]
# 기울기 막대: 어깨선 · 골반선(3 줄에 켜진다)
glow = mat("선", (1.0, 0.5, 0.1), 0.5, emit=1.0)
bars = [box((0.8, 0.025, 0.025), glow, hero["C"], (0, -0.17, 0.42)), box((0.7, 0.025, 0.025), glow, hero["P"], (0, -0.15, 0.0))]

cams = {"front": camera("front", (0, -3.2, 1.05), (0, 0, 1.0), 30),
        "close": camera("close", (0.3, -1.9, 1.35), (0, 0, 1.2), 32),
        "side": camera("side", (2.6, -1.6, 1.1), (0, 0, 1.0), 30),
        "low": camera("low", (0.6, -2.1, 0.4), (0, 0, 1.0), 26),
        "top": camera("top", (0.15, -0.7, 3.1), (0, 0, 1.2), 30),
        "orbit": camera("orbit", (0, -2.6, 1.2), (0, 0, 1.1), 30),
        "wide": camera("wide", (0, -4.0, 1.1), (0, 0, 0.95), 24)}

for fr in range(1, T.end + 1):
    t = fr / 24
    c = T.u(1, 0.2, 0.5, fr); color(cm, lerp(WOOD, CH, c), fr); c2 = T.u(1, 0.45, 0.75, fr); color(pm, lerp(WOOD, PE, c2), fr)
    tilt = 0.2 * T.u(2, 0.1, 0.8, fr) * (1 - T.u(5, 0, 0.3, fr) * 0.5)
    twist = 0.45 * T.u(4, 0.1, 0.7, fr) * (1 - T.u(5, 0, 0.3, fr))
    pose(hero, fr, tilt=tilt, twist=twist + 0.03 * math.sin(t * 2), arm=0.2 * math.sin(t))
    hero["R"].location.x = -0.37 * T.u(5, 0, 0.4, fr); key(hero["R"], fr, "location")
    for b in bars:
        b.scale.x = (0.8 if b is bars[0] else 0.7) * max(0.001, T.u(3, 0.05, 0.4, fr)) * (1 - T.u(5, 0, 0.3, fr)) + 0.0001; key(b, fr, "scale")
    for i, (m, p) in enumerate(zip(others, poses)):
        k = T.u(5, 0.1 + 0.15 * i, 0.45 + 0.15 * i, fr)
        m["R"].scale = (max(0.001, k * (1 + 0.15 * math.sin(math.pi * k))),) * 3; key(m["R"], fr, "scale")
        pose(m, fr, tilt=p.get("tilt", 0), twist=p.get("twist", 0) + 0.04 * math.sin(t * 2 + i), lean=p.get("lean", 0), arm=p.get("arm", 0))
    oc, _ = cams["orbit"]; a = math.radians(-90 + 60 * math.sin(t * 0.5)); oc.location = (2.6 * math.cos(a), 2.6 * math.sin(a), 1.3); key(oc, fr, "location")
    tc, _ = cams["top"]; tc.location.x = 0.4 * math.sin(t * 0.6); key(tc, fr, "location")
    wc, _ = cams["wide"]; wc.location.y = -4.0 + 0.25 * math.sin(t * 0.5); key(wc, fr, "location")
끝(T, cams)
