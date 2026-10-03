"""4-7 손전등(Biederman 1987 그림 26) — 4-1 의 얼룩이 이음매에서 선 가운데로 미끄러지면 손전등이 읽힌다. 진짜 손전등이 판에서 튀어나와 불을 켠다."""
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
손전등_중간 = [(-0.6, 0.22), (-0.98, 0.0), (0.625, 0.3), (-0.1, -0.22), (0.96, 0.0), (0.625, -0.3), (0.12, 0.22)]

T = 시작(); 무대(ARGS[1])
흰판((0, 1.0, 1.8), 3.0, 3.6)
ink = mat("먹", (0.03, 0.03, 0.035), 0.5)
A = 28
g = 그림(손전등, (0.05, 1.8), 1.4, rot=A, m=ink)
blue = mat("얼룩", (0.28, 0.33, 0.58), 0.55)
blobs = [얼룩(g.w(p, -0.06), 0.25, blue, k) for k, p in enumerate(손전등_이음)]
src = [g.w(p, -0.06) for p in 손전등_이음]; dst = [g.w(p, -0.06) for p in 손전등_중간]
# 진짜 손전등(지온): 몸 원기둥 + 머리 원뿔대 + 렌즈 + 스위치
lamp = empty("손전등", loc=g.w((0, 0), -0.5)); lamp.rotation_euler.y = -math.radians(A)
k = 1.4; bodym, headm = mat("몸", (0.95, 0.55, 0.3), 0.5), mat("머리", (0.35, 0.6, 0.9), 0.5)
cyl(0.22 * k, 1.3 * k, bodym, lamp, (-0.25 * k, 0, 0), (0, math.pi / 2, 0), bevel=0.02)
bpy.ops.mesh.primitive_cone_add(radius1=0.22 * k, radius2=0.38 * k, depth=0.45 * k, vertices=48, rotation=(0, math.pi / 2, 0)); put(bpy.context.object, headm, lamp, (0.625 * k, 0, 0))
lens = mat("렌즈", (1.0, 0.95, 0.6), 0.3, emit=0.0); lp = next(n for n in lens.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
cyl(0.36 * k, 0.03, lens, lamp, (0.86 * k, 0, 0), (0, math.pi / 2, 0))
box((0.27 * k, 0.12, 0.1 * k), headm, lamp, (-0.215 * k, 0, 0.25 * k), bevel=0.02)
beam = mat("빛", (1.0, 0.92, 0.5), 0.5, emit=1.2, alpha=True); ba = alpha_of(beam)
bpy.ops.mesh.primitive_cone_add(radius1=1.2, radius2=0.36 * k, depth=2.4, vertices=48, rotation=(0, -math.pi / 2, 0)); put(bpy.context.object, beam, lamp, (0.86 * k + 1.2, 0, 0))
cat = 고양이("고양이", (-0.4, -0.3, 0)); cat[0].rotation_euler.z = 1.3
J = g.w((0.4, 0.22))
cams = {"front": camera("front", (0, -4.2, 1.7), (0, 1, 1.7), 33),
        "close": camera("close", (0.3, -2.7, 1.9), (0.15, 1, 1.85), 33),
        "wide": camera("wide", (2.0, -4.4, 0.45), (0, 1, 1.4), 24),
        "catcam": camera("catcam", (-0.9, -1.6, 0.45), (0.1, 0.6, 1.5), 24),
        "low": camera("low", (1.1, -1.7, 0.25), (-0.1, 0.5, 1.0), 22),
        "blob": camera("blob", J + Vector((0.6, -1.9, -0.25)), J + Vector((0, 0, -0.05)), 36),
        "pop": camera("pop", (1.6, -3.2, 1.0), (0.1, 0.4, 1.6), 26)}
L = T.lines
for fr in range(1, T.end + 1):
    for i, b in enumerate(blobs):
        u = T.u(1, 0.1 + 0.06 * i, 0.5 + 0.06 * i, fr) if i < 4 else T.u(2, 0.0 + 0.08 * (i - 4), 0.5 + 0.08 * (i - 4), fr)
        b.location = src[i].lerp(dst[i], u) + Vector((0, -0.12 * math.sin(math.pi * u), 0))
        sq = 0.15 * math.sin(math.pi * u); b.scale = (1 + sq, 1, 1 - sq); b.rotation_euler.y = 0.3 * math.sin(fr / 12 + i)
        키(b, fr, "location", "scale", "rotation_euler")
    pop = T.u(5, 0.1, 0.5, fr); ov = pop + 0.25 * math.sin(math.pi * pop)
    lamp.scale = (max(ov, 0.001),) * 3; lamp.location = g.w((0, 0), -0.05 - 0.6 * pop)
    lamp.rotation_euler.y = -math.radians(A) - 0.25 * T.u(6, 0, 0.6, fr); lamp.rotation_euler.z = -0.35 * T.u(5, 0.5, 1.0, fr)
    키(lamp, fr, "scale", "location", "rotation_euler")
    on = T.u(5, 0.55, 0.7, fr) * (0.85 + 0.15 * math.sin(fr / 2))
    ba.default_value = 0.3 * on; ba.keyframe_insert("default_value", frame=fr)
    lp.inputs["Emission Strength"].default_value = 2.5 * on; lp.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    # 고양이: 갸웃 → 알아보고 깡충
    hop = 0.2 * abs(math.sin(fr / 3.5)) * (T.u(3, 0.1, 0.2, fr) - T.u(4, 0, 0.1, fr) + T.u(5, 0.6, 0.7, fr))
    cat[0].location = (-0.4, -0.3, hop); cat[1].rotation_euler = (0.35 * math.sin(fr / 6) * (1 - T.u(2, 0.6, 0.8, fr)), -0.6, 0)
    키(cat[0], fr, "location"); 키(cat[1], fr, "rotation_euler"); 고양이_키(cat, fr, False)
    c = cams["front"][0]; c.location.y = -4.2 + 0.6 * fr / T.end; 키(c, fr, "location")
    c = cams["close"][0]; c.location.x = 0.3 - 0.4 * math.sin(fr / 40); 키(c, fr, "location")
    c = cams["pop"][0]; c.location.x = 1.6 - 1.0 * T.u(5, 0, 1, fr) - 0.6 * T.u(6, 0, 1, fr); 키(c, fr, "location")
끝(T, cams)
