"""34 AI가 못 푼 부품 · Claude가 직접 짰다 — 블렌더 뷰포트 무대(HS-1 과 같은 어두운 격자) 위에 진짜 부품 메시.
사람 부품 = 노랑 · Claude 코드 결과 = 하늘색 · O = 초록 고리 · X = 빨강 막대 두 개. 다섯 곳(줄 · 모니터 · 공막대 · 엉덩이 · 점수)을 카메라가 옮겨 다닌다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *
HERE = "G:/art2real/원화3d/과정/영상05/장난감/34_클로드코드"
FONT = bpy.data.fonts.load("C:/Windows/Fonts/malgunbd.ttf") if False else None

T = 시작(); 무대(ARGS[1], trees=False)
FONT = bpy.data.fonts.load("C:/Windows/Fonts/malgunbd.ttf")
for o in bpy.data.objects:   # 하늘 판 숨김 · 뷰포트 회색 바탕
    if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "하늘": o.hide_render = True
for n in bpy.context.scene.world.node_tree.nodes:
    if n.type == "BACKGROUND" and n.inputs[1].default_value > 1: n.inputs[0].default_value = (0.11, 0.11, 0.12, 1); n.inputs[1].default_value = 1.0
gm = bpy.data.materials["땅"]; nt = gm.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
def line(ax):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = "PINGPONG"; m.inputs[1].default_value = 0.25; nt.links.new(sep.outputs[ax], m.inputs[0])
    c = nt.nodes.new("ShaderNodeMath"); c.operation = "LESS_THAN"; c.inputs[1].default_value = 0.008; nt.links.new(m.outputs[0], c.inputs[0]); return c
a, b = line(0), line(1); mxn = nt.nodes.new("ShaderNodeMath"); mxn.operation = "MAXIMUM"; nt.links.new(a.outputs[0], mxn.inputs[0]); nt.links.new(b.outputs[0], mxn.inputs[1])
mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0.08, 0.08, 0.09, 1); mix.inputs[2].default_value = (0.24, 0.24, 0.26, 1)
nt.links.new(mxn.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.9

YEL, SKY = mat("사람", (0.98, 0.84, 0.32), 0.45), mat("클로드", (0.45, 0.72, 0.98), 0.45)
GRN, RED, DARK = mat("오", (0.15, 0.85, 0.35), 0.4, emit=1.5), mat("엑스", (0.95, 0.15, 0.15), 0.4, emit=1.5), mat("받침", (0.26, 0.26, 0.29), 0.7)
WHITE = mat("글", (0.95, 0.95, 0.95), 0.5, emit=1.0)

def stl(name, m, loc, s):
    try: bpy.ops.wm.stl_import(filepath=f"{HERE}/{name}.stl")
    except Exception: bpy.ops.import_mesh.stl(filepath=f"{HERE}/{name}.stl")
    o = bpy.context.object; o.data.materials.append(m); o.scale = (s,) * 3; o.location = loc
    bpy.ops.object.shade_flat(); return o
def text(s, loc, size, m, rot=(math.pi / 2, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot); t = bpy.context.object
    t.data.body = s; t.data.size = size; t.data.extrude = 0.01; t.data.font = FONT; t.data.align_x = "CENTER"; t.data.materials.append(m); return t
def ring(loc, r, m):
    bpy.ops.mesh.primitive_torus_add(location=loc, rotation=(math.pi / 2, 0, 0), major_radius=r, minor_radius=r * 0.13); o = bpy.context.object; o.data.materials.append(m); return o
def cross(loc, r, m):
    p = empty("엑스", loc=loc)
    for ang in (45, -45):
        o = box((r * 2, r * 0.26, r * 0.26), m, parent=p); o.rotation_euler = (0, math.radians(ang), 0)
    return p

# A 줄(x=-9): 사람 부품 10 개 + X
AX = -9.0; box((4.2, 0.9, 0.3), DARK, loc=(AX, -0.5, 0.15), bevel=0.03); box((4.2, 0.9, 0.9), DARK, loc=(AX, 0.6, 0.45), bevel=0.03)
POS = [(AX - 1.6 + (i % 5) * 0.8, -0.5 if i < 5 else 0.6, 0.3 if i < 5 else 0.9) for i in range(10)]
row = [stl(f"g{i}", YEL, POS[i], 0.62) for i in range(10)]
xs = [cross((x, y - 0.45, z + 0.75), 0.17, RED) for x, y, z in POS]
# B 모니터(x=0, y=7): 코드 화면 + 만들어지는 허리
BX, BY = 0.0, 7.0
box((2.4, 0.12, 1.6), mat("모니터", (0.06, 0.06, 0.07), 0.6), loc=(BX - 0.8, BY + 0.3, 1.25), bevel=0.04); cyl(0.06, 0.6, DARK, loc=(BX - 0.8, BY + 0.35, 0.3))
code = open("G:/art2real/트레일/trail10_cadrille/runs/교사시험/07.py", encoding="utf-8").read().split("\n")[:9]
lines_ = [text(l[:22], (BX - 1.85, BY + 0.22, 1.85 - i * 0.2), 0.11, mat(f"코드{i}", (0.6, 0.9, 1.0), 0.5, emit=1.2)) for i, l in enumerate(code)]
for t in lines_: t.data.align_x = "LEFT"
text("> Claude Code", (BX - 0.8, BY + 0.22, 2.2), 0.13, mat("프롬", (1.0, 0.8, 0.35), 0.5, emit=1.4))
box((1.2, 1.2, 0.3), DARK, loc=(BX + 1.3, BY, 0.15), bevel=0.03); waist = stl("c7", SKY, (BX + 1.3, BY, 0.3), 0.9)
# C 공막대(x=0): 왼쪽 사람 · 오른쪽 Claude
CX = 0.0
for dx in (-0.85, 0.85): box((1.2, 1.2, 0.5), DARK, loc=(CX + dx, 0, 0.25), bevel=0.03)
g0, c0 = stl("g0", YEL, (CX - 0.85, 0, 0.5), 0.95), stl("c0", SKY, (CX + 0.85, 0, 0.5), 0.95)
text("사람", (CX - 0.85, -0.62, 0.12), 0.16, WHITE); text("Claude", (CX + 0.85, -0.62, 0.12), 0.16, WHITE)
okC = ring((CX + 0.85, -0.2, 1.35), 0.2, GRN)
GL0 = mat("클로드0", (0.45, 0.72, 0.98), 0.45); c0.data.materials[0] = GL0; GLP = next(n for n in GL0.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); GLP.inputs["Emission Color"].default_value = (0.2, 1.0, 0.4, 1)
# D 엉덩이(x=8)
DX = 8.0
for dx in (-0.85, 0.85): box((1.2, 1.2, 0.5), DARK, loc=(DX + dx, 0, 0.25), bevel=0.03)
g2, c2 = stl("g2", YEL, (DX - 0.85, 0, 0.5), 0.95), stl("c2", SKY, (DX + 0.85, 0, 0.5), 0.95)
text("사람", (DX - 0.85, -0.62, 0.12), 0.16, WHITE); text("Claude", (DX + 0.85, -0.62, 0.12), 0.16, WHITE)
hiG, hiR = ring((DX - 0.85, -0.55, 0.75), 0.17, GRN), ring((DX + 0.85, -0.55, 0.75), 0.17, RED); xD = cross((DX + 0.85, -0.3, 1.9), 0.3, RED)
GHM = mat("빈자리", (1.0, 0.25, 0.2), 0.3, emit=2.0, alpha=True); ghost = ball(0.095, GHM, loc=(DX + 0.85, -0.55, 0.75)); GHA = alpha_of(GHM)
for o in (okC, xD, hiG, hiR):
    o.hide_render = True
    for ch in o.children: ch.hide_render = True   # 빈 객체만 숨기면 막대가 남아 화면 위에 빨간 마름모로 떴다
# E 점수(x=16): 블록 10 개 두 줄
EX = 16.0
for k, (nm, ok, y) in enumerate((("채점기", 9, 1.6), ("내 눈", 7, 0.6))):
    text(f"{nm}  {ok}/10", (EX, -0.2, y + 0.3), 0.3, GRN if k == 0 else RED)
    for i in range(10): box((0.3, 0.3, 0.3), GRN if i < ok else RED, loc=(EX - 1.62 + i * 0.36, 0, y), bevel=0.03)

cams = {
    "hook": camera("hook", (AX, -5.2, 2.0), (AX, 0, 0.9), 26), "hookclose": camera("hookclose", (AX - 2.5, -2.4, 1.2), (AX - 2.0, 0, 0.7), 35),
    "term": camera("term", (BX - 1.0, BY - 3.6, 1.5), (BX - 1.0, BY, 1.4), 30), "termclose": camera("termclose", (BX + 1.5, BY - 2.0, 1.0), (BX + 1.3, BY, 0.7), 40),
    "pair": camera("pair", (CX, -4.2, 1.3), (CX, 0, 0.95), 32), "pairorbit": camera("pairorbit", (CX + 2.5, -2.6, 1.6), (CX + 0.85, 0, 0.9), 38),
    "hip": camera("hip", (DX, -4.2, 1.3), (DX, 0, 0.95), 32), "hipclose": camera("hipclose", (DX + 0.5, -2.6, 1.0), (DX + 0.85, 0, 0.75), 40),
    "score": camera("score", (EX, -5.0, 1.3), (EX, 0, 1.2), 26), "scoreclose": camera("scoreclose", (EX + 0.8, -2.8, 0.75), (EX + 0.8, 0, 0.7), 32),
}
RINGS = [okC, hiG, hiR, xD] + xs
CUTCAM = []; f0 = 1
for c_ in T.cuts: CUTCAM += [(f0, f0 + c_["n"], cams[c_["cam"]][0])]; f0 += c_["n"]
for o in RINGS: o.rotation_mode = "QUATERNION"
for fr in range(1, T.end + 1):
    cam_ = next(c for a_, b_, c in CUTCAM if a_ <= fr < b_) if fr < f0 else CUTCAM[-1][2]
    for o in RINGS:
        ax = Vector((0, 0, 1)) if o.type == 'MESH' else Vector((0, -1, 0))   # 고리(토러스) = Z 축 · X 표시(빈 객체) = -Y 쪽 면
        o.rotation_quaternion = ax.rotation_difference(cam_.location - o.location)
        o.keyframe_insert("rotation_quaternion", frame=fr)
    GLP.inputs["Emission Strength"].default_value = 1.6 * 깜빡(T, 2, 0.45, fr); GLP.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    GHA.default_value = 0.85 * 깜빡(T, 4, 0.45, fr); GHA.keyframe_insert("default_value", frame=fr)
    for o in (g0, c0, g2, c2, waist): o.rotation_euler = (0, 0, fr / 40); o.keyframe_insert("rotation_euler", frame=fr)
    for i, x in enumerate(xs): s = max(T.u(0, 0.1 + i * 0.05, 0.15 + i * 0.05, fr), 0.001); x.scale = (s,) * 3; x.keyframe_insert("scale", frame=fr)
    s = max(T.u(2, 0.55, 0.65, fr), 0.001); okC.scale = (s,) * 3; okC.keyframe_insert("scale", frame=fr)
    s = max(T.u(4, 0.5, 0.6, fr), 0.001); xD.scale = (s,) * 3; xD.keyframe_insert("scale", frame=fr)
    s = max(T.u(1, 0.2, 0.9, fr), 0.001); waist.scale = (0.9, 0.9, 0.9 * s); waist.keyframe_insert("scale", frame=fr)   # 코드 줄이 늘 때 부품이 아래부터 자람
    for i, t in enumerate(lines_): t.hide_render = T.u(1, i * 0.08, i * 0.08 + 0.01, fr) < 0.5; t.keyframe_insert("hide_render", frame=fr)
    c, _ = cams["pairorbit"]; c.location = Vector((CX + 0.85 + 2.6 * math.sin(fr / 30), -2.6 * math.cos(fr / 30), 1.6)); c.keyframe_insert("location", frame=fr)
    c, _ = cams["hook"]; c.location.x = AX - 0.6 + 1.2 * T.u(0, 0, 1, fr); c.keyframe_insert("location", frame=fr)
    c, _ = cams["hipclose"]; c.location.y = -2.6 + 0.5 * T.u(4, 0.4, 1, fr); c.keyframe_insert("location", frame=fr)
from bpy_extras.object_utils import world_to_camera_view
AN = {"줄": (AX, -0.5, 1.0), "줄부품": POS[3], "모니터": (BX - 0.8, BY + 0.2, 2.0), "허리": (BX + 1.3, BY, 1.0), "공막대사람": (CX - 0.85, 0, 0.95), "공막대클로드": (CX + 0.85, 0, 0.95),
      "엉덩이사람": (DX - 0.85, -0.55, 0.75), "엉덩이클로드": (DX + 0.85, -0.55, 0.75), "채점기": (EX, 0, 1.9), "내눈": (EX, 0, 0.9)}
sc = bpy.context.scene; out_ = []; f_ = 1
for k, c_ in enumerate(T.cuts):
    fr = f_ + c_["n"] * 3 // 4; sc.frame_set(fr); cam = cams[c_["cam"]][0]
    line = next((i for i, (a_, b_) in enumerate(T.lines) if a_ <= fr < b_), len(T.lines) - 1)
    pts = {}
    for nm, p in AN.items():
        co = world_to_camera_view(sc, cam, Vector(p)); pts[nm] = [round(co.x, 4), round(1 - co.y, 4), co.z > 0 and 0 <= co.x <= 1 and 0 <= co.y <= 1]
    out_.append({"컷": k, "카메라": c_["cam"], "줄": line, "점": pts}); f_ += c_["n"]
import json as _j, os as _o; _o.makedirs(ARGS[2], exist_ok=True); _o.makedirs(ARGS[2], exist_ok=True); _j.dump(out_, open(ARGS[2] + "/앵커.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
앵커프레임(T, cams, {"클로드0": (CX + 0.85, 0, 1.3), "빈자리": (DX + 0.85, -0.55, 0.95), "사람공": (DX - 0.85, -0.55, 0.75),
                    "모니터": (BX - 0.8, BY + 0.2, 2.25), "허리": (BX + 1.3, BY, 1.1), "줄": (AX, -0.5, 1.2)}, ARGS[2])
끝(T, cams)
