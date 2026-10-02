"""2-2 원기둥 변신 — 원기둥 하나가 단면(각) · 크기(좁아짐) · 축(휨)을 하나씩 바꿔 벽돌 · 원뿔 · 굽은 관으로 모핑 → 넷이 나란히 서고 돈다(Biederman 1987 그림 6)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

NA, NL = 32, 24
def pts(R, H, sq=0, tp=0, bd=0):
    """스윕 꼭짓점: sq=단면 각짐 · tp=끝 좁힘 · bd=축 휨(0..1 → 90°)."""
    out = []
    for j in range(NL + 1):
        t = j / NL; r = R * (1 - 0.95 * tp * t)
        if bd < 1e-4: c, tang = Vector((0, 0, H * t)), Vector((0, 0, 1))
        else:
            K = bd * math.pi / 2; Rc = H / K; ph = K * t
            c, tang = Vector((Rc * (1 - math.cos(ph)), 0, Rc * math.sin(ph))), Vector((math.sin(ph), 0, math.cos(ph)))
        nx = Vector((tang.z, 0, -tang.x)); ny = Vector((0, 1, 0))
        for i in range(NA):
            a = 2 * math.pi * i / NA + math.pi / 4; ca, sa = math.cos(a), math.sin(a)
            m = max(abs(ca), abs(sa)); k = (1 - sq) + sq / m * 0.8
            out.append(c + (nx * ca + ny * sa) * r * k)
    return out
def sweep(name, R, H, m, loc, keys):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts(R, H)]
    for j in range(NL):
        for i in range(NA): bm.faces.new([vs[j * NA + i], vs[j * NA + (i + 1) % NA], vs[(j + 1) * NA + (i + 1) % NA], vs[(j + 1) * NA + i]])
    bm.faces.new(vs[:NA][::-1]); bm.faces.new(vs[NL * NA:])
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    try: me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(35)
    except AttributeError: pass
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = loc; me.materials.append(m)
    o.shape_key_add(name="basis")
    for kn, kw in keys.items():
        sk = o.shape_key_add(name=kn); P = pts(R, H, **kw)
        for v, p in zip(sk.data, P): v.co = p
    for k in o.data.shape_keys.key_blocks[1:]: k.value = 1.0 if len(keys) == 1 else 0.0
    return o
def key(o, kn, val, fr):
    k = o.data.shape_keys.key_blocks[kn]; k.value = val; k.keyframe_insert("value", frame=fr)

T = 시작(); 무대(ARGS[1])
blue = mat("파랑", (0.35, 0.6, 0.95), 0.5)
hero = sweep("원기둥", 0.4, 1.45, blue, (-0.25, 0, 0), {"sq": dict(sq=1), "tp": dict(tp=1), "bd": dict(bd=1)})
row_m = [mat("줄%d" % i, c, 0.5) for i, c in enumerate([(0.35, 0.6, 0.95), (0.95, 0.45, 0.4), (0.98, 0.8, 0.3), (0.55, 0.85, 0.5)])]
row = [sweep("줄%d" % i, 0.24, 1.0, row_m[i], (x, 0.3, 0), {k: {k: 1}} if k else {}) for i, (x, k) in enumerate(zip((-1.05, -0.35, 0.35, 1.05), (None, "sq", "tp", "bd")))]
cat = 고양이("고양이", (-0.95, -0.6, 0)); cat[0].rotation_euler.z = 0.3

cams = {"front": camera("front", (0, -3.4, 0.5), (0, 0, 0.9), 36),
        "close": camera("close", (0.5, -2.3, 1.2), (0, 0, 0.8), 32),
        "side": camera("side", (1.0, -2.8, 0.5), (0.0, 0, 0.85), 32),
        "low": camera("low", (-0.7, -2.0, 0.2), (-0.4, 0, 0.75), 24),
        "wide": camera("wide", (0, -3.5, 0.4), (0, 0.2, 0.75), 26),
        "orbit": camera("orbit", (0, -3.6, 1.0), (0, 0.3, 0.6), 26)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a, b: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    # 주인공: 줄 1·2·3 에서 하나씩 바꿨다 되돌림 · 줄 4 에서 작아지며 사라짐
    for i, kn in ((1, "sq"), (2, "tp"), (3, "bd")):
        v = g(i, 0.05, 0.45) * (1 - (g(i + 1, 0.0, 0.25) if i < 3 else 0)) if i < 3 else g(i, 0.05, 0.45) * (1 - g(4, 0, 0.2))
        key(hero, kn, v, fr)
    pulse = 1 + 0.06 * math.sin(fr / 4) * (1 - g(4, 0, 0.3))
    s = pulse * (1 - g(4, 0.0, 0.3)); hero.scale = (s, s, s); hero.keyframe_insert("scale", frame=fr)
    hero.rotation_euler.z = fr / FPS * 0.6; hero.keyframe_insert("rotation_euler", frame=fr)
    # 줄: 줄 4 에서 차례로 솟아남 · 이후 제자리 돌기
    for i, o in enumerate(row):
        u = g(4, 0.15 + 0.15 * i, 0.4 + 0.15 * i); s = max(1e-3, u * (1 + 0.25 * math.sin(math.pi * u)))
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=fr)
        o.rotation_euler.z = g(5, 0, 1) * math.pi * 2 * (1 if i % 2 else -1) + 0.4; o.keyframe_insert("rotation_euler", frame=fr)
    oc = cams["orbit"][0]; a = math.radians(-90 + 50 * g(5, 0, 1) - 25); oc.location = (3.6 * math.cos(a), 0.3 + 3.6 * math.sin(a), 1.3); oc.keyframe_insert("location", frame=fr)
    # 고양이: 바뀔 때마다 움찔 · 줄 6 에서 줄 앞을 걸음
    hop = sum(math.sin(math.pi * g(i, 0.05, 0.25)) for i in (1, 2, 3)) * 0.18
    walk = g(6, 0.0, 0.8); x = -0.95 - 0.4 * g(4, 0, 0.3) + 2.4 * walk
    cat[0].location = (x, -0.55, hop); cat[0].rotation_euler.z = 0.3 * (1 - g(6, 0, 0.1)); cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0.25 * math.sin(fr / 11), -0.4, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < walk < 1)
끝(T, cams)
