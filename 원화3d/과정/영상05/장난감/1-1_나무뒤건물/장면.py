"""1-1 나무 가지 뒤 건물(Kellman & Shipley 1991 그림1) — 앙상한 나무 뒤 탑. 가지가 자라 탑을 수십 조각으로 잘라도 하나로 보인다 · 카메라 옆걸음에도 하나."""
import bpy, math, random
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1], trees=False)
random.seed(3)
wall, roof, win, bark = mat("벽", (0.98, 0.78, 0.55), 0.8), mat("지붕", (0.85, 0.35, 0.3), 0.7), mat("창", (0.25, 0.35, 0.6), 0.3), mat("가지", (0.32, 0.2, 0.12), 0.9)
glowm = mat("채움", (1.0, 0.55, 0.15), 0.8)
tw = 1.5
tower = box((tw, tw, 3.4), wall, loc=(0, 2.6, 1.7), bevel=0.04)
cone(1.15, 1.0, roof, loc=(0, 2.6, 3.9))
for zx in [(x, z) for x in (-0.45, 0, 0.45) for z in (0.7, 1.5, 2.3, 3.0)]:
    box((0.24, 0.04, 0.36), win, loc=(zx[0], 2.6 - tw / 2 - 0.01, zx[1]))
# 채움 표시: 탑 앞면에 깜빡이는 주황 판(가지 뒤 부분 = 눈이 채운 곳)
fill = box((tw * 0.98, 0.01, 3.3), mat("채움판", (1.0, 0.55, 0.15), 0.8, emit=1.2, alpha=True), loc=(0, 2.6 - tw / 2 - 0.03, 1.7))
fa = alpha_of(fill.data.materials[0])

# 가지: 밑동 빈 객체를 키워 자라게 한다
def 가지(p, d, L, r, born):
    e = empty("가지밑", loc=p); e.rotation_mode = "QUATERNION"; e.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(d))
    cyl(r, L, bark, e, (0, 0, L / 2)); return (e, born)
tree = empty("나무", loc=(0, 0, 0))
br = [가지((-0.15, 0, 0), (0, 0, 1), 4.2, 0.09, 0.0)]
for k in range(26):
    z = random.uniform(0.9, 3.9); s = random.choice((-1, 1))
    d = Vector((s * random.uniform(0.5, 1.0), random.uniform(-0.2, 0.2), random.uniform(0.3, 1.1))).normalized()
    p = Vector((-0.15, 0, z)); L = random.uniform(0.8, 1.7)
    born = 0.0 if k < 7 else (k - 7) / 19
    br.append(가지(p, d, L, random.uniform(0.025, 0.05), born))
    if k % 2 == 0:                                   # 잔가지
        q = p + d * L * random.uniform(0.4, 0.8); d2 = (d + Vector((random.uniform(-0.8, 0.8), 0, random.uniform(0.2, 0.8)))).normalized()
        br.append(가지(q, d2, L * 0.6, 0.02, min(1, born + 0.08) if born else 0.0))
for e, _ in br: e.parent = tree

cat = 고양이("고양이", (-2.0, -1.0, 0)); cat[0].scale = (1.6, 1.6, 1.6)
cams = {"front": camera("front", (0, -5.2, 1.6), (0, 1.5, 2.1), 30),
        "close": camera("close", (0.4, -3.4, 2.2), (0, 2, 2.3), 34),
        "low": camera("low", (-1.6, -3.0, 0.35), (0, 1.5, 2.0), 22),
        "side": camera("side", (2.4, -3.6, 1.4), (0, 1.8, 2.2), 30),
        "track": camera("track", (-2.0, -5.0, 1.6), (0, 1.8, 2.1), 30),
        "track2": camera("track2", (1.0, -4.6, 2.6), (0, 1.8, 2.0), 30)}
base = {k: Vector(c[0].location) for k, c in cams.items()}

for fr in range(1, T.end + 1):
    g = T.u(2, 0, 1, fr) if fr >= T.lines[2][0] else 0          # 가지 자람 진행
    for e, born in br:
        s = 1.0 if born == 0 else min(1, max(0, (g - born * 0.9) / 0.12))
        e.scale = (max(s, 1e-3),) * 3; e.keyframe_insert("scale", frame=fr)
    tree.rotation_euler.y = 0.02 * math.sin(fr / 13); tree.keyframe_insert("rotation_euler", frame=fr)   # 바람
    # 고양이: 1 줄에서 걸어 들어와 탑을 올려다봄 · 마지막 줄에 다시 걷기
    u = T.u(1, 0, 0.7, fr); x = -2.0 + 1.6 * u; walk = 0 < u < 1
    w2 = T.u(6, 0.2, 1, fr) if fr >= T.lines[6][0] else 0; x += 1.4 * w2; walk = walk or 0 < w2 < 1
    cat[0].location = (x, -1.0, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.7 * T.u(1, 0.7, 0.95, fr), 0.3 * math.sin(fr / 11)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    # 카메라: 모두 천천히 미끄러짐 · track 은 옆걸음
    for k, (c, _) in cams.items():
        p = base[k].copy(); p.x += 0.25 * math.sin(fr / 40 + len(k))
        if k == "track": p.x = -2.0 + 4.0 * T.u(4, 0, 0.5, fr)
        if k == "track2": p.x = 1.0 - 2.5 * T.u(4, 0.5, 1, fr)
        c.location = p; c.keyframe_insert("location", frame=fr)
    a = 0.0
    if fr >= T.lines[5][0] and fr <= T.lines[5][1]: a = 0.55 * (0.5 + 0.5 * math.sin(fr / 3)) * T.u(5, 0, 0.2, fr)
    fa.default_value = a; fa.keyframe_insert("default_value", frame=fr)
    fill.hide_render = a == 0; fill.keyframe_insert("hide_render", frame=fr)
끝(T, cams)
