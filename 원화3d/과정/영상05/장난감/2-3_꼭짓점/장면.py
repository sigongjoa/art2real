"""2-3 꼭짓점 — 벽돌 · 원기둥의 겉이 투명해지고 모서리만 빛난다 · 벽돌 꼭짓점 공 · 원기둥 휜 테두리 · 돌려도 곧음/휨이 그대로(Biederman 1987 그림 5)."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def parent_keep(o, p): o.parent = p; o.matrix_parent_inverse = p.matrix_world.inverted()
bm_, cm_ = mat("벽돌", (0.95, 0.5, 0.42), 0.6, alpha=True), mat("원통", (0.4, 0.62, 0.95), 0.5, alpha=True)
ba, ca = alpha_of(bm_), alpha_of(cm_)
for m in (bm_, cm_): m.show_transparent_back = False
line_s, line_c = mat("곧은선", (1.0, 0.85, 0.2), 0.5, emit=2.2), mat("휜선", (0.3, 0.95, 1.0), 0.5, emit=2.2)
dot = mat("꼭짓점", (1.0, 0.3, 0.6), 0.4, emit=1.5)

BX, BS = Vector((-0.55, 0, 0.36)), Vector((0.42, 0.34, 0.36))      # 벽돌 중심 · 반치수
bp = empty("벽돌축", loc=BX); brick = box(tuple(2 * BS), bm_, bp)
corners = [Vector((sx * BS.x, sy * BS.y, sz * BS.z)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
bbars, balls = [], []
for i, a in enumerate(corners):
    for b in corners[i + 1:]:
        if sum(abs(p - q) > 1e-6 for p, q in zip(a, b)) == 1: o = bar(BX + a, BX + b, 0.018, line_s); parent_keep(o, bp); bbars.append(o)
    o = ball(0.06, dot, loc=BX + a); parent_keep(o, bp); balls.append(o)

CX, R, H = Vector((0.62, 0, 0)), 0.32, 0.85
cp = empty("원통축", loc=CX); cylo = cyl(R, H, cm_, cp, (0, 0, H / 2))
rings = []
for z in (0.0, H):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.018, major_segments=64, minor_segments=8)
    o = put(bpy.context.object, line_c, loc=CX + Vector((0, 0, z))); parent_keep(o, cp); rings.append(o)
sides = [bar(CX + Vector((s * R, 0, 0)), CX + Vector((s * R, 0, H)), 0.018, line_s) for s in (-1, 1)]   # 옆선(정면에서 본 윤곽)

cat = 고양이("고양이", (-1.6, -0.75, 0)); cat[0].rotation_euler.z = 0.2
cams = {"front": camera("front", (0, -3.5, 1.4), (0, 0, 0.5), 30),
        "close": camera("close", (0.3, -2.3, 1.7), (0, 0, 0.45), 30),
        "brick": camera("brick", (-0.3, -2.0, 1.5), (-0.5, 0, 0.4), 32),
        "cylc": camera("cylc", (0.5, -2.0, 1.5), (0.62, 0, 0.42), 32),
        "side": camera("side", (1.2, -2.9, 1.1), (0, 0, 0.45), 30),
        "top": camera("top", (0.2, -1.5, 3.0), (0, 0, 0.3), 28),
        "orbit": camera("orbit", (0, -3.3, 1.6), (0, 0, 0.45), 30),
        "low": camera("low", (-0.8, -2.6, 0.25), (-0.6, 0, 0.6), 24)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    fade = g(1, 0.1, 0.6) * (1 - g(5, 0.3, 0.9))
    ba.default_value = ca.default_value = 1 - 0.85 * fade
    ba.keyframe_insert("default_value", frame=fr); ca.keyframe_insert("default_value", frame=fr)
    for o in bbars + rings + sides: o.hide_render = fr < L[1][0] + 4 or (fr >= L[6][0] and g(6, 0, 1) > 0.6); o.keyframe_insert("hide_render", frame=fr)
    for k, o in enumerate(balls):
        u = g(2, 0.1 + 0.08 * k, 0.25 + 0.08 * k); s = max(1e-3, u * (1 + 0.6 * math.sin(math.pi * u)))
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=fr)
    for o in rings:
        s = 1 + 0.25 * math.sin(math.pi * g(3, 0.1, 0.5)); o.scale = (s, s, 1 + 2 * (s - 1)); o.keyframe_insert("scale", frame=fr)
    for o in sides: o.hide_render = o.hide_render or g(4, 0, 1) > 0; o.keyframe_insert("hide_render", frame=fr)  # 돌릴 땐 옆선 숨김
    spin = g(4, 0, 1) * math.pi * 1.0 + g(5, 0, 1) * 0.6 + g(6, 0, 1) * 0.6
    bp.rotation_euler = (0.35 * math.sin(math.pi * g(4, 0, 1)), 0, spin); bp.keyframe_insert("rotation_euler", frame=fr)
    cp.rotation_euler = (0.3 * math.sin(math.pi * g(4, 0, 1)), 0, -spin); cp.keyframe_insert("rotation_euler", frame=fr)
    oc = cams["orbit"][0]; a = math.radians(-90 + 40 * math.sin(math.pi * g(4, 0, 1))); oc.location = (3.3 * math.cos(a), 3.3 * math.sin(a), 1.6); oc.keyframe_insert("location", frame=fr)
    # 고양이: 줄 6 에서 벽돌 위로 폴짝
    j = g(6, 0.15, 0.6); x = -1.6 + 1.05 * j; y = -0.75 + 0.75 * j; z = 2 * BS.z * j + 0.45 * math.sin(math.pi * j)
    cat[0].location = (x, y, z); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 12), -0.5, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < j < 1)
끝(T, cams)
