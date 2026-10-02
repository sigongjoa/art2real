"""7-4 공과 원반(Tse 1999 그림 9) — 음영 없는 남색 동그라미 둘. 불이 켜지면 왼쪽은 공, 오른쪽은 원반. 원반이 동전처럼 돌고 공은 통통 튄다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def 키(o, fr, *props):
    for q in props: o.keyframe_insert(q, frame=fr)

def 켜지는색(name, flat, lit):          # 섞기 0 = 음영 없는 단색 · 1 = 보통 재질
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    p.inputs["Base Color"].default_value = (*lit, 1); p.inputs["Roughness"].default_value = 0.45
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (*flat, 1); em.inputs[1].default_value = 1.0
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(em.outputs[0], mx.inputs[1]); nt.links.new(p.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0]); return m, mx.inputs[0]

T = 시작(); 무대(ARGS[1])
bm = mat("판", (1, 1, 1), 1.0, emit=1.45)
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); put(bpy.context.object, bm, loc=(0, 1.0, 1.6)).scale = (3.2, 3.2, 1)
m, f = 켜지는색("공색", (0.1, 0.12, 0.32), (0.45, 0.6, 1.0))
sph = ball(0.45, m, loc=(-0.6, 0, 1.45))
disk = cyl(0.45, 0.06, m, loc=(0.6, 0, 1.45), rot=(math.pi / 2, 0, 0), bevel=0.01)
cat = 고양이("고양이", (-2.0, -0.8, 0))
cams = {"front": camera("front", (0, -9.5, 1.45), (0, 0, 1.4), 72),
        "close": camera("close", (0, -7.5, 1.45), (0, 0, 1.45), 80),
        "low": camera("low", (1.3, -1.9, 0.3), (0, 0, 1.2), 22),
        "side": camera("side", (2.6, -1.6, 1.6), (0, 0, 1.4), 28),
        "top": camera("top", (0.3, -1.4, 3.6), (0, 0, 1.4), 28),
        "spin": camera("spin", (1.1, -1.8, 1.5), (0.6, 0, 1.45), 34),
        "wide": camera("wide", (2.2, -4.4, 0.6), (0, 0, 1.2), 24)}
L = T.lines
for fr in range(1, T.end + 1):
    lit = T.u(2, 0.45, 0.6, fr); flick = 1 if lit >= 1 or lit <= 0 else (1 if (fr // 2) % 2 else 0) * lit
    f.default_value = flick; f.keyframe_insert("default_value", frame=fr)
    sp = T.u(5, 0.1, 1, fr) + T.u(6, 0, 1, fr)
    disk.rotation_euler = (math.pi / 2, 0, 2 * math.pi * 2.5 * sp); 키(disk, fr, "rotation_euler")
    bo = abs(math.sin((fr - L[5][0]) / 5)) * 0.35 * T.u(5, 0.0, 0.1, fr)
    sph.location.z = 1.45 + bo; 키(sph, fr, "location")
    w = T.u(0, 0.2, 0.8, fr); w2 = T.u(4, 0.0, 0.6, fr)
    cat[0].location = (-2.0 + 1.6 * w + 1.6 * w2, -0.8, 0)
    cat[0].rotation_euler.z = 0.9 * T.u(0, 0.8, 1, fr) - 0.9 * T.u(4, 0, 0.1, fr) + 0.9 * T.u(4, 0.6, 0.7, fr)
    tilt = 0.4 * math.sin(fr / 6) * (T.u(1, 0, 0.2, fr) - T.u(2, 0.4, 0.6, fr))
    look = 0.2 * math.sin(2 * math.pi * 2.5 * sp) * T.u(5, 0, 0.2, fr)
    cat[1].rotation_euler = (tilt, -0.7, look)
    키(cat[0], fr, "location", "rotation_euler"); 키(cat[1], fr, "rotation_euler"); 고양이_키(cat, fr, (0 < w < 1) or (0 < w2 < 1))
    c = cams["front"][0]; c.location.x = 0.1 * math.sin(fr / 40); 키(c, fr, "location")
    c = cams["side"][0]; c.location.y = -1.6 + 1.2 * T.u(4, 0, 1, fr); 키(c, fr, "location")
    c = cams["wide"][0]; c.location.x = 2.2 - 1.2 * fr / T.end; 키(c, fr, "location")
끝(T, cams)
