"""4-2 중간 삭제 vs 모서리 삭제(Biederman 1987 그림 16) — 위 · 아래 판에 같은 램프 선화. 지우개 둘이 같은 양을 지우되 위는 가운데, 아래는 모서리. 고양이가 올려다본다."""
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

def 지우기계획(g, mode, p, f0, f1, start=(3.0, 0.6, 3.0)):
    """mode 'mid' = 변 가운데 p 만큼 · 'vtx' = 변 양 끝 p/2 씩. 지우개가 구역을 차례로 돌며 지운다.
    반환: (조각별 숨는 프레임, 지우개 위치 함수 fr → Vector)"""
    if mode == "mid":
        zones = [g.mid(ei) for ei in range(len(g.edges))]
        own = [ei if abs(s - 0.5) < p / 2 else None for (_, ei, s) in g.pieces]
    else:
        zones = []
        def zid(pt):
            for i, z in enumerate(zones):
                if abs(z[0] - pt[0]) + abs(z[1] - pt[1]) < 1e-3: return i
            zones.append(pt); return len(zones) - 1
        ends = [(zid(e[0]), zid(e[-1])) for e in g.edges]
        own = [ends[ei][0] if s < p / 2 else ends[ei][1] if s > 1 - p / 2 else None for (_, ei, s) in g.pieces]
    nz = len(zones); slot = (f1 - f0) / nz
    hide = [f0 + slot * (z + 0.75) if z is not None else 10 ** 9 for z in own]
    W = [g.w(z, -0.16) for z in zones]; S = Vector(start)
    def pos(fr):
        if fr < f0: return S
        k = (fr - f0) / slot
        if k >= nz:
            return W[-1].lerp(S, ease((fr - f1) / 20))
        zi = int(k); t = k - zi; a = W[zi - 1] if zi else S
        if t < 0.4:
            u = ease(t / 0.4); v = a.lerp(W[zi], u); v.z += 0.25 * math.sin(math.pi * u); return v
        return W[zi] + Vector((0.07 * math.sin(fr * 1.7), 0, 0.03 * math.cos(fr * 1.7)))
    return hide, pos

램프 = [
    호(0, 0.5, 0.3, 0.06, 180, 360, 10), 호(0, 0.5, 0.3, 0.06, 0, 180, 10),      # 0-1 갓 윗테
    [(-0.3, 0.5), (-0.55, 0.05)], [(0.3, 0.5), (0.55, 0.05)],                   # 2-3 갓 옆
    호(0, 0.05, 0.55, 0.11, 180, 360, 16),                                      # 4 갓 아랫테
    [(-0.04, -0.06), (-0.04, -0.45)], [(0.04, -0.06), (0.04, -0.45)],          # 5-6 기둥
    호(0, -0.5, 0.35, 0.07, 180, 360, 12), 호(0, -0.5, 0.35, 0.07, 0, 180, 12),   # 7-8 받침 윗면
    [(-0.35, -0.5), (-0.35, -0.6)], [(0.35, -0.5), (0.35, -0.6)],             # 9-10 받침 옆
    호(0, -0.6, 0.35, 0.07, 180, 360, 12),                                      # 11 받침 아래
]

T = 시작(); 무대(ARGS[1])
wood = mat("기둥", (0.75, 0.55, 0.35), 0.8)
for z in (2.75, 1.05): 흰판((0, 1.0, z), 2.2, 1.62)
for x in (-1.16, 1.16): box((0.1, 0.1, 3.6), wood, loc=(x, 1.02, 1.8), bevel=0.02)
ink = mat("먹", (0.03, 0.03, 0.035), 0.5)
gt = 그림(램프, (0, 2.78), 1.05, m=ink); gb = 그림(램프, (0, 1.06), 1.05, m=ink)
L = T.lines
ht, pt = 지우기계획(gt, "mid", 0.45, L[1][0] + 5, L[1][1] + 10, (2.5, 0.5, 3.6))
hb, pb = 지우기계획(gb, "vtx", 0.45, L[2][0] + 5, L[2][1] + 10, (2.5, 0.5, 0.3))
보임키([o for o, _, _ in gt.pieces], lambda fr, i: fr < ht[i], T.end)
보임키([o for o, _, _ in gb.pieces], lambda fr, i: fr < hb[i], T.end)
e1, e2 = 지우개(), 지우개()
cat = 고양이("고양이", (-2.0, 0.1, 0))
cams = {"front": camera("front", (0, -4.6, 1.9), (0, 1, 1.9), 36),
        "top": camera("top", (0.25, -2.4, 2.85), (0, 1, 2.78), 34),
        "bottom": camera("bottom", (-0.25, -2.4, 1.2), (0, 1, 1.06), 34),
        "close": camera("close", (0.1, -1.6, 1.15), (0, 1, 1.08), 26),
        "low": camera("low", (1.2, -1.5, 0.3), (-0.3, 0.6, 1.6), 22),
        "wide": camera("wide", (2.4, -4.6, 0.6), (0, 1, 1.9), 26)}
for fr in range(1, T.end + 1):
    e1.location = pt(fr); e2.location = pb(fr)
    for e in (e1, e2): e.rotation_euler.y = 0.15 * math.sin(fr * 1.7); 키(e, fr, "location", "rotation_euler")
    w = T.u(3, 0.0, 0.6, fr); turn = T.u(3, 0.5, 0.8, fr)
    cat[0].location = (-2.0 + 1.6 * w, 0.1, 0); cat[0].rotation_euler.z = 1.2 * turn
    up = 0.9 * turn * (1 - 0.6 * T.u(4, 0, 0.3, fr)) + 0.5 * T.u(5, 0, 0.3, fr)
    tilt = 0.35 * math.sin((fr - L[4][0]) / 6) * (T.u(4, 0.1, 0.25, fr) - T.u(5, 0, 0.2, fr))
    cat[1].rotation_euler = (tilt, -up, 0); 키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler")
    고양이_키(cat, fr, 0 < w < 1)
    c = cams["front"][0]; c.location.y = -4.6 + 0.5 * fr / T.end; 키(c, fr, "location")
    c = cams["close"][0]; c.location.x = 0.1 + 0.3 * math.sin(fr / 30); 키(c, fr, "location")
    c = cams["wide"][0]; c.location.x = 2.4 - 1.2 * fr / T.end; 키(c, fr, "location")
끝(T, cams)
