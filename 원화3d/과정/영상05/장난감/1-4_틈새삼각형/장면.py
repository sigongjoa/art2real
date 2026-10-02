"""1-4 홈 판 사이 삼각형(Kellman & Shipley 1991 그림6) — 세로 틈이 난 판이 미끄러지며 뒤 삼각형을 띠로만 보여 준다 · 판을 걷으면 온전한 삼각형."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
put(bpy.context.object, mat("흰판", (1, 1, 1), 1.0, emit=1.45), loc=(0, 1.0, 1.5)).scale = (3.4, 3.0, 1)
# 삼각형(주황, 두께 있는 판)
me = bpy.data.meshes.new("tri"); bm = bmesh.new()
bm.faces.new([bm.verts.new(v) for v in ((-1.0, 0, 0.45), (1.0, 0, 0.45), (0, 0, 2.5))]); bm.to_mesh(me); bm.free()
tri = bpy.data.objects.new("삼각형", me); bpy.context.scene.collection.objects.link(tri)
tri.location = (0, 0.6, 0); tri.modifiers.new("두께", "SOLIDIFY").thickness = 0.06
tri.data.materials.append(mat("삼각", (1.0, 0.45, 0.12), 0.7, emit=1.0))
# 틈 판: 남색 널 + 위아래 틀 (빈 객체 하나에 달아 같이 움직임)
navy = mat("널", (0.16, 0.2, 0.42), 0.7)
panel = empty("틈판", loc=(0, 0, 0))
for k in range(-9, 10):
    box((0.36, 0.06, 2.5), navy, panel, (k * 0.5, 0, 1.45), bevel=0.015)
box((10, 0.08, 0.2), navy, panel, (0, 0, 0.15)); box((10, 0.08, 0.2), navy, panel, (0, 0, 2.75))

cat = 고양이("고양이", (-1.6, -0.6, 0)); cat[0].scale = (1.4, 1.4, 1.4)
cams = {"front": camera("front", (0, -4.0, 1.4), (0, 0, 1.45), 30),
        "slide": camera("slide", (-0.6, -3.6, 1.2), (0, 0, 1.45), 30),
        "close": camera("close", (0, -2.9, 1.5), (0, 0, 1.5), 32),
        "low": camera("low", (-0.6, -2.7, 0.3), (0, 0, 1.4), 24),
        "side": camera("side", (1.0, -3.4, 1.6), (0, 0.4, 1.4), 28),
        "wide": camera("wide", (0, -5.0, 1.7), (0, 0.4, 1.5), 28)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    lift = T.u(4, 0.05, 0.6, fr) if fr >= T.lines[4][0] else 0
    back = T.u(6, 0.2, 0.9, fr) if fr >= T.lines[6][0] else 0       # 마지막 줄에 판이 다시 내려옴
    h = lift * (1 - back)
    panel.location = (0.25 * math.sin(fr / 30) * (1 - h), 0, 3.4 * h)
    panel.keyframe_insert("location", frame=fr)
    # 고양이: 판 앞을 서성 · 판이 걷히면 삼각형 앞으로 걸어가 올려다봄
    x = -1.6 + 0.5 * math.sin(fr / 45); walk = True
    if fr >= T.lines[4][0]:
        u = T.u(4, 0.4, 1, fr); x = x * (1 - u) + (-0.55) * u
    cat[0].location = (x, -0.6, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.5, 0.35 * math.sin(fr / 12)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, walk and not (fr >= T.lines[4][0] and T.u(4, 0.4, 1, fr) >= 1))
    for k, (c, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 53)
        if k == "slide": p.x = -0.6 + 1.2 * T.u(1, 0, 1, fr)
        c.location = p; c.keyframe_insert("location", frame=fr)
끝(T, cams)
