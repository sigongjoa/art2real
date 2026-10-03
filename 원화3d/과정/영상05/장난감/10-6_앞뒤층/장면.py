"""10-6 앞뒤층 — 지온 인형의 머리카락이 앞머리 / 뒷머리 두 껍질로 앞뒤로 벌어지고, 치마도 앞자락 / 뒷자락으로 갈라졌다 다시 닫힌다(See-through 그림 5)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
skin, skirt_m, hairF, hairB = mat("살", (0.98, 0.78, 0.62), 0.6), mat("치마", (0.45, 0.65, 0.98), 0.55), mat("앞머리", (0.95, 0.5, 0.55), 0.55), mat("뒷머리", (0.7, 0.35, 0.5), 0.55)
shirt, eye = mat("윗옷", (1.0, 0.95, 0.85), 0.6), mat("눈", (0.05, 0.05, 0.05), 0.3)
HC = Vector((0, 0, 1.03))
for x in (-0.08, 0.08): cyl(0.055, 0.42, skin, loc=(x, 0, 0.21))
cyl(0.13, 0.42, shirt, loc=(0, 0, 0.66)); ball(0.13, shirt, loc=(0, 0, 0.86), scale=(1, 0.85, 0.5))
ball(0.155, skin, loc=HC)
for s in (-1, 1):
    a = cyl(0.038, 0.4, skin, loc=(s * 0.2, 0, 0.66)); a.rotation_euler.y = s * 0.2
    ball(0.022, eye, loc=(s * 0.055, -0.145, 1.05))

def hair(front):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.19, segments=48, ring_count=24); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data); kill = []
    for v in bm.verts:
        x, y, z = v.co
        if front and (y > 0.0 or (abs(x) < 0.13 and z < 0.06) or z < -0.12): kill.append(v)
        if not front and y < 0.0: kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    if not front:
        for v in bm.verts:
            if v.co.z < 0: v.co.z *= 2.4; v.co.y += 0.02
    bm.to_mesh(o.data); bm.free(); bpy.ops.object.shade_smooth()
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.025; s.offset = 1
    return put(o, hairF if front else hairB, loc=HC)
hf, hb = hair(True), hair(False)

def skirt(front):
    bpy.ops.mesh.primitive_cone_add(radius1=0.32, radius2=0.14, depth=0.36, vertices=64, end_fill_type="NOTHING"); o = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(o.data); g = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_outer=front, clear_inner=not front)
    bm.to_mesh(o.data); bm.free(); bpy.ops.object.shade_smooth()
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.02; s.offset = 1
    return put(o, skirt_m, loc=(0, 0, 0.5))
sf, sb = skirt(True), skirt(False)

cat = 고양이("고양이", (-0.85, -0.5, 0)); cat[0].rotation_euler.z = 0.4
cams = {"front": camera("front", (0, -3.0, 0.7), (0, 0, 0.68), 50),
        "close": camera("close", (0.35, -1.5, 1.2), (0, 0, 0.95), 36),
        "side": camera("side", (1.7, -1.9, 0.95), (0, 0, 0.7), 36),
        "wide": camera("wide", (1.0, -3.0, 0.5), (-0.1, 0, 0.62), 38),
        "low": camera("low", (1.0, -1.6, 0.25), (0, 0, 0.5), 28)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    close = 1 - g(6, 0.1, 0.6)
    h = g(1, 0.2, 0.9) * close; s = g(4, 0.05, 0.5) * close
    hf.location = HC + Vector((0, -0.3 * h, 0.03 * math.sin(fr / 8) * h)); hb.location = HC + Vector((0, 0.3 * h, 0))
    sf.location = (0, -0.28 * s, 0.5); sb.location = (0, 0.28 * s, 0.5)
    for o in (hf, hb, sf, sb): o.keyframe_insert("location", frame=fr)
    hop = 0.2 * math.sin(math.pi * g(2, 0.1, 0.35)) + 0.2 * math.sin(math.pi * g(4, 0.4, 0.6))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.6 + 0.3 * g(4, 0, 0.3), 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
