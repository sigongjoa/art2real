"""8-8 창 빛 원뿔 — Speed 1913 Diagram V. 풀밭에 선 창틀(면광원) 앞 반들한 원뿔 · 고양이가 원뿔을 돌아 걸으면 하이라이트가 고양이 눈을 따라 미끄러진다 · 그늘 쪽엔 바닥 빛(반사광)이 옅게 켜진다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)

sun = next(o for o in bpy.data.objects if o.type == "LIGHT"); sun.data.energy = 1.2
bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=1.6, vertices=96, location=(0, 0, 0.8)); C = bpy.context.object
bpy.ops.object.shade_smooth(); put(C, mat("원뿔", (0.85, 0.45, 0.38), 0.07), loc=(0, 0, 0.8))
# 창: 빛나는 유리 + 나무 틀 + 뒤에 면광원(원뿔 쪽을 본다)
WX = -1.5
wood, glass = mat("틀", (0.55, 0.38, 0.25), 0.7), mat("유리", (1.0, 0.97, 0.88), 0.5, emit=1.6)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(0, math.pi / 2, 0)); g = put(bpy.context.object, glass, loc=(WX, -0.3, 1.25)); g.scale = (1.5, 1.0, 1)
for p, q in [((WX, -0.82, 0.48), (WX, -0.82, 2.02)), ((WX, 0.22, 0.48), (WX, 0.22, 2.02)), ((WX, -0.82, 0.5), (WX, 0.22, 0.5)), ((WX, -0.82, 2.0), (WX, 0.22, 2.0)), ((WX, -0.3, 0.5), (WX, -0.3, 2.0)), ((WX, -0.82, 1.25), (WX, 0.22, 1.25))]:
    bar(p, q, 0.035, wood)
for y in (-0.82, 0.22): bar((WX, y, 0), (WX, y, 0.5), 0.035, wood)
bpy.ops.object.light_add(type="AREA", location=(WX + 0.05, -0.3, 1.25), rotation=(0, -math.pi / 2, 0)); L = bpy.context.object
L.data.shape, L.data.size, L.data.size_y, L.data.energy, L.data.color = "RECTANGLE", 1.5, 1.0, 350, (1.0, 0.95, 0.85)
# 반사광: 그늘 쪽 바닥에서 올라오는 옅은 초록 빛(5 줄에 켜진다)
bpy.ops.object.light_add(type="AREA", location=(0.85, 0.35, 0.03), rotation=(math.pi, 0, 0)); B = bpy.context.object; B.data.use_shadow = False
B.data.size, B.data.color = 0.8, (0.55, 0.95, 0.5)
cat = 고양이("고양이", (0, -1.6, 0), (0.55, 0.55, 0.6))

cams = {"front": camera("front", (0.2, -3.6, 1.1), (-0.5, 0, 0.95), 28),
        "close": camera("close", (-0.2, -1.9, 1.0), (-0.1, 0, 0.8), 35),
        "wide": camera("wide", (1.6, -4.0, 1.6), (-0.8, 0, 0.9), 26),
        "side": camera("side", (-0.6, -3.4, 0.5), (-0.9, 0, 1.0), 26),
        "win": camera("win", (-1.3, -2.0, 0.8), (-1.0, 0, 1.1), 28),
        "low": camera("low", (1.3, -1.8, 0.35), (0, 0, 0.8), 28),
        "dark": camera("dark", (2.0, 0.6, 0.7), (0, 0, 0.75), 30),
        "catcam": camera("catcam", (0, -2.3, 0.6), (0, 0, 0.8), 30),
        "orbit": camera("orbit", (0, -2.6, 1.0), (0, 0, 0.8), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    # 고양이: 0–3 줄 앞에서 두리번 · 4 줄 원뿔을 돌아 오른쪽으로 걷는다 · 6 줄 앉음
    u = T.u(4, 0.0, 0.9, fr); a = math.radians(-90 + 85 * u); r = 1.6
    root = cat[0]; root.location = (r * math.cos(a), r * math.sin(a), 0)
    root.rotation_euler.z = a + math.pi / 2 if 0 < u < 1 else (math.pi / 2 if u == 0 else a + math.pi)
    key(root, fr, "location", "rotation_euler")
    cat[1].rotation_euler = (0, -0.5, 0.3 * math.sin(t * 1.5)); key(cat[1], fr, "rotation_euler")
    고양이_키(cat, fr, 0 < u < 1)
    # 고양이 눈 뒤 카메라 · 궤도 카메라도 같은 각으로 돈다 → 하이라이트가 미끄러진다
    for nm, rr, z in (("catcam", 2.3, 0.6), ("orbit", 2.6, 1.0)):
        oc, _ = cams[nm]; b = math.radians(-90 + 85 * u + (8 * math.sin(t) if nm == "orbit" else 0)); oc.location = (rr * math.cos(b), rr * math.sin(b), z); key(oc, fr, "location")
    L.data.energy = 350 * (0.3 + 0.7 * T.u(2, 0, 0.5, fr)) if fr < T.lines[3][0] else 350; L.data.keyframe_insert("energy", frame=fr)
    B.data.energy = 60 * T.u(5, 0.1, 0.5, fr); B.data.keyframe_insert("energy", frame=fr)
    fc, _ = cams["front"]; fc.location.x = 0.2 + 0.3 * math.sin(t * 0.5); key(fc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = -0.2 + 0.25 * math.sin(t * 0.8); key(cc, fr, "location")
끝(T, cams)
