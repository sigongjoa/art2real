"""6-8 기둥 뒤 차(Ao 외 그림2) — 고양이가 탄 장난감 차가 기둥 뒤에 선다. 보이는 부분 초록 → 기둥이 반투명해지며 숨은 부분 빨강 → 합치면 노랑 한 대."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

PX, PW = 0.0, 0.6                                 # 기둥 x · 폭
# 차 재질: 세계 x 로 칠 — 바탕 → 초록(보이는) · 빨강(숨은) · 노랑(합침)
cm = mat("차", (0.85, 0.85, 0.9), 0.5); nt = cm.node_tree; N, L = nt.nodes.new, nt.links.new
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
sep = N("ShaderNodeSeparateXYZ"); L(N("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
def m_(op, a, b):
    m = N("ShaderNodeMath"); m.operation = op
    for i, v in enumerate((a, b)):
        if isinstance(v, (int, float)): m.inputs[i].default_value = v
        else: L(v, m.inputs[i])
    return m
ax = m_("ABSOLUTE", m_("SUBTRACT", sep.outputs[0], PX).outputs[0], 0)
inside = m_("LESS_THAN", ax.outputs[0], PW / 2)
vis = m_("MULTIPLY", m_("SUBTRACT", 1.0, inside.outputs[0]).outputs[0], 0.0)     # inputs[1] 키
hid = m_("MULTIPLY", inside.outputs[0], 0.0)
def mix(fac, a, b):
    m = N("ShaderNodeMixRGB"); L(fac, m.inputs[0])
    for i, v in ((1, a), (2, b)):
        if isinstance(v, tuple): m.inputs[i].default_value = (*v, 1)
        else: L(v, m.inputs[i])
    return m
c = mix(vis.outputs[0], (0.85, 0.85, 0.9), (0.3, 0.85, 0.4)); c = mix(hid.outputs[0], c.outputs[0], (0.95, 0.25, 0.3))
uni = N("ShaderNodeMixRGB"); L(c.outputs[0], uni.inputs[1]); uni.inputs[2].default_value = (1.0, 0.85, 0.2, 1); uni.inputs[0].default_value = 0.0   # 합침
L(uni.outputs[0], bsdf.inputs["Base Color"])

car = empty("차", loc=(-3.2, 0.3, 0))
box((1.7, 0.75, 0.45), cm, car, (0, 0, 0.48), bevel=0.08); box((0.95, 0.68, 0.38), cm, car, (-0.1, 0, 0.88), bevel=0.08)
wm = mat("바퀴", (0.15, 0.15, 0.18), 0.6); wheels = []
for x in (-0.55, 0.55):
    for y in (-0.38, 0.38):
        w = empty("바퀴축", car, (x, y, 0.22)); cyl(0.2, 0.1, wm, w, rot=(math.pi / 2, 0, 0)); wheels.append(w)
pm = mat("기둥", (0.95, 0.75, 0.55), 0.7, alpha=True); pa = alpha_of(pm)
box((PW, 0.5, 2.8), pm, loc=(PX, -0.6, 1.4), bevel=0.04)
cat = 고양이("고양이", (0, 0, 1.07)); cat[0].parent = car; cat[0].location = (-0.15, 0, 1.07); cat[0].scale = (1.3, 1.3, 1.3)

cams = {"front": camera("front", (0, -4.4, 1.0), (0, 0, 0.9), 30),
        "close": camera("close", (0.2, -3.3, 1.0), (0, 0, 0.8), 28),
        "low": camera("low", (-0.4, -3.2, 0.25), (0, 0, 0.9), 22),
        "side": camera("side", (1.8, -3.6, 1.6), (0, 0, 0.8), 26),
        "wide": camera("wide", (0, -5.4, 1.5), (0, 0, 1.0), 28)}
base = {k: cc[0].location.copy() for k, cc in cams.items()}

for fr in range(1, T.end + 1):
    u = T.u(0, 0.0, 0.85, fr); x = -3.2 + 3.2 * u                       # 첫 줄에 차가 들어와 섬
    car.location.x = x; car.keyframe_insert("location", frame=fr)
    for w in wheels: w.rotation_euler.y = x / 0.2; w.keyframe_insert("rotation_euler", frame=fr)
    see = T.u(2, 0.0, 0.3, fr) * (1 - T.u(6, 0.2, 0.7, fr))
    pa.default_value = 1 - 0.7 * see; pa.keyframe_insert("default_value", frame=fr)
    v = T.u(1, 0.1, 0.4, fr); h = T.u(2, 0.2, 0.5, fr); un = T.u(3, 0.2, 0.6, fr)
    vis.inputs[1].default_value = v; vis.inputs[1].keyframe_insert("default_value", frame=fr)
    hid.inputs[1].default_value = h * (0.8 + 0.2 * math.sin(fr / 2.5)); hid.inputs[1].keyframe_insert("default_value", frame=fr)
    uni.inputs[0].default_value = un; uni.inputs[0].keyframe_insert("default_value", frame=fr)
    cat[1].rotation_euler = (0, -0.3, 0.5 * math.sin(fr / 10)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    cat[0].location.z = 1.07 + 0.05 * abs(math.sin(fr / 3)) * (0 < u < 1) + 0.12 * math.sin(math.pi * un)
    cat[0].keyframe_insert("location", frame=fr)
    고양이_키(cat, fr, False)
    for k, (cc, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        cc.location = p; cc.keyframe_insert("location", frame=fr)
끝(T, cams)
