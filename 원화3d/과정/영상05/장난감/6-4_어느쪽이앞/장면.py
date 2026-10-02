"""6-4 저절로 갈라지는 도형(Kellman & Shipley 1991 그림12) — 같은 색(그림자 없는 발광) 막대 두 개가 X. 정면에선 앞뒤 단서가 없고, 옆에서 보면 한쪽이 앞 · 다음엔 다른 쪽이 앞."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 0.7, 1.55)).scale = (3.8, 3.0, 1)
ink = bpy.data.materials.new("막대"); ink.use_nodes = True; nt = ink.node_tree; nt.nodes.clear()   # 빛 · 그림자 없는 평평한 색
em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.13, 0.2, 0.5, 1); em.inputs[1].default_value = 1.6
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
bars = []
for a in (0.7, -0.7):
    b = box((2.7, 0.06, 0.38), ink, loc=(0, 0, 1.55)); b.rotation_euler.y = a; bars.append(b)

cat = 고양이("고양이", (-1.2, -1.0, 0)); cat[0].scale = (1.5, 1.5, 1.5)
cams = {"front": camera("front", (0, -4.1, 1.5), (0, 0, 1.55), 28),
        "close": camera("close", (0.1, -2.8, 1.6), (0, 0, 1.55), 26),
        "low": camera("low", (-0.3, -3.0, 0.3), (0, 0, 1.5), 22),
        "orbit": camera("orbit", (0, -4.1, 1.5), (0, 0, 1.55), 26),
        "orbit2": camera("orbit2", (0, -4.1, 1.5), (0, 0, 1.55), 26)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    s = T.u(4, 0.15, 0.55, fr)                        # 5 줄: 앞뒤가 바뀜
    d = 0.3 * (1 - 2 * s)
    bars[0].location.y, bars[1].location.y = -d, d
    for b in bars: b.keyframe_insert("location", frame=fr)
    # 고양이: 고개를 좌우로 갸웃(어느 쪽?) · 4 줄에 옆으로 걸어가 봄 · 5 줄에 되돌아옴
    w = T.u(3, 0, 0.7, fr) - T.u(5, 0, 0.7, fr)
    cat[0].location.x = -1.2 + 2.0 * w; cat[0].rotation_euler.z = 0 if fr < T.lines[5][0] else math.pi
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0.45 * math.sin(fr / 8), -0.45, 0.2); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < T.u(3, 0, 0.7, fr) < 1 or 0 < T.u(5, 0, 0.7, fr) < 1)
    for k, (cm, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        if k in ("orbit", "orbit2"):
            ln = 3 if k == "orbit" else 4
            a = math.radians(-90 + 65 * T.u(ln, 0, 0.8, fr) * (1 if k == "orbit" else -1)); p = Vector((4.1 * math.cos(a), 4.1 * math.sin(a), 1.7))
        cm.location = p; cm.keyframe_insert("location", frame=fr)
끝(T, cams)
