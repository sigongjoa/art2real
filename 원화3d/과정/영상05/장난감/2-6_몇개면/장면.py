"""2-6 몇 개면 — 원판 → 기둥 → 그릇이 하나씩 떨어져 와인잔이 되고, 원통 + 머리 → 손전등이 켜진다(Biederman 1987 그림 12)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

def bowl(R, m, parent, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=48, ring_count=24); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 1e-4], context="VERTS"); bm.to_mesh(o.data); bm.free()
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.025
    bpy.ops.object.shade_smooth(); return put(o, m, parent, loc)

T = 시작(); 무대(ARGS[1])
gm, wine = mat("잔", (0.55, 0.78, 0.98), 0.25), mat("포도주", (0.75, 0.15, 0.3), 0.3)
glass = empty("잔", loc=(0, 0, 0))
g_parts = [cyl(0.24, 0.04, gm, glass, (0, 0, 0.02), bevel=0.015), cyl(0.035, 0.5, gm, glass, (0, 0, 0.29)), bowl(0.3, gm, glass, (0, 0, 0.84))]
g_parts[2].scale = (1, 1, 1.1)
fill = cyl(0.27, 0.02, wine, glass, (0, 0, 0.78))
g_home = [o.location.copy() for o in g_parts]
fm, hm, beam_m = mat("몸통", (0.98, 0.62, 0.35), 0.5), mat("머리", (0.95, 0.45, 0.4), 0.5), mat("빛", (1.0, 0.95, 0.6), 0.5, emit=3.0, alpha=True)
fl = empty("손전등", loc=(0.45, -0.2, 0.15))
barrel = cyl(0.11, 0.6, fm, fl, (0, 0, 0), (0, math.pi / 2, 0), bevel=0.02)
bpy.ops.mesh.primitive_cone_add(radius1=0.11, radius2=0.2, depth=0.2, vertices=48, rotation=(0, math.pi / 2, 0))
head = put(bpy.context.object, hm, fl, (0.4, 0, 0)); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cone_add(radius1=0.19, radius2=0.7, depth=1.6, vertices=48, rotation=(0, math.pi / 2, 0), end_fill_type="NOTHING")
beam = put(bpy.context.object, beam_m, fl, (1.3, 0, 0)); ba = alpha_of(beam_m)
fl.rotation_euler.z = -0.5

cat = 고양이("고양이", (-0.95, -0.55, 0)); cat[0].rotation_euler.z = 0.3
cams = {"front": camera("front", (0, -3.0, 0.55), (0.0, 0, 0.6), 38),
        "close": camera("close", (0.5, -1.9, 1.1), (0, 0, 0.5), 34),
        "side": camera("side", (1.3, -2.0, 0.7), (0, 0, 0.5), 34),
        "low": camera("low", (-0.6, -2.1, 0.2), (-0.1, 0, 0.5), 26)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    for k, o in enumerate(g_parts):
        u = g(k + 1, 0.05, 0.35); bounce = 0.06 * math.sin(math.pi * g(k + 1, 0.35, 0.5))
        o.location = g_home[k] + Vector((0, 0, 1.8 * (1 - u) + bounce)); s = max(1e-3, min(1, u * 3))
        o.scale = (s, s, s * (1.1 if k == 2 else 1)); o.keyframe_insert("location", frame=fr); o.keyframe_insert("scale", frame=fr)
    w = g(3, 0.5, 0.8); fill.scale = (max(1e-3, w),) * 3; fill.keyframe_insert("scale", frame=fr)
    aside = g(4, 0, 0.3)                                                       # 잔은 왼쪽 뒤로 비킴
    glass.location = (-0.55 * aside, 0.5 * aside, 0); glass.rotation_euler.z = 0.3 * math.sin(fr / 18)
    glass.keyframe_insert("location", frame=fr); glass.keyframe_insert("rotation_euler", frame=fr)
    ub = g(4, 0.2, 0.55); uh = g(5, 0.05, 0.4)
    barrel.scale = (max(1e-3, ub),) * 3; head.scale = (max(1e-3, uh),) * 3
    head.location = (0.4 + 1.2 * (1 - uh), 0, 0)
    barrel.keyframe_insert("scale", frame=fr); head.keyframe_insert("scale", frame=fr); head.keyframe_insert("location", frame=fr)
    on = g(5, 0.5, 0.65); ba.default_value = 0.35 * on; ba.keyframe_insert("default_value", frame=fr)
    beam.hide_render = on <= 0; beam.keyframe_insert("hide_render", frame=fr)
    fl.rotation_euler.z = -0.5 + 0.25 * math.sin(fr / 15) * on; fl.keyframe_insert("rotation_euler", frame=fr)
    hop = 0.2 * (math.sin(math.pi * g(3, 0.4, 0.65)) + math.sin(math.pi * g(5, 0.45, 0.7)))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.35 * math.sin(fr / 10) * (1 - g(3, 0.4, 0.5)), -0.5, 0.4 * g(4, 0, 0.4)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
