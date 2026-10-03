"""6-7 보이는 칠 vs 숨은 칠(Zhu 외 2017 그림2) — 상자 뒤 원통. 위에서부터 보이는 부분만 초록으로 칠해지고, 상자가 반투명해지면 숨은 부분이 빨강으로 칠해진다."""
import bpy, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
for o in bpy.data.objects:                      # 하늘 판을 옆으로 넓힘
    if o.data and getattr(o.data, "materials", None) and o.data.materials and o.data.materials[0].name == "하늘": o.scale.x = 140

Z0, Z1 = 0.6, 1.6                                 # 상자가 가리는 높이
# 원통 재질: 높이(z)로 칠 — 초록(보이는 칠) · 빨강(숨은 칠)
cm = mat("원통", (1.0, 0.62, 0.3), 0.6); nt = cm.node_tree; N, L = nt.nodes.new, nt.links.new
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
sep = N("ShaderNodeSeparateXYZ"); L(N("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
def math_(op, a, b):
    m = N("ShaderNodeMath"); m.operation = op
    for i, v in enumerate((a, b)):
        if isinstance(v, (int, float)): m.inputs[i].default_value = v
        else: L(v, m.inputs[i])
    return m
z = sep.outputs[2]
paint = math_("GREATER_THAN", z, 3.0)                       # 칠 높이(위 → 아래로 내려옴) — inputs[1] 에 키
inside = math_("MULTIPLY", math_("GREATER_THAN", z, Z0).outputs[0], math_("LESS_THAN", z, Z1).outputs[0])
amodal = math_("MULTIPLY", inside.outputs[0], 0.0)          # 숨은 칠 세기 — inputs[1] 에 키
vis = math_("MULTIPLY", paint.outputs[0], math_("SUBTRACT", 1.0, inside.outputs[0]).outputs[0])
def mix(fac, a, b):
    m = N("ShaderNodeMixRGB"); L(fac, m.inputs[0])
    for i, v in ((1, a), (2, b)):
        if isinstance(v, tuple): m.inputs[i].default_value = (*v, 1)
        else: L(v, m.inputs[i])
    return m
c1 = mix(vis.outputs[0], (1.0, 0.62, 0.3), (0.3, 0.85, 0.4)); c2 = mix(amodal.outputs[0], c1.outputs[0], (0.95, 0.25, 0.3))
L(c2.outputs[0], bsdf.inputs["Base Color"])
cyl(0.42, 2.0, cm, loc=(0, 0.3, 1.25))
bm_ = mat("상자", (0.3, 0.45, 0.85), 0.6, alpha=True); ba = alpha_of(bm_)
bm_.use_backface_culling = True
if hasattr(bm_, "show_transparent_back"): bm_.show_transparent_back = False
box((1.6, 0.8, Z1 - Z0 + 0.04), bm_, loc=(0, -0.55, (Z0 + Z1) / 2), bevel=0.04)
box((0.3, 0.3, Z0 - 0.02), mat("받침", (0.6, 0.45, 0.3), 0.8), loc=(0, -0.55, (Z0 - 0.02) / 2))
# 붓: 칠하는 높이를 따라 내려오는 막대
brush = cyl(0.06, 1.2, mat("붓", (0.95, 0.95, 0.9), 0.5), loc=(0, -0.2, 3.0), rot=(0, math.pi / 2, 0))

cat = 고양이("고양이", (-1.2, -1.3, 0)); cat[0].scale = (1.25, 1.25, 1.25)
cams = {"front": camera("front", (0, -4.2, 1.3), (0, 0, 1.3), 30),
        "close": camera("close", (0.2, -3.2, 1.4), (0, 0, 1.3), 28),
        "low": camera("low", (-0.4, -3.2, 0.3), (0, 0, 1.2), 22),
        "side": camera("side", (1.6, -3.6, 1.6), (0, 0, 1.2), 26),
        "wide": camera("wide", (0, -5.2, 1.7), (0, 0, 1.3), 28)}
base = {k: c[0].location.copy() for k, c in cams.items()}

for fr in range(1, T.end + 1):
    lv = 2.4 - 2.3 * T.u(1, 0.05, 0.8, fr)                   # 보이는 칠: 위에서 아래로
    paint.inputs[1].default_value = lv; paint.inputs[1].keyframe_insert("default_value", frame=fr)
    see = T.u(3, 0.05, 0.4, fr); ba.default_value = 1 - 0.7 * see; ba.keyframe_insert("default_value", frame=fr)
    am = T.u(3, 0.4, 0.9, fr) * (0.8 + 0.2 * math.sin(fr / 2.5)); amodal.inputs[1].default_value = am
    amodal.inputs[1].keyframe_insert("default_value", frame=fr)
    bz = lv if fr < T.lines[3][0] else Z1 - (Z1 - Z0) * T.u(3, 0.4, 0.9, fr)
    show = (0 < T.u(1, 0.05, 0.8, fr) < 1) or (0 < T.u(3, 0.4, 0.9, fr) < 1)
    brush.location = (0.25 * math.sin(fr / 2), -1.05, bz); brush.hide_render = not show
    brush.keyframe_insert("location", frame=fr); brush.keyframe_insert("hide_render", frame=fr)
    x = -1.5 + 3.0 * (0.5 - 0.5 * math.cos(fr / 45))
    cat[0].location.x = x; cat[0].rotation_euler.z = 0 if math.sin(fr / 45) >= 0 else math.pi
    cat[0].keyframe_insert("location", frame=fr); cat[0].keyframe_insert("rotation_euler", frame=fr)
    cat[1].rotation_euler = (0, -0.5, 0.3 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, abs(math.sin(fr / 45)) > 0.08)
    for k, (c, _) in cams.items():
        p = base[k].copy(); p.x += 0.2 * math.sin(fr / 37 + len(k)); p.y += 0.25 * math.sin(fr / 47)
        c.location = p; c.keyframe_insert("location", frame=fr)
끝(T, cams)
