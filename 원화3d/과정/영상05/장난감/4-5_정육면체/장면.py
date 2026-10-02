"""4-5 정육면체 선 지우기(Hummel & Biederman 1992) — 선 막대로 지은 정육면체 둘이 돈다. 왼쪽은 모서리 가운데를, 오른쪽은 꼭짓점 주변을 같은 양 지운다. 오른쪽은 떠 있는 막대 열두 개."""
import bpy, math, random
from mathutils import Vector
from 장난감_공용 import *

# ── 선화 도구(이 장면 전용 사본): 흰 판 위 검은 선을 짧은 막대 조각으로 — 조각마다 숨겨 「지우기」 ──
_UNIT = []
def 막대(p, q, r, m):                     # 메시 공유 가벼운 막대(수백 개용)
    if not _UNIT:
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, vertices=12); u = bpy.context.object
        for f in u.data.polygons: f.use_smooth = True
        u.data.materials.append(m); _UNIT.append(u.data); bpy.data.objects.remove(u)
    p, q = Vector(p), Vector(q); d = q - p
    o = bpy.data.objects.new("선", _UNIT[0]); bpy.context.scene.collection.objects.link(o)
    o.location = (p + q) / 2; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    o.scale = (r, r, d.length + 1.4 * r)
    o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m
    return o

def 호(cx, cz, rx, rz, a0, a1, n=14):     # 타원 호 점들(도 단위)
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cz + rz * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]

class 그림:
    """edges = [[(x,z),...], ...] 변(꼭짓점→꼭짓점). 판 평면 y 에 center · scale · rot(도)로 놓는다.
    pieces = [(obj, 변 번호, 변 안 위치 s 0..1)]"""
    def __init__(s, edges, center, scale, rot=0.0, y=0.975, r=0.022, m=None, step=0.06):
        s.c, s.k, s.a, s.y = center, scale, math.radians(rot), y
        s.edges, s.pieces = edges, []
        for ei, poly in enumerate(edges):
            W = [s.w(p) for p in poly]; cum = [0.0]
            for i in range(1, len(W)): cum.append(cum[-1] + (W[i] - W[i - 1]).length)
            n = max(2, round(cum[-1] / step))
            def at(t):
                L = t * cum[-1]
                for i in range(1, len(W)):
                    if cum[i] >= L - 1e-9:
                        f = (L - cum[i - 1]) / max(1e-9, cum[i] - cum[i - 1]); return W[i - 1].lerp(W[i], f)
                return W[-1]
            for j in range(n):
                s.pieces.append((막대(at(j / n), at((j + 1) / n), r, m), ei, (j + 0.5) / n))
    def w(s, p, dy=0.0):                    # 그림 좌표 → 세계
        x, z = p; ca, sa = math.cos(s.a), math.sin(s.a)
        return Vector((s.c[0] + s.k * (x * ca - z * sa), s.y + dy, s.c[1] + s.k * (x * sa + z * ca)))
    def mid(s, ei):                         # 변 가운데 점(그림 좌표)
        e = s.edges[ei]; return e[len(e) // 2] if len(e) > 2 else ((e[0][0] + e[1][0]) / 2, (e[0][1] + e[1][1]) / 2)

def 보임키(objs, fn, end):                 # fn(fr, i) → 보임? 바뀌는 프레임에만 키
    for i, o in enumerate(objs):
        prev = None
        for fr in range(1, end + 1):
            v = bool(fn(fr, i))
            if v != prev:
                o.hide_render = not v; o.keyframe_insert("hide_render", frame=fr); prev = v

def 흰판(loc, w, h):
    m = mat("판", (1, 1, 1), 1.0, emit=1.45)
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); o = put(bpy.context.object, m, loc=loc); o.scale = (w, h, 1)
    return o

def 얼룩(loc, r, m, seed=0):              # 판 앞 납작한 덩어리(공 셋)
    rnd = random.Random(seed); e = empty("얼룩", loc=loc)
    ball(r, m, e, (0, 0, 0), (1, 0.3, 0.9))
    for k in range(3):
        a = rnd.uniform(0, 6.28); ball(r * rnd.uniform(0.5, 0.7), m, e, (r * 0.6 * math.cos(a), 0, r * 0.6 * math.sin(a)), (1, 0.3, 1))
    return e

def 지우개(loc=(0, 0, 0)):
    e = empty("지우개", loc=loc)
    box((0.3, 0.14, 0.13), mat("고무", (0.98, 0.62, 0.68), 0.8), e, (0, 0, -0.04), bevel=0.03)
    box((0.31, 0.15, 0.1), mat("띠", (0.25, 0.45, 0.85), 0.6), e, (0, 0, 0.07), bevel=0.02)
    return e

def 키(o, fr, *props):
    for p in props: o.keyframe_insert(p, frame=fr)

# 손전등 선화(그림 좌표 · 가로 약 1.9) — 4-1 · 4-7 공용
손전등 = [
    [(-0.9, 0.22), (0.4, 0.22)],                       # 0 몸 위
    [(-0.9, -0.22), (0.4, -0.22)],                     # 1 몸 아래
    호(-0.9, 0, 0.08, 0.22, 90, 270),                  # 2 꼬리 끝 반 타원
    호(0.4, 0, 0.07, 0.22, 90, -90),                   # 3 몸-머리 이음
    [(0.4, 0.22), (0.85, 0.38)],                       # 4 머리 위
    [(0.4, -0.22), (0.85, -0.38)],                     # 5 머리 아래
    호(0.85, 0, 0.11, 0.38, 90, 270),                  # 6 렌즈 왼쪽
    호(0.85, 0, 0.11, 0.38, 90, -90),                  # 7 렌즈 오른쪽
    [(-0.35, 0.22), (-0.35, 0.33)], [(-0.35, 0.33), (-0.08, 0.33)], [(-0.08, 0.33), (-0.08, 0.22)],   # 8-10 스위치
]
손전등_이음 = [(-0.9, 0.22), (-0.9, -0.22), (0.4, 0.22), (0.4, -0.22), (0.85, 0.38), (0.85, -0.38), (-0.215, 0.3)]
손전등_중간 = [(-0.25, -0.22), (0.25, 0.22), (-0.98, 0.0), (0.625, 0.3), (0.625, -0.3), (0.96, 0.0), (0.47, 0.0)]

def 선상자(center, a, m, step=0.05, r=0.022):
    e = empty("상자", loc=center); h = a / 2; pieces = []
    V = [Vector((x, y, z)) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
    E = [(i, j) for i in range(8) for j in range(i + 1, 8) if (V[i] - V[j]).length < a * 1.01]
    for ei, (i, j) in enumerate(E):
        n = round(a / step)
        for k in range(n):
            o = 막대(V[i].lerp(V[j], k / n), V[i].lerp(V[j], (k + 1) / n), r, m); o.parent = e
            pieces.append((o, ei, (k + 0.5) / n))
    return e, pieces

T = 시작(); 무대(ARGS[1])
ink = mat("먹", (0.12, 0.14, 0.3), 0.5)
P = 0.5
cl, pl = 선상자((-0.85, 0.8, 1.35), 0.9, ink); cr, pr = 선상자((0.85, 0.8, 1.35), 0.9, ink)
L = T.lines
보임키([o for o, _, _ in pl], lambda fr, i: not (abs(pl[i][2] - 0.5) < P / 2 * T.u(1, 0.1, 0.7, fr)), T.end)
보임키([o for o, _, _ in pr], lambda fr, i: not (min(pr[i][2], 1 - pr[i][2]) < P / 2 * T.u(2, 0.1, 0.7, fr)), T.end)
흰판((0, 1.9, 1.7), 4.2, 3.4)
pedm = mat("받침", (0.95, 0.85, 0.6), 0.7)
for x in (-0.85, 0.85): cyl(0.35, 0.7, pedm, loc=(x, 0.8, 0.35), bevel=0.04)
cat = 고양이("고양이", (-2.2, -0.3, 0))
cams = {"front": camera("front", (0, -3.0, 2.1), (0, 0.8, 1.3), 24),
        "left": camera("left", (-0.6, -1.9, 1.9), (-0.85, 0.8, 1.3), 30),
        "right": camera("right", (0.6, -1.9, 1.9), (0.85, 0.8, 1.3), 30),
        "close": camera("close", (1.3, -1.1, 1.9), (0.85, 0.8, 1.35), 30),
        "orbit": camera("orbit", (-0.85, -2.0, 1.9), (-0.85, 0.8, 1.3), 30),
        "low": camera("low", (1.4, -1.3, 0.25), (0.5, 0.8, 1.1), 22),
        "wide": camera("wide", (2.3, -3.6, 0.6), (0, 0.8, 1.2), 24)}
for fr in range(1, T.end + 1):
    for k, c in enumerate((cl, cr)):
        c.rotation_euler.z = math.radians(25 + 0.9 * fr + 10 * k); c.location.z = 1.35 + 0.04 * math.sin(fr / 14 + k)
        키(c, fr, "rotation_euler", "location")
    # 오른쪽 막대들이 조금씩 흩어진다(4 번째 줄)
    sp = T.u(4, 0.1, 0.8, fr) * (1 - T.u(6, 0, 0.4, fr))
    for o, ei, s in pr:
        o.delta_location = Vector(((ei % 3 - 1) * 0.08, (ei % 2 - 0.5) * 0.12, (ei % 4 - 1.5) * 0.06)) * sp; o.keyframe_insert("delta_location", frame=fr)
    a = math.radians(-90 + 140 * T.u(3, 0, 1, fr)); oc = cams["orbit"][0]
    oc.location = (-0.85 + 2.6 * math.cos(a), 0.8 + 2.6 * math.sin(a), 1.9); 키(oc, fr, "location")
    w = T.u(0, 0.2, 0.9, fr); w2 = T.u(4, 0, 0.5, fr)
    cat[0].location = (-2.2 + 2.2 * w + 0.9 * w2, -0.3, 0); cat[0].rotation_euler.z = 0.5 * T.u(1, 0, 0.3, fr) - 0.5 * T.u(4, 0, 0.1, fr) + 0.9 * T.u(4, 0.5, 0.7, fr)
    tilt = 0.4 * math.sin(fr / 6) * (T.u(4, 0.6, 0.7, fr) - T.u(5, 0.5, 0.7, fr))
    cat[1].rotation_euler = (tilt, -0.8, 0)
    키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler"); 고양이_키(cat, fr, (0 < w < 1) or (0 < w2 < 1))
    c = cams["front"][0]; c.location.y = -3.0 + 0.3 * fr / T.end; 키(c, fr, "location")
    c = cams["wide"][0]; c.location.x = 2.3 - 1.4 * fr / T.end; 키(c, fr, "location")
끝(T, cams)
