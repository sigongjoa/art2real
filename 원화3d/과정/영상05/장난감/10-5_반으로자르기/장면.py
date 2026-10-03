"""10-5 반으로 자르기 — 지온 인형(소체 + 치마 껍질 + 머리 껍질)을 빛 칼날이 세로로 가르고, 두 쪽이 벌어져 단면을 보인다 · 몸은 꽉 참, 옷 · 머리는 얇은 껍질(StdGEN 그림 6)."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
skin, dress_m, hair_m = mat("살", (0.98, 0.78, 0.62), 0.6), mat("옷", (0.45, 0.65, 0.98), 0.55), mat("머리", (0.62, 0.35, 0.3), 0.55)
sec = mat("단면", (0.95, 0.35, 0.4), 0.7)
eye = mat("눈", (0.05, 0.05, 0.05), 0.3)

def shell_from(o, t):
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = t; s.offset = 1; return o
src = []   # (객체, 꽉 찬가?)
for x in (-0.08, 0.08): src.append((cyl(0.06, 0.4, skin, loc=(x, 0, 0.2)), True))
src.append((cyl(0.13, 0.4, skin, loc=(0, 0, 0.6)), True)); src.append((ball(0.13, skin, loc=(0, 0, 0.8), scale=(1, 0.85, 0.6)), True))
src.append((ball(0.155, skin, loc=(0, 0, 1.03)), True))
for s in (-1, 1):
    a = cyl(0.04, 0.42, skin, loc=(s * 0.27, 0, 0.62)); a.rotation_euler.y = s * 0.25; src.append((a, True))
    src.append((ball(0.022, eye, loc=(s * 0.055, -0.145, 1.05)), True))
bpy.ops.mesh.primitive_cone_add(radius1=0.33, radius2=0.155, depth=0.5, vertices=64, end_fill_type="NOTHING")
dress = put(bpy.context.object, dress_m, loc=(0, 0, 0.6)); bpy.ops.object.shade_smooth(); shell_from(dress, 0.02); src.append((dress, False))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, segments=48, ring_count=24); hair = bpy.context.object
bm = bmesh.new(); bm.from_mesh(hair.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.03 and (v.co.y < 0.02 or v.co.z < -0.15)], context="VERTS"); bm.to_mesh(hair.data); bm.free()
put(hair, hair_m, loc=(0, 0.01, 1.05)); bpy.ops.object.shade_smooth(); shell_from(hair, 0.025); src.append((hair, False))

# 굳히기(모디파이어 · 변환 적용) → x=0 에서 가르기
bpy.ops.object.select_all(action="DESELECT")
for o, _ in src: o.select_set(True)
bpy.context.view_layer.objects.active = src[0][0]
bpy.ops.object.convert(target="MESH"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
L_half, R_half = empty("왼쪽"), empty("오른쪽")
for o, solid in src:
    o2 = o.copy(); o2.data = o.data.copy(); bpy.context.scene.collection.objects.link(o2)
    for ob, keep_neg in ((o, True), (o2, False)):
        bm = bmesh.new(); bm.from_mesh(ob.data); g = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=keep_neg, clear_inner=not keep_neg)
        if solid:
            if len(ob.data.materials) < 2: ob.data.materials.append(sec)
            r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
            for f in r["faces"]: f.material_index = 1; f.smooth = False
        bm.to_mesh(ob.data); bm.free()
        ob.parent = L_half if keep_neg else R_half
        if not bm.is_valid and len(ob.data.vertices) == 0: ob.hide_render = True

blade_m = mat("칼날", (1.0, 0.95, 0.6), 0.4, emit=3.0, alpha=True); alpha_of(blade_m).default_value = 0.5
blade = box((0.01, 1.0, 0.02), blade_m, loc=(0, 0, 2.0))

cat = 고양이("고양이", (-0.95, -0.45, 0)); cat[0].rotation_euler.z = 0.35
cams = {"front": camera("front", (0, -3.0, 0.75), (0, 0, 0.62), 40),
        "close": camera("close", (0.4, -1.8, 1.0), (0, 0, 0.65), 36),
        "side": camera("side", (1.1, -2.0, 0.9), (0, 0, 0.6), 36),
        "wide": camera("wide", (0, -3.3, 0.6), (0, 0, 0.65), 34),
        "hair": camera("hair", (0.3, -1.2, 1.35), (0, 0.0, 0.98), 36),
        "low": camera("low", (-0.4, -2.2, 0.2), (-0.2, 0, 0.6), 26)}

L = T.lines
for fr in range(1, T.end + 1):
    g = lambda i, a=0.0, b=1.0: T.u(i, a, b, fr) if fr >= L[i][0] else 0
    c = g(1, 0.1, 0.8); blade.location.z = 1.8 - 1.85 * c; blade.scale.z = 0.02 if 0 < c < 1 else 0.001
    blade.hide_render = not (0 < c < 1) and fr >= L[1][0]
    if fr < L[1][0]: blade.hide_render = True
    blade.keyframe_insert("location", frame=fr); blade.keyframe_insert("scale", frame=fr); blade.keyframe_insert("hide_render", frame=fr)
    opn = g(2, 0.0, 0.5) * (1 - g(6, 0.2, 0.8)); wob = 0.04 * math.sin(fr / 12) * opn
    L_half.location = (-0.36 * opn, -0.05 * opn, 0.0); L_half.rotation_euler.z = -0.95 * opn + wob
    R_half.location = (0.36 * opn, -0.05 * opn, 0.0); R_half.rotation_euler.z = 0.95 * opn - wob
    for h in (L_half, R_half): h.keyframe_insert("location", frame=fr); h.keyframe_insert("rotation_euler", frame=fr)
    hop = 0.22 * math.sin(math.pi * g(1, 0.75, 0.95)) + 0.15 * math.sin(math.pi * g(6, 0.75, 0.95))
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0.3 * math.sin(fr / 11), -0.5, 0); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
끝(T, cams)
