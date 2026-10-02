"""5-1 막대 뒤 벌레(Tse 1999) — 흰 판 앞, 굵은 막대 뒤로 검은 S 관. 보이는 건 양쪽 토막 둘 · 눈이 상상한 가운데(주황 점선)가 깜빡이고 · 막대가 들리면 진짜 관 하나."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def spline(pts, n=120):                      # Catmull-Rom 표본
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        for k in range(n // (len(P) - 3)):
            t = k / (n // (len(P) - 3)); p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out + [P[-2]]
def tube(pts, r, m):
    cu = bpy.data.curves.new("관", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new("관", cu); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
board = mat("판", (1, 1, 1), 1.0, emit=1.45)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, board, loc=(0, 1.0, 1.8)).scale = (4.2, 3.8, 1)
black = mat("벌레", (0.02, 0.02, 0.025), 0.45)
Y = 0.45
S = [(-1.35, Y, 0.55), (-1.0, Y, 1.25), (-0.45, Y, 1.45), (0.0, Y, 1.75), (0.45, Y, 2.05), (1.0, Y, 2.25), (1.35, Y, 2.95)]
pts = spline(S); worm = tube(pts, 0.17, black)
pillar = box((0.95, 0.35, 3.6), mat("막대", (0.55, 0.7, 0.95), 0.7), loc=(0, 0, 1.8), bevel=0.04)
# 눈이 지어낸 가운데 — 막대 앞 주황 점선(가려진 구간만)
glow = mat("상상", (1.0, 0.45, 0.08), 0.5, emit=2.2, alpha=True); ga = alpha_of(glow)
hid = [p for p in pts if abs(p.x) < 0.5]
dash = [bar(hid[i] + Vector((0, -Y - 0.25, 0)), hid[min(i + 3, len(hid) - 1)] + Vector((0, -Y - 0.25, 0)), 0.05, glow) for i in range(0, len(hid) - 3, 6)]
cat = 고양이("고양이", (-1.0, -1.0, 0)); cat[0].rotation_euler.z = math.radians(60)

cams = {"front": camera("front", (0, -5.6, 1.6), (0, 0, 1.6), 25),
        "close": camera("close", (0.0, -3.9, 1.6), (0, 0, 1.6), 26),
        "low": camera("low", (1.7, -2.8, 0.35), (-0.1, 0, 1.4), 22),
        "catcam": camera("catcam", (-1.9, -2.3, 0.45), (0, 0, 1.6), 24),
        "orbit": camera("orbit", (0, -5.6, 1.9), (0, 0.2, 1.7), 30)}

for fr in range(1, T.end + 1):
    # 고양이: 0줄 걸어 들어옴 · 1줄 좌우 토막 번갈아 봄 · 3줄 막대가 들리면 깜짝 뒷걸음
    walk = T.u(0, 0.1, 0.8, fr); x = -1.7 + 0.9 * walk
    back = T.u(3, 0.2, 0.4, fr) if fr >= T.lines[3][0] else 0
    hop = 0.25 * math.sin(math.pi * T.u(3, 0.2, 0.35, fr)) if fr >= T.lines[3][0] else 0
    cat[0].location = (x - 0.3 * back, -1.0 - 0.3 * back, hop); cat[0].keyframe_insert("location", frame=fr)
    look = math.sin((fr - T.lines[1][0]) / 10) if fr >= T.lines[1][0] else 0
    up = 0.5 + 0.3 * back
    cat[1].rotation_euler = (0, -up, 0.6 * look * (1 - back)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < walk < 1)
    # 상상 점선: 2줄에서 깜빡이며 나타남 · 3줄에 막대 들리면 사라짐 · 4줄에 다시 진하게(막대 내려온 뒤)
    a = 0.0
    if T.lines[2][0] <= fr < T.lines[3][0]: a = 0.9 * T.u(2, 0.1, 0.4, fr) * (0.65 + 0.35 * math.sin(fr * 0.9))
    if fr >= T.lines[4][0]: a = 0.9 * T.u(4, 0.3, 0.6, fr) * (0.7 + 0.3 * math.sin(fr * 0.9))
    ga.default_value = a; ga.keyframe_insert("default_value", frame=fr)
    for d in dash: d.hide_render = a < 0.02; d.keyframe_insert("hide_render", frame=fr)
    # 막대: 3줄 올라갔다 4줄 처음에 내려옴
    lift = T.u(3, 0.1, 0.5, fr) if fr >= T.lines[3][0] else 0
    if fr >= T.lines[4][0]: lift = 1 - T.u(4, 0, 0.25, fr)
    pillar.location.z = 1.8 + 3.4 * lift; pillar.rotation_euler.y = 0.12 * math.sin(math.pi * lift)
    pillar.keyframe_insert("location", frame=fr); pillar.keyframe_insert("rotation_euler", frame=fr)
    # 벌레가 살짝 꿈틀(좌우로 조금)
    worm.location.x = 0.06 * math.sin(fr / 14); worm.keyframe_insert("location", frame=fr)
    oc, ot = cams["orbit"]; u = T.u(3, 0, 0.8, fr) if fr >= T.lines[3][0] else 0
    ang = math.radians(-90 + 35 * u); dist = 5.6
    oc.location = (dist * math.cos(ang), dist * math.sin(ang), 1.9); oc.keyframe_insert("location", frame=fr)
    # 0줄 front 는 천천히 밀고 들어감
    fc, _ = cams["front"]; fc.location.y = -5.6 + 0.6 * T.u(0, 0, 1, fr) if fr < T.lines[1][0] else -5.0; fc.keyframe_insert("location", frame=fr)
끝(T, cams)
