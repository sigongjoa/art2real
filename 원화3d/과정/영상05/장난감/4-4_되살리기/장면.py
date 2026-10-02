"""4-4 복원 가능 vs 불가(Biederman 1987 그림 21) — 같은 물뿌리개 선화 두 장, 같은 양을 지우되 자리만 다르다. 왼쪽은 주황 선이 빈틈을 이어 되살아나고, 오른쪽은 엉뚱한 선만 깜빡인다."""
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

물뿌리개 = [
    호(0, 0.25, 0.35, 0.08, 180, 360, 12), 호(0, 0.25, 0.35, 0.08, 0, 180, 12),   # 0-1 윗면
    [(-0.35, 0.25), (-0.35, -0.45)], [(0.35, 0.25), (0.35, -0.05)], [(0.35, -0.25), (0.35, -0.45)],   # 2-4 옆
    호(0, -0.45, 0.35, 0.08, 180, 360, 12),                                     # 5 바닥
    [(0.35, -0.05), (0.78, 0.38)], [(0.35, -0.25), (0.86, 0.3)], [(0.78, 0.38), (0.86, 0.3)],   # 6-8 주둥이
    호(-0.02, 0.27, 0.24, 0.32, 180, 0, 14),                                    # 9 손잡이
]
P = 0.5
def gone(mode, s): return abs(s - 0.5) < P / 2 if mode == "mid" else (s < P / 2 or s > 1 - P / 2)

T = 시작(); 무대(ARGS[1])
wood = mat("기둥", (0.75, 0.55, 0.35), 0.8)
for x in (-0.8, 0.8):
    흰판((x, 1.0, 1.35), 1.45, 1.9)
    for dx in (-0.75, 0.75): box((0.08, 0.08, 2.4), wood, loc=(x + dx, 1.02, 1.2), bevel=0.02)
ink = mat("먹", (0.03, 0.03, 0.035), 0.5); glow = mat("이음", (1.0, 0.33, 0.03), 0.5, emit=1.1)
gl = 그림(물뿌리개, (-1.05, 1.36), 1.0, m=ink); gr = 그림(물뿌리개, (0.55, 1.36), 1.0, m=ink)
fill = 그림(물뿌리개, (-1.05, 1.36), 1.0, y=0.965, r=0.026, m=glow)
L = T.lines
보임키([o for o, _, _ in gl.pieces], lambda fr, i: not (fr >= L[1][0] + 4 and gone("mid", gl.pieces[i][2])), T.end)
보임키([o for o, _, _ in gr.pieces], lambda fr, i: not (fr >= L[2][0] + 4 and gone("vtx", gr.pieces[i][2])), T.end)
보임키([o for o, _, _ in fill.pieces], lambda fr, i: gone("mid", fill.pieces[i][2]) and fr >= L[3][0] + (0.15 + 0.6 * fill.pieces[i][1] / 10) * (L[3][1] - L[3][0]), T.end)
# 오른쪽: 엉뚱한 이음 후보가 깜빡였다 사라진다
rnd = random.Random(4); tries = []
ends = [gr.w(e[0]) for e in 물뿌리개] + [gr.w(e[-1]) for e in 물뿌리개]
for k in range(6):
    a, b = rnd.sample(range(len(ends)), 2); a, b = ends[a].copy(), ends[b].copy(); a.y = b.y = 0.962
    tries.append(막대(a, b, 0.022, glow))
보임키(tries, lambda fr, i: L[4][0] + 6 + 9 * i <= fr < L[4][0] + 15 + 9 * i, T.end)
# 지우개 둘: 판 위를 문지르다 빠진다
e1, e2 = 지우개(), 지우개()
cat = 고양이("고양이", (-2.0, -0.2, 0))
cams = {"front": camera("front", (0, -3.6, 1.2), (0, 1, 1.45), 26),
        "left": camera("left", (-0.6, -2.4, 1.5), (-0.8, 1, 1.4), 30),
        "right": camera("right", (0.6, -2.4, 1.5), (0.8, 1, 1.4), 30),
        "close": camera("close", (0.9, -1.4, 1.5), (0.75, 1, 1.4), 30),
        "low": camera("low", (0.3, -1.6, 0.25), (-0.7, 0.8, 1.2), 22),
        "wide": camera("wide", (1.8, -3.4, 0.5), (0, 1, 1.4), 24)}
for fr in range(1, T.end + 1):
    for e, i, x0 in ((e1, 1, -0.8), (e2, 2, 0.8)):
        a = T.u(i, 0, 0.15, fr); b = T.u(i, 0.25, 0.45, fr)
        v = Vector((x0 + 0.35 * math.sin(fr * 0.9), 0.82, 1.4 + 0.4 * math.cos(fr * 0.37)))
        e.location = Vector((x0 + 2.4 * (1 if x0 > 0 else -1), 0.6, 3.2)).lerp(v, a - b) if b < 1 else Vector((0, 0, -5))
        e.rotation_euler.y = 0.2 * math.sin(fr * 1.7); 키(e, fr, "location", "rotation_euler")
    # 고양이: 왼쪽 판 앞에서 기뻐 뛰고, 오른쪽 판 앞에서 갸웃
    w = T.u(0, 0.3, 0.9, fr); m2 = T.u(4, 0, 0.4, fr)
    x = -2.0 + 1.2 * w + 1.5 * m2
    hop = 0.18 * abs(math.sin(fr / 3.5)) * (T.u(3, 0.5, 0.6, fr) - T.u(4, 0, 0.05, fr))
    cat[0].location = (x, -0.2, hop); cat[0].rotation_euler.z = 1.2 * T.u(0, 0.85, 1, fr) - 1.2 * (T.u(4, 0, 0.05, fr) - T.u(4, 0.4, 0.5, fr))
    tilt = 0.4 * math.sin(fr / 6) * (T.u(4, 0.45, 0.55, fr) - T.u(5, 0.5, 0.7, fr))
    cat[1].rotation_euler = (tilt, -0.7, 0)
    키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler"); 고양이_키(cat, fr, (0 < w < 1) or (0 < m2 < 1))
    c = cams["front"][0]; c.location.y = -3.6 + 0.4 * fr / T.end; 키(c, fr, "location")
    c = cams["close"][0]; c.location.x = 0.9 + 0.3 * math.sin(fr / 30); 키(c, fr, "location")
    c = cams["wide"][0]; c.location.x = 1.8 - 1.2 * fr / T.end; 키(c, fr, "location")
끝(T, cams)
