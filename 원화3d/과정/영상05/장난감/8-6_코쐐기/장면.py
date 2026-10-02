"""8-6 코 쐐기 — Vanderpoel 1907 p39. 큰 달걀 얼굴 석상에 코가 쐐기로 솟는다 · 네 면(콧등 · 옆 둘 · 밑)에 차례로 색 · 해가 위로 돌아 콧등은 밝고 밑은 그늘 · 코끝 · 콧방울 공이 붙어 진짜 코."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

skin = mat("살", (0.98, 0.76, 0.62), 0.7); dark = mat("눈", (0.05, 0.05, 0.06), 0.3)
SK = (0.98, 0.76, 0.62)
cyl(0.35, 0.6, skin, loc=(0, 0.05, 0.3))
H = empty("머리", loc=(0, 0, 1.4))
ball(0.8, skin, H, (0, 0, 0), (0.8, 0.9, 1.1))
for s in (-1, 1):
    ball(0.07, dark, H, (s * 0.24, -0.64, 0.12)); box((0.3, 0.1, 0.06), skin, H, (s * 0.22, -0.66, 0.26), bevel=0.02)
box((0.26, 0.06, 0.04), mat("입", (0.9, 0.45, 0.45), 0.6), H, (0, -0.64, -0.42), bevel=0.015)

# 쐐기 코: 뿌리 둘 · 코끝 둘 · 밑 뒤 둘 → 네 면(콧등 · 왼 · 오른 · 밑), 면마다 재질
v = [(-0.04, 0, 0.42), (0.04, 0, 0.42), (0.07, -0.3, -0.12), (-0.07, -0.3, -0.12), (0.17, 0, -0.18), (-0.17, 0, -0.18)]
f = [(0, 3, 2, 1), (0, 5, 3), (1, 2, 4), (3, 5, 4, 2), (0, 1, 4, 5)]
nm = [mat("콧등", SK, 0.6), mat("왼", SK, 0.6), mat("오른", SK, 0.6), mat("밑", SK, 0.6)]
me = bpy.data.meshes.new("코"); me.from_pydata(v, [], f); me.update()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
for m in nm + [skin]: me.materials.append(m)
for i, p in enumerate(me.polygons): p.material_index = min(i, 4)
N = bpy.data.objects.new("코", me); bpy.context.scene.collection.objects.link(N); N.parent = H; N.location = (0, -0.6, -0.08)
cols = [(1.0, 0.92, 0.55), (0.55, 0.8, 1.0), (0.55, 0.8, 1.0), (0.7, 0.45, 0.85)]
soft = [ball(0.075, skin, N, (0, -0.26, -0.08)), ball(0.055, skin, N, (-0.1, -0.13, -0.13), (1, 1.2, 0.9)), ball(0.055, skin, N, (0.1, -0.13, -0.13), (1, 1.2, 0.9))]
sun = next(o for o in bpy.data.objects if o.type == "LIGHT")

cams = {"front": camera("front", (0, -3.2, 1.4), (0, 0, 1.3), 30),
        "close": camera("close", (0.55, -1.75, 1.35), (0, -0.7, 1.32), 35),
        "side": camera("side", (2.0, -1.6, 1.4), (0, -0.6, 1.3), 32),
        "low": camera("low", (0.5, -1.7, 0.75), (0, -0.6, 1.3), 30),
        "top": camera("top", (0.3, -1.6, 2.5), (0, -0.7, 1.3), 32),
        "orbit": camera("orbit", (0, -2.2, 1.4), (0, -0.6, 1.3), 32)}

for fr in range(1, T.end + 1):
    t = fr / 24
    H.rotation_euler = (0, 0, 0.25 * math.sin(t * 0.7)); key(H, fr, "rotation_euler")
    g = T.u(0, 0.0, 0.5, fr); N.scale = (1, max(0.001, g), 1); key(N, fr, "scale")          # 코가 얼굴에서 솟는다
    for j, m in enumerate(nm):
        k = T.u(1, 0.5, 0.8, fr) if j == 0 else T.u(2, 0.05 + 0.3 * (j - 1) * (j < 3) + 0.6 * (j == 3), 0.3 + 0.3 * (j - 1) * (j < 3) + 0.6 * (j == 3), fr)
        if j == 0: k = max(k, T.u(2, 0, 0.2, fr))
        k *= 1 - T.u(4, 0.3, 0.8, fr)
        c = [SK[i] + (cols[j][i] - SK[i]) * k for i in range(3)] + [1]
        p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Base Color"].default_value = c
        p.inputs["Base Color"].keyframe_insert("default_value", frame=fr)
    for i, o in enumerate(soft):
        k = T.u(4, 0.3 + 0.15 * i, 0.6 + 0.15 * i, fr); o.scale = Vector((1, 1.2, 0.9) if i else (1, 1, 1)) * max(0.001, k * (1 + 0.3 * math.sin(math.pi * k)))
        o.hide_render = k < 0.02; key(o, fr, "scale", "hide_render")
    # 3 줄: 해가 머리 위로 올라 콧등만 밝다
    a = T.u(3, 0.1, 0.6, fr) * (1 - T.u(4, 0.2, 0.7, fr))
    sun.rotation_euler = (math.radians(50 - 35 * a), 0, math.radians(-30 + 30 * a)); key(sun, fr, "rotation_euler")
    oc, _ = cams["orbit"]; b = math.radians(-90 + 55 * math.sin(t * 0.6)); oc.location = (2.2 * math.cos(b), 2.2 * math.sin(b), 1.5); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.55 * math.cos(t * 0.5); key(cc, fr, "location")
끝(T, cams)
