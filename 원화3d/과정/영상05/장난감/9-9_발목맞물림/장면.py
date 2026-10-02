"""9-9 발목 맞물림 — Bridgman 1920 p205. 큰 발 조각: 뒤꿈치 블록 + 앞발 쐐기 블록이 갈라졌다 다시 붙고 · 정강이 기둥이 들렸다 내려와 양쪽 복사뼈 갈퀴로 발목 블록을 걸터 문다 · 발끝이 오르내려도 정강이는 그 자리."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def mesh(name, v, f, m, parent, loc):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = 0.015, 2
    return put(o, m, parent, loc)

heel_m, front_m, shin_m = mat("뒤꿈치", (1.0, 0.6, 0.48), 0.55), mat("앞발", (0.48, 0.82, 0.62), 0.55), mat("정강이", (1.0, 0.84, 0.4), 0.55)
cyl(0.9, 0.04, mat("받침", (0.93, 0.9, 0.84), 0.8), loc=(0, -0.2, 0.02), bevel=0.01)
AX = 0.47                                            # 발목 축 높이
F = empty("발", loc=(0, 0, AX))
heel = box((0.26, 0.32, 0.34), heel_m, F, (0, 0.12, -0.26), bevel=0.03)
talus = box((0.18, 0.24, 0.13), heel_m, F, (0, 0.02, -0.03), bevel=0.03)
# 앞발 쐐기: 뒤는 높고(0.3) 발끝으로 낮아진다(0.08)
fv = [(-0.15, 0, 0), (0.15, 0, 0), (0.15, -0.6, 0), (-0.15, -0.6, 0), (-0.13, 0, 0.3), (0.13, 0, 0.3), (0.12, -0.6, 0.08), (-0.12, -0.6, 0.08)]
FB = empty("앞발자리", F, (0, -0.04, -0.43))
front = mesh("앞발", fv, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], front_m, FB, (0, 0, 0))
S = empty("정강이", loc=(0, 0.02, AX))
box((0.2, 0.2, 0.95), shin_m, S, (0, 0, 0.6), bevel=0.03)
for sx in (-1, 1):
    box((0.05, 0.13, 0.22), shin_m, S, (sx * 0.12, 0, 0.03), bevel=0.015); ball(0.055, shin_m, S, (sx * 0.135, 0, -0.02))

cams = {"front": camera("front", (1.7, -2.6, 0.9), (0, -0.15, 0.6), 30),
        "close": camera("close", (1.0, -1.3, 0.6), (0, -0.05, 0.45), 32),
        "side": camera("side", (2.4, -0.3, 0.7), (0, -0.15, 0.55), 30),
        "low": camera("low", (0.9, -1.4, 0.15), (0, 0, 0.5), 26),
        "orbit": camera("orbit", (0, -2.6, 0.9), (0, -0.1, 0.6), 30)}

for fr in range(1, T.end + 1):
    t = fr / 24
    sp = math.sin(math.pi * T.u(1, 0.2, 0.9, fr))      # 1 줄: 앞발이 앞으로 갈라졌다 붙는다
    FB.location.y = -0.04 - 0.35 * sp; key(FB, fr, "location")
    for o, j in ((heel, 0), (front, 1)):              # 2 줄: 차례로 통 튄다
        k = math.sin(math.pi * T.u(2, 0.05 + 0.45 * j, 0.4 + 0.45 * j, fr)); o.location.z = (o.location.z if o is front else -0.26) + (0 if o is front else 0.1 * k)
        if o is front: o.location.z = 0.1 * k
        key(o, fr, "location")
    up = math.sin(math.pi * T.u(3, 0.0, 0.8, fr))        # 3 줄: 정강이가 들렸다 내려와 문다
    S.location.z = AX + 0.45 * up + 0.03 * math.sin(t * 2) * (1 - T.u(1, 0, 0.3, fr)); key(S, fr, "location")
    flex = math.sin(2 * math.pi * T.u(4, 0.1, 1.0, fr)) * 0.35 + math.sin(2 * math.pi * T.u(5, 0.0, 0.9, fr)) * 0.3
    F.rotation_euler.x = flex; key(F, fr, "rotation_euler")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 70 * T.u(6, 0, 1, fr) + 25 * math.sin(t * 0.5)); oc.location = (2.6 * math.cos(a), -0.1 + 2.6 * math.sin(a), 0.9); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 1.0 + 0.3 * math.sin(t * 0.6); key(cc, fr, "location")
끝(T, cams)
