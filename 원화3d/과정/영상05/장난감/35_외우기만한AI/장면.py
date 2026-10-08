"""35 외우기만 한 AI — 가로 긴 영상. 34 편과 같은 어두운 격자 무대 위 여러 곳을 카메라가 옮겨 다닌다.
책상(배운 부품) · 시험대 · 칠판(코드 글자 · 숫자 40 %) · 창고(글자 조각 15 만) · 순서(구멍 A·B) · 조각 선반(10 칸) · 그림자 극장(컨투어) · 크기(15 억 대 461 만) · 눈(얼림) · 모니터(한 스텝) · 결과판"""
import bpy, math, os
from mathutils import Vector
from 장난감_공용 import *
HERE = "G:/art2real/원화3d/과정/영상05/장난감/35_외우기만한AI"; P34 = "G:/art2real/원화3d/과정/영상05/장난감/34_클로드코드"
STEP_IMG = "G:/art2real/트레일/trail10_cadrille/runs/조각0/한스텝.png"
RES_IMG = next(p for p in ["G:/art2real/트레일/trail10_cadrille/runs/조각0/시험그림.png", "G:/art2real/트레일/trail10_cadrille/runs/그림/구조_인코더시험.png"] if os.path.exists(p))
RES2_IMG = "G:/art2real/트레일/trail10_cadrille/runs/조각1/시험그림.png"
CODE = "G:/art2real/트레일/trail10_cadrille/runs/교사1/data/train/0000.py"

T = 시작(); 무대(ARGS[1], trees=False)
sc = bpy.context.scene
try: sc.eevee.use_soft_shadows = True
except Exception: pass
FONT = bpy.data.fonts.load("C:/Windows/Fonts/malgunbd.ttf"); MONO = bpy.data.fonts.load("C:/Windows/Fonts/consola.ttf")
for o in bpy.data.objects:
    if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "하늘": o.hide_render = True
    if o.type == "LIGHT": o.data.use_shadow = False; o.data.energy = 1.6   # 전체 빛은 그림자 없이 — 극장 벽에 엉뚱한 그림자가 안 생기게
for n in sc.world.node_tree.nodes:
    if n.type == "BACKGROUND" and n.inputs[1].default_value > 1: n.inputs[0].default_value = (0.11, 0.11, 0.12, 1); n.inputs[1].default_value = 1.0
gm = bpy.data.materials["땅"]; nt = gm.node_tree; Pn = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
def gline(ax):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = "PINGPONG"; m.inputs[1].default_value = 0.25; nt.links.new(sep.outputs[ax], m.inputs[0])
    c = nt.nodes.new("ShaderNodeMath"); c.operation = "LESS_THAN"; c.inputs[1].default_value = 0.008; nt.links.new(m.outputs[0], c.inputs[0]); return c
a_, b_ = gline(0), gline(1); mxn = nt.nodes.new("ShaderNodeMath"); mxn.operation = "MAXIMUM"; nt.links.new(a_.outputs[0], mxn.inputs[0]); nt.links.new(b_.outputs[0], mxn.inputs[1])
mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0.08, 0.08, 0.09, 1); mix.inputs[2].default_value = (0.24, 0.24, 0.26, 1)
nt.links.new(mxn.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[0], Pn.inputs["Base Color"]); Pn.inputs["Roughness"].default_value = 0.9

YEL, SKY = mat("사람", (0.98, 0.84, 0.32), 0.45), mat("하늘색", (0.45, 0.72, 0.98), 0.45)
GRN, RED, DARK = mat("초록", (0.15, 0.85, 0.35), 0.4, emit=1.5), mat("빨강", (0.95, 0.15, 0.15), 0.4, emit=1.5), mat("받침", (0.26, 0.26, 0.29), 0.7)
WHITE = mat("글", (0.95, 0.95, 0.95), 0.5, emit=1.0)
PINK, WALL = mat("분홍", (0.95, 0.55, 0.65), 0.6), mat("벽", (0.88, 0.88, 0.86), 0.9)
HOLE = mat("구멍", (1.0, 0.3, 0.25), 0.3, emit=0.8, alpha=True); alpha_of(HOLE).default_value = 0.55

def stl(path, m, loc, s, rot=(0, 0, 0)):
    try: bpy.ops.wm.stl_import(filepath=path)
    except Exception: bpy.ops.import_mesh.stl(filepath=path)
    o = bpy.context.object; o.data.materials.append(m); o.scale = (s,) * 3; o.location = loc; o.rotation_euler = rot
    bpy.ops.object.shade_flat(); return o
def text(s, loc, size, m, rot=(math.pi / 2, 0, 0), font=None, align="CENTER"):
    bpy.ops.object.text_add(location=loc, rotation=rot); t = bpy.context.object
    t.data.body = s; t.data.size = size; t.data.extrude = 0.008; t.data.font = font or FONT; t.data.align_x = align; t.data.materials.append(m); return t
def cross(loc, r, m):
    p = empty("엑스", loc=loc)
    for ang in (45, -45):
        o = box((r * 2, r * 0.26, r * 0.26), m, parent=p); o.rotation_euler = (0, math.radians(ang), 0)
    return p
def imgplane(path, loc, w):
    im = bpy.data.images.load(path); h = w * im.size[1] / im.size[0]
    if h > 3.2: w, h = w * 3.2 / h, 3.2   # 세로로 긴 결과 그림은 높이에 맞춤(4.4 m 폭이면 7 m 가 되어 일부만 보였다)
    m = bpy.data.materials.new("화면" + os.path.basename(path)); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
    tx = t.nodes.new("ShaderNodeTexImage"); tx.image = im; em = t.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 0.85
    o_ = t.nodes.new("ShaderNodeOutputMaterial"); t.links.new(tx.outputs[0], em.inputs[0]); t.links.new(em.outputs[0], o_.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0)); o = put(bpy.context.object, m, loc=loc); o.scale = (w, h, 1)
    box((w + 0.16, 0.1, h + 0.16), mat("테", (0.06, 0.06, 0.07), 0.6), loc=(loc[0], loc[1] + 0.07, loc[2]), bevel=0.03); return o, h
def hide(o, v):
    o.hide_render = v
    for c in o.children: c.hide_render = v

# ── A 책상(x=-24): AI 학생 + 배운 부품 10 + 점수 ──
AX = -24.0
ROB = mat("로봇", (0.55, 0.78, 0.95), 0.5); EYE = mat("로봇눈", (0.2, 1.0, 0.9), 0.3, emit=3.0)
rob = empty("로봇", loc=(AX, 1.4, 0)); cyl(0.38, 0.9, ROB, rob, (0, 0, 0.45), bevel=0.08)
head = empty("머리", rob, (0, 0, 1.15)); box((0.7, 0.55, 0.5), ROB, head, bevel=0.08)
for s in (-1, 1): ball(0.07, EYE, head, (s * 0.16, -0.28, 0.03))
cyl(0.015, 0.25, DARK, head, (0, 0, 0.37)); ball(0.05, RED, head, (0, 0, 0.5))
box((3.6, 1.0, 0.75), DARK, loc=(AX, 0, 0.375), bevel=0.04)
learned = [stl(f"{P34}/g{i}.stl", YEL, (AX - 1.5 + (i % 5) * 0.75, -0.2 if i < 5 else 0.25, 0.75), 0.5) for i in range(10)]
text("배운 부품  67%", (AX, 0.9, 2.15), 0.32, GRN)
# 시험대(x=-15): 처음 보는 부품 3 + 점수
TX, TY = AX + 9.0, 0.0
for k in range(3): box((0.9, 0.9, 0.5), DARK, loc=(TX - 1.2 + k * 1.2, TY, 0.25), bevel=0.03)
tests = [stl(f"{HERE}/s{k}.stl", SKY, (TX - 1.2 + k * 1.2, TY, 0.85), 0.006) for k in range(3)]
text("처음 보는 부품", (TX, TY + 0.5, 1.75), 0.26, WHITE)
text("가르치기 전 34%  →  후 27%", (TX, TY + 0.5, 1.4), 0.24, RED)

# ── B 칠판(x=-6): 진짜 cadrille 학습 코드 · 숫자만 노랗게 ──
BX = -6.0
box((5.2, 0.12, 2.9), mat("칠판", (0.08, 0.22, 0.16), 0.8), loc=(BX, 1.0, 1.75), bevel=0.04)
src0 = open(CODE, encoding="utf-8").read().replace("\n", ""); src = src0[src0.index("r=w0"):]; W_ = 50; rows_ = [src[i:i + W_] for i in range(0, W_ * 11, W_)]
NUMM = mat("숫자", (1.0, 0.55, 0.1), 0.4, emit=1.6); NUMP = next(n for n in NUMM.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
code_lines, num_lines = [], []
for i, r in enumerate(rows_):
    y0 = 2.95 - i * 0.22
    cr = "".join(" " if (c.isdigit() or c == "-") else c for c in r)   # 글자 판 · 숫자 판을 나눠 겹침 없이
    code_lines.append(text(cr, (BX - 2.45, 0.93, y0), 0.17, mat(f"코드{i}", (0.7, 0.82, 0.76), 0.5, emit=0.45), font=MONO, align="LEFT"))
    nr = "".join(c if (c.isdigit() or c == "-") else " " for c in r)   # 고정폭 글꼴이라 같은 자리에 숫자만 겹쳐 쓴다
    num_lines.append(text(nr, (BX - 2.45, 0.92, y0), 0.17, NUMM, font=MONO, align="LEFT"))
# ── C 창고(x=6): 작은 블록 벽 = 글자 조각 15 만 · 구석 한 줌만 빛남 ──
CX = 6.0
blk = box((0.045, 0.045, 0.045), mat("조각", (0.55, 0.57, 0.62), 0.7), loc=(CX - 3.6, 1.5, 0.06))
for ax, n, off in ((0, 140, (1.15, 0, 0)), (2, 55, (0, 0, 1.15)), (1, 4, (0, 1.6, 0))):
    md = blk.modifiers.new("arr%d" % ax, "ARRAY"); md.count = n; md.relative_offset_displace = off
HAND = mat("한줌", (1.0, 0.6, 0.15), 0.4, emit=0.5); HP = next(n for n in HAND.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
hand = box((0.045, 0.045, 0.045), HAND, loc=(CX + 3.2, 1.45, 0.06))
for ax, n, off in ((0, 7, (1.15, 0, 0)), (2, 4, (0, 0, 1.15))):
    md = hand.modifiers.new("arr%d" % ax, "ARRAY"); md.count = n; md.relative_offset_displace = off
# ── O 순서(x=18): 같은 판 둘 · 구멍 A·B 순서만 다름 ──
OX = 18.0; PL = mat("판", (0.98, 0.84, 0.32), 0.5)
holes = {}
for side, dx in (("L", -1.4), ("R", 1.4)):
    box((2.0, 1.2, 0.18), PL, loc=(OX + dx, 0, 0.6), bevel=0.03); box((0.3, 0.3, 0.5), DARK, loc=(OX + dx, 0, 0.25))
    for nm, hx in (("A", -0.5), ("B", 0.5)):
        holes[side + nm] = cyl(0.17, 0.02, mat("뚫림" + side + nm, (0.03, 0.03, 0.03), 0.9), loc=(OX + dx + hx, 0, 0.7))
        text(nm, (OX + dx + hx, -0.65, 0.78), 0.2, WHITE)
text("A 먼저 → B", (OX - 1.4, 0.3, 1.35), 0.22, WHITE); text("B 먼저 → A", (OX + 1.4, 0.3, 1.35), 0.22, WHITE)
eq = text("=", (OX, 0, 0.85), 0.5, GRN); xO = cross((OX + 1.4, -0.4, 1.0), 0.45, RED)
drills = {s: empty("드릴" + s, loc=(OX + dx, 0, 2.2)) for s, dx in (("L", -1.4), ("R", 1.4))}
for d in drills.values(): cyl(0.05, 0.9, mat("드릴날", (0.8, 0.8, 0.85), 0.3), d, (0, 0, 0)); cyl(0.14, 0.4, RED, d, (0, 0, 0.6), bevel=0.03)
# ── D 조각 선반(x=30): 10 칸 ──
DX = 30.0; NAMES = ["상자", "원통z", "원통x", "원통y", "공", "구멍z", "구멍x", "구멍y", "사각구멍", "빈칸"]
ROTS = {"z": (0, 0, 0), "x": (0, math.pi / 2, 0), "y": (math.pi / 2, 0, 0)}
for k, nm in enumerate(NAMES):
    x = DX - 2.4 + (k % 5) * 1.2; z = 1.55 if k < 5 else 0.45; box((1.1, 0.8, 0.06), DARK, loc=(x, 0, z - 0.33))
    text(nm, (x, -0.42, z - 0.47), 0.15, WHITE)
    if nm == "상자": box((0.5, 0.4, 0.4), YEL, loc=(x, 0, z - 0.1), bevel=0.03)
    elif nm == "공": ball(0.25, YEL, loc=(x, 0, z - 0.05))
    elif nm.startswith("원통"): cyl(0.2, 0.55, YEL, loc=(x, 0, z - 0.05), rot=ROTS[nm[-1]])
    elif nm.startswith("구멍"): cyl(0.13, 0.6, HOLE, loc=(x, 0, z - 0.05), rot=ROTS[nm[-1]])
    elif nm == "사각구멍": box((0.4, 0.4, 0.4), HOLE, loc=(x, 0, z - 0.1))
box((6.2, 0.9, 0.08), DARK, loc=(DX, 0.05, 2.05)); box((0.08, 0.9, 2.1), DARK, loc=(DX - 3.06, 0.05, 1.05)); box((0.08, 0.9, 2.1), DARK, loc=(DX + 3.06, 0.05, 1.05))
# ── E 그림자 극장(x=42): 부품 하나 · 세 방향 빛 · 벽 둘 + 바닥판 ──
EX = 42.0; EH = 1.3
box((5.0, 0.05, 3.2), WALL, loc=(EX, 2.5, 1.6)); box((0.05, 5.0, 3.2), WALL, loc=(EX - 2.5, 0, 1.6)); box((5.0, 5.0, 0.04), WALL, loc=(EX, 0, 0.02))
cyl(0.02, EH - 0.4, DARK, loc=(EX, 0, (EH - 0.4) / 2))
gt = stl(f"{HERE}/s0.stl", YEL, (EX, 0, EH), 0.016)
GUESS = mat("추측", (0.45, 0.72, 0.98), 0.4, alpha=True); alpha_of(GUESS).default_value = 0.8
guess = empty("추측", loc=(EX, 0, EH)); ball(0.42, GUESS, guess, (0, 0, 0), (1.0, 0.85, 0.35)); box((0.5, 0.9, 0.25), GUESS, guess, (0.3, 0.1, 0.05), bevel=0.05)
suns = []
for rot in ((math.pi / 2, 0, 0), (0, math.pi / 2, 0), (0, 0, 0)):
    bpy.ops.object.light_add(type="SUN", rotation=rot); s = bpy.context.object; s.data.energy = 3.2; s.data.angle = math.radians(0.5); suns.append(s)
# ── F 크기(x=54) · 눈(x=63) ──
FX = 54.0
box((3.0, 3.0, 3.0), PINK, loc=(FX - 1.2, 1.0, 1.5), bevel=0.1); text("15억", (FX - 1.2, -0.52, 1.5), 0.6, WHITE)
box((0.45, 0.45, 0.45), mat("작은", (0.15, 0.85, 0.35), 0.5), loc=(FX + 1.5, 0, 0.225), bevel=0.03); text("461만", (FX + 2.35, -0.3, 0.15), 0.22, GRN)
EYX, EYY = FX + 9.0, 0.0
eye = empty("눈", loc=(EYX - 1.0, EYY, 1.2)); ball(0.55, mat("흰자", (0.97, 0.97, 0.97), 0.3), eye)
cyl(0.26, 0.08, mat("홍채", (0.2, 0.45, 0.85), 0.3), eye, (0, -0.52, 0), (math.pi / 2, 0, 0)); cyl(0.12, 0.1, mat("동공", (0.02, 0.02, 0.02), 0.3), eye, (0, -0.56, 0), (math.pi / 2, 0, 0))
ICE = mat("얼음", (0.7, 0.9, 1.0), 0.1, emit=0.15, alpha=True); alpha_of(ICE).default_value = 0.35; box((1.5, 1.5, 1.5), ICE, loc=(EYX - 1.0, EYY, 1.2), bevel=0.06)
text("얼림", (EYX - 1.0, EYY - 0.8, 2.2), 0.28, mat("얼음글", (0.6, 0.85, 1.0), 0.4, emit=1.2))
arm = empty("손", loc=(EYX + 1.3, EYY, 0.0)); cyl(0.12, 1.0, ROB, arm, (0, 0, 0.5)); cyl(0.09, 0.8, ROB, arm, (-0.3, 0, 1.1), (0, math.radians(-40), 0))
claw = empty("집게", arm, (-0.58, 0, 1.4))
for s in (-1, 1): box((0.06, 0.06, 0.3), ROB, claw, (0, s * 0.09, -0.12))
text("새로 가르침", (EYX + 1.3, EYY - 0.45, 2.2), 0.24, GRN)
# ── G 모니터(x=75) · H 결과(x=87) ──
GX, HX, H2X = 75.0, 87.0, 99.0
mon, mh = imgplane(STEP_IMG, (GX, 0.6, 1.9), 4.4); res, rh = imgplane(RES_IMG, (HX, 0.6, 1.9), 4.4)
res2, rh2 = imgplane(RES2_IMG, (H2X, 0.6, 1.9), 4.4)
for x in (GX, HX, H2X): cyl(0.08, 0.8, DARK, loc=(x, 0.7, 0.4))

cams = {
    "desk": camera("desk", (AX - 0.4, -5.2, 2.0), (AX, 0.5, 1.1), 30), "deskclose": camera("deskclose", (AX - 1.8, -2.4, 1.5), (AX - 0.6, 0.2, 1.0), 38),
    "test": camera("test", (TX, -4.6, 1.6), (TX, 0.2, 1.1), 32), "testclose": camera("testclose", (TX + 1.6, -3.2, 1.6), (TX + 0.4, 0, 1.2), 40),
    "board": camera("board", (BX, -4.6, 1.8), (BX, 1.0, 1.75), 32), "boardclose": camera("boardclose", (BX - 1.2, -2.2, 2.4), (BX - 1.2, 1.0, 2.4), 36),
    "ware": camera("ware", (CX, -6.5, 1.6), (CX, 1.5, 1.6), 30), "wareclose": camera("wareclose", (CX + 2.3, -1.2, 0.5), (CX + 3.4, 1.5, 0.2), 38),
    "ord": camera("ord", (OX, -4.6, 2.4), (OX, 0, 0.9), 32), "ordclose": camera("ordclose", (OX + 2.2, -3.2, 2.0), (OX + 1.2, 0, 0.95), 36),
    "shelf": camera("shelf", (DX, -5.6, 1.4), (DX, 0, 1.05), 32), "shelfclose": camera("shelfclose", (DX + 0.6, -3.4, 1.2), (DX + 0.6, 0, 0.9), 36),
    "theater": camera("theater", (EX + 3.4, -5.0, 2.6), (EX - 0.6, 0.6, 1.3), 28), "theaterclose": camera("theaterclose", (EX + 1.2, -2.4, 1.6), (EX - 0.8, 1.6, 1.3), 30),
    "size": camera("size", (FX, -7.5, 1.6), (FX, 0, 1.4), 30), "sizeclose": camera("sizeclose", (FX + 1.5, -2.4, 0.6), (FX + 1.5, 0, 0.42), 40),
    "eye": camera("eye", (EYX, -5.2, 1.5), (EYX, 0, 1.2), 32), "eyeclose": camera("eyeclose", (EYX - 1.0, -2.3, 1.3), (EYX - 1.0, 0, 1.2), 38),
    "mon": camera("mon", (GX, -4.4, 1.9), (GX, 0.6, 1.9), 34), "monclose": camera("monclose", (GX + 0.6, -2.4, 1.9), (GX + 0.6, 0.6, 1.9), 40),
    "result": camera("result", (HX, -4.4, 1.9), (HX, 0.6, 1.9), 34), "resultclose": camera("resultclose", (HX - 0.6, -2.4, 1.9), (HX - 0.6, 0.6, 1.9), 40),
    "result2": camera("result2", (H2X, -4.4, 1.9), (H2X, 0.6, 1.9), 34), "result2close": camera("result2close", (H2X + 0.6, -2.4, 2.2), (H2X + 0.6, 0.6, 2.2), 40),
}
CUTCAM = []; f0 = 1
for c_ in T.cuts: CUTCAM += [(f0, f0 + c_["n"], cams[c_["cam"]][0])]; f0 += c_["n"]
xO.rotation_mode = "QUATERNION"
L12, L18 = T.lines[12], T.lines[18]
for fr in range(1, T.end + 1):
    t = fr / FPS
    head.rotation_euler.z = 0.15 * math.sin(t * 1.3); head.keyframe_insert("rotation_euler", frame=fr)
    for o in tests + [gt]: o.rotation_euler.z = t * 0.35; o.keyframe_insert("rotation_euler", frame=fr)
    guess.rotation_euler.z = t * 0.35; guess.keyframe_insert("rotation_euler", frame=fr)
    NUMP.inputs["Emission Strength"].default_value = 1.0 + 3.0 * max(깜빡(T, 6, 0.25, fr), 깜빡(T, 5, 0.3, fr)); NUMP.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    HP.inputs["Emission Strength"].default_value = 0.5 + 3.5 * 깜빡(T, 9, 0.45, fr); HP.inputs["Emission Strength"].keyframe_insert("default_value", frame=fr)
    for i, ln in enumerate(code_lines):   # 4 줄 동안 한 줄씩 써짐
        v = fr < T.lines[5][0] and T.u(4, i * 0.07, i * 0.07 + 0.01, fr) < 0.5
        ln.hide_render = v; num_lines[i].hide_render = v; ln.keyframe_insert("hide_render", frame=fr); num_lines[i].keyframe_insert("hide_render", frame=fr)
    # 순서: 왼쪽 A→B · 오른쪽 B→A · 그다음 = 과 X
    u1, u2 = T.u(12, 0.08, 0.22, fr), T.u(12, 0.26, 0.4, fr)
    for side, first, dx in (("L", "A", -1.4), ("R", "B", 1.4)):
        second = "B" if first == "A" else "A"; d = drills[side]
        d.location.x = OX + dx + {"A": -0.5, "B": 0.5}[first if u1 < 1 else second]
        d.location.z = 2.2 - 1.0 * math.sin(math.pi * (u1 if u1 < 1 else u2)); d.keyframe_insert("location", frame=fr)
        for nm, u in ((first, u1), (second, u2)):
            h = holes[side + nm]; s = max(min(u * 2, 1), 0.001); h.scale = (s, s, 1); h.keyframe_insert("scale", frame=fr)
    s = max(T.u(12, 0.5, 0.6, fr), 0.001); eq.scale = (s,) * 3; eq.keyframe_insert("scale", frame=fr)
    s = max(T.u(12, 0.65, 0.75, fr), 0.001); xO.scale = (s,) * 3; xO.keyframe_insert("scale", frame=fr)
    cam_ = next((c for a2, b2, c in CUTCAM if a2 <= fr < b2), CUTCAM[-1][2])
    xO.rotation_quaternion = Vector((0, -1, 0)).rotation_difference(cam_.location - Vector(xO.location)); xO.keyframe_insert("rotation_quaternion", frame=fr)
    # 극장: 추측(파랑)은 18 줄 뒤쪽에만 · 그림자 흐림은 22 줄에서 풀었다 조임
    show = L18[0] + 0.2 * (L18[1] - L18[0]) <= fr <= L18[1]
    for ch in guess.children: ch.hide_render = not show; ch.keyframe_insert("hide_render", frame=fr)
    gt.hide_render = show; gt.keyframe_insert("hide_render", frame=fr)
    blur = T.u(22, 0.0, 0.3, fr) * (1 - T.u(22, 0.55, 1.0, fr))
    for s_ in suns: s_.data.angle = math.radians(0.5 + 28 * blur); s_.data.keyframe_insert("angle", frame=fr)
    claw.rotation_euler.y = 0.3 * math.sin(t * 2.2); claw.keyframe_insert("rotation_euler", frame=fr)
    eye.rotation_euler.z = 0.2 * math.sin(t * 0.9); eye.keyframe_insert("rotation_euler", frame=fr)
    c, _ = cams["wareclose"]; c.location.x = CX + 2.3 - 1.2 * (t % 6) / 6; c.keyframe_insert("location", frame=fr)
    c, _ = cams["theater"]; c.location.x = EX + 3.4 - 1.0 * math.sin(t / 5); c.keyframe_insert("location", frame=fr)
    c, _ = cams["ware"]; c.location.y = -6.5 + 1.2 * T.u(8, 0, 1, fr); c.keyframe_insert("location", frame=fr)
    c, _ = cams["size"]; c.location.y = -7.5 + 1.5 * T.u(24, 0, 1, fr); c.keyframe_insert("location", frame=fr)
    c, _ = cams["desk"]; c.location.x = AX - 0.8 + 0.8 * math.sin(t / 4); c.keyframe_insert("location", frame=fr)
앵커프레임(T, cams, {"한줌": (CX + 3.4, 1.45, 0.3), "오른판": (OX + 1.4, 0, 1.0), "구멍칸": (DX, 0, 0.45), "벽": (EX - 0.2, 2.45, 1.5),
                     "얼음": (EYX - 1.0, EYY, 2.0), "손": (EYX + 1.0, EYY, 1.6), "모니터": (GX + 1.0, 0.5, 1.6), "숫자칠판": (BX - 1.0, 0.9, 2.5)}, ARGS[2])
끝(T, cams)
