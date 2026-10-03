"""1-7 Bregman B(Wagemans 외 그림23) — 흰 판 위 회색 조각. 같은 자리의 덩굴 판이 흰색(안 보임)일 땐 조각, 검게 칠하면 B 가 읽힌다."""
import bpy, bmesh, math, random
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 0.1, 1.55)).scale = (3.6, 3.0, 1)
grey = mat("글자", (0.32, 0.35, 0.42), 0.6)
for x, z, a, s in [(-0.95, 2.35, 0.25, 0.95), (0.75, 2.45, -0.35, 0.9), (-0.1, 1.55, 0.1, 1.0), (-1.05, 0.7, -0.2, 0.9), (0.95, 0.75, 0.4, 0.95)]:
    bpy.ops.object.text_add(); t = bpy.context.object
    t.data.body = "B"; t.data.extrude = 0.02; t.data.size = s; t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
    t.rotation_euler = (math.pi / 2, a, 0); t.location = (x, 0, z); t.data.materials.append(grey)

# 덩굴: 평평한 띠(판과 같은 흰색 발광 → 검정으로)
random.seed(5)
me = bpy.data.meshes.new("덩굴"); bm = bmesh.new()
for z0, w in [(0.72, 0.14), (1.15, 0.06), (1.58, 0.14), (2.0, 0.06), (2.42, 0.14)]:   # 굵은 띠가 글자 가운데를 지운다
    ph, amp = random.uniform(0, 6), 0.09
    pts = [Vector((x, 0, z0 + amp * math.sin(3.1 * x + ph) + 0.05 * math.sin(7 * x))) for x in [-1.75 + 3.5 * i / 60 for i in range(61)]]
    prev = None
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, 60)] - pts[max(i - 1, 0)]).normalized(); n = Vector((-d.z, 0, d.x)) * w
        pair = (bm.verts.new(p + n), bm.verts.new(p - n))
        if prev: bm.faces.new((prev[0], prev[1], pair[1], pair[0]))
        prev = pair
bm.to_mesh(me); bm.free()
vine = bpy.data.objects.new("덩굴", me); bpy.context.scene.collection.objects.link(vine); vine.location = (0, -0.06, 0)
vm = mat("덩굴", (1, 1, 1), 1.0, emit=1.45); vine.data.materials.append(vm)
try: vm.shadow_method = "NONE"
except AttributeError: pass
vine.visible_shadow = False
vp = next(n for n in vm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")

cat = 고양이("고양이", (-1.3, -0.7, 0)); cat[0].scale = (1.2, 1.2, 1.2)
cams = {"front": camera("front", (0, -3.7, 1.5), (0, 0, 1.55), 28),
        "close": camera("close", (0.2, -2.9, 1.7), (0.1, 0, 1.75), 26),
        "low": camera("low", (-0.4, -2.9, 0.3), (0, 0, 1.5), 22),
        "side": camera("side", (1.3, -3.3, 1.5), (0, 0, 1.55), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    dark = T.u(2, 0.15, 0.85, fr) * (1 - T.u(4, 0.1, 0.35, fr)) + T.u(4, 0.6, 0.85, fr)   # 칠함 · 5 줄에서 잠깐 지웠다 다시
    c = 1 - 0.97 * dark
    vp.inputs["Base Color"].default_value = (c, c, c, 1); vp.inputs["Base Color"].keyframe_insert("default_value", frame=fr)
    vp.inputs["Emission Color"].default_value = (c, c, c, 1); vp.inputs["Emission Color"].keyframe_insert("default_value", frame=fr)
    # 고양이: 판 앞을 왔다 갔다 · 덩굴이 칠해지면 멈춰 올려다봄
    x = -1.3 + 2.4 * (0.5 - 0.5 * math.cos(fr / 50)); walk = abs(math.sin(fr / 50)) > 0.05
    cat[0].location = (x, -0.7, 0); cat[0].rotation_euler.z = 0 if math.sin(fr / 50) >= 0 else math.pi
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0, -0.6 * dark, 0.3 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk)
    for k, (cm, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
