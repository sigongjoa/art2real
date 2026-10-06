"""HS-1 하드서피스 = 버튼 순서 = 코드 — 찰흙(스컬팅)은 손가락에 눌려 뭉개지고, 차양은 칠판 코드 한 줄마다 판 → 밀기 → 깎기(빨간 면) → 홈 → chamfer(12→4) 로 다시 깎인다."""
import bpy, math, os
from mathutils import Vector
from 장난감_공용 import *
HERE = os.path.dirname(os.path.abspath(ARGS[0])) if False else "G:/art2real/원화3d/과정/영상05/장난감/HS-1_하드서피스"

def text(s, loc, size, m):
    bpy.ops.object.text_add(location=loc, rotation=(math.pi / 2, 0, 0)); t = bpy.context.object
    t.data.body = s; t.data.size = size; t.data.extrude = 0.005; t.data.materials.append(m); return t
def stl(name, m, red=None):
    try: bpy.ops.wm.stl_import(filepath=f"{HERE}/{name}.stl")
    except Exception: bpy.ops.import_mesh.stl(filepath=f"{HERE}/{name}.stl")
    o = bpy.context.object; o.data.materials.append(m)
    if red:
        o.data.materials.append(red)
        for p in o.data.polygons:
            if 0.2 < abs(p.normal.z) < 0.95: p.material_index = 1
    o.scale = (0.012,) * 3; o.location = (PX, 0, 0.42); return o

T = 시작(); 무대(ARGS[1], trees=False)
# 배경 = 블렌더 3D 뷰포트(사용자 10-06 「블렌더나 CAD 틱하게 · 대비로 잘 보이게」): 어두운 회색 · 격자 바닥 · 빨강 X / 초록 Y 축 · 그림 벽 없음
for o in bpy.data.objects:
    if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "하늘": o.hide_render = True
wn = bpy.context.scene.world.node_tree.nodes
for n in wn:
    if n.type == "BACKGROUND" and n.inputs[1].default_value > 1: n.inputs[0].default_value = (0.11, 0.11, 0.12, 1); n.inputs[1].default_value = 1.0
gm = bpy.data.materials["땅"]; nt = gm.node_tree; P = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
def line(ax, step, w):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = "PINGPONG"; m.inputs[1].default_value = step / 2; nt.links.new(sep.outputs[ax], m.inputs[0])
    c = nt.nodes.new("ShaderNodeMath"); c.operation = "LESS_THAN"; c.inputs[1].default_value = w; nt.links.new(m.outputs[0], c.inputs[0]); return c
def mx(a, b):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = "MAXIMUM"; nt.links.new(a.outputs[0], m.inputs[0]); nt.links.new(b.outputs[0], m.inputs[1]); return m
g = mx(line(0, 0.5, 0.008), line(1, 0.5, 0.008))
mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = (0.08, 0.08, 0.09, 1); mix.inputs[2].default_value = (0.24, 0.24, 0.26, 1)
nt.links.new(g.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = 0.9
for nm, sz, col in (("X축", (40, 0.03, 0.004), (0.9, 0.22, 0.25)), ("Y축", (0.03, 40, 0.004), (0.45, 0.75, 0.2))):
    box(sz, mat(nm, col, 0.5, emit=0.8), loc=(0, -1.6, 0.002) if nm == "X축" else (-3.0, 0, 0.002))
PX = 1.3
yel, red = mat("부품", (0.98, 0.86, 0.35), 0.5), mat("깎은면", (0.95, 0.25, 0.2), 0.5)
box((2.6, 1.4, 0.4), mat("받침", (0.26, 0.26, 0.29), 0.7), loc=(PX, 0, 0.2), bevel=0.03)
steps = {k: stl(k, yel, red if k in ("깎기", "홈", "숫자") else None) for k in ("판", "밀기", "깎기", "홈", "숫자")}
board = box((2.0, 0.06, 1.9), mat("칠판", (0.08, 0.08, 0.09), 0.8), loc=(-1.2, 0.3, 1.45), bevel=0.03)
for x in (-1.95, -0.45): cyl(0.035, 0.6, mat("다리판", (0.25, 0.25, 0.27), 0.8), loc=(x, 0.3, 0.3))
chalk = mat("글씨", (0.55, 0.85, 1.0), 0.5, emit=1.8); hot = mat("바뀐글씨", (1.0, 0.6, 0.2), 0.5, emit=2.0)
L = ["sketch( V )", ".extrude(44)", ".chamfer(12)", ".cut( groove )"]
texts = [text(s, (-2.0, 0.26, 2.05 - 0.4 * i), 0.19, chalk) for i, s in enumerate(L)]
alt = text(".chamfer(4)", (-2.0, 0.26, 2.05 - 0.8), 0.19, hot)
# 그림 액자(AI 가 보는 그림)
fm = bpy.data.materials.new("그림"); fm.use_nodes = True; nt = fm.node_tree; nt.nodes.clear()
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(HERE + "/그림.png"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 1.45; oo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tx.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], oo.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=1.3, rotation=(math.pi / 2, 0, 0)); pic = put(bpy.context.object, fm, loc=(-3.35, 0.1, 1.5))
picbox = box((1.42, 0.05, 1.42), mat("액자", (0.35, 0.25, 0.18), 0.7), loc=(-3.35, 0.24, 1.5))
arrow = bar((-2.6, 0.1, 1.5), (-2.25, 0.1, 1.5), 0.08, mat("화살", (1.0, 0.6, 0.2), 0.5, emit=1.0))
# 찰흙 + 손가락 (따로 떨어진 작업대)
CX = -5.0
box((1.4, 1.4, 0.5), mat("작업대", (0.26, 0.26, 0.29), 0.8), loc=(CX, 0, 0.25), bevel=0.03)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=0.42, location=(CX, 0, 0.9)); clay = bpy.context.object
clay.data.materials.append(mat("찰흙", (0.85, 0.45, 0.3), 0.85)); bpy.ops.object.shade_smooth()
clay.shape_key_add(name="b"); dents = []
for dname, d in [("앞", Vector((0, -1, 0.15))), ("옆", Vector((0.8, -0.5, 0.4)))]:
    k = clay.shape_key_add(name=dname, from_mix=False); d.normalize()
    for v, kv in zip(clay.data.vertices, k.data):
        n = v.co.normalized(); w = max(0.0, n.dot(d) - 0.75) / 0.25
        kv.co = v.co - n * 0.22 * w * w + Vector((0, 0, -0.02 * w))
    dents.append((k, d))
skin = mat("손", (0.98, 0.8, 0.68), 0.6)
finger = cyl(0.07, 0.6, skin, loc=(CX, -1.0, 0.98), rot=(math.pi / 2, 0, 0))
finger.rotation_mode = "QUATERNION"

cams = {"wide": camera("wide", (0.1, -5.6, 1.7), (0.1, 0, 1.0), 22),
        "board": camera("board", (-1.2, -3.9, 1.4), (-1.2, 0.3, 1.3), 26),
        "part": camera("part", (PX, -3.3, 2.5), (PX, 0, 0.5), 25),
        "close": camera("close", (PX + 1.4, -3.1, 1.9), (PX, 0, 0.55), 28),
        "pic": camera("pic", (-2.3, -5.0, 1.4), (-2.3, 0.2, 1.3), 25),
        "clay": camera("clay", (CX, -2.6, 1.3), (CX, 0, 0.8), 28),
        "clay2": camera("clay2", (CX + 1.6, -1.9, 1.5), (CX, 0, 0.85), 30)}

def u_(li, a, b, fr): return T.u(li, a, b, fr) if fr >= T.lines[li][0] else 0.0
for fr in range(1, T.end + 1):
    # 찰흙: 0줄 · 2줄에 손가락이 두 번 누름
    p1 = math.sin(math.pi * u_(0, 0.2, 0.8, fr)); p2 = max(math.sin(math.pi * u_(2, 0.05, 0.45, fr)), 0)
    dents[0][0].value = min(1.0, u_(0, 0.35, 0.6, fr) + 0.0); dents[1][0].value = u_(2, 0.2, 0.4, fr)
    for k, _ in dents: k.keyframe_insert("value", frame=fr)
    if fr < T.lines[2][0]: tip = Vector((CX, -0.42, 0.98)) + Vector((0, -0.6, 0)) * (1 - p1); dirv = Vector((0, 1, -0.15))
    else:
        d = dents[1][1]; tip = Vector((CX, 0, 0.9)) + d * (0.42 + 0.6 * (1 - p2)); dirv = -d
    finger.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv); finger.location = tip - dirv.normalized() * 0.3
    finger.keyframe_insert("location", frame=fr); finger.keyframe_insert("rotation_quaternion", frame=fr)
    # 차양 단계: 4줄 판 → 밀기 · 5줄 깎기 → 홈 · 8줄 숫자
    a = u_(4, 0.05, 0.3, fr); e = u_(4, 0.45, 0.85, fr); c = u_(5, 0.1, 0.2, fr); g = u_(5, 0.5, 0.6, fr); n = u_(8, 0.35, 0.45, fr)
    cur = "숫자" if n > 0.5 else "홈" if g > 0.5 else "깎기" if c > 0.5 else "밀기" if e > 0 else "판" if a > 0 else "홈"
    for k, o in steps.items():
        o.hide_render = k != cur; o.keyframe_insert("hide_render", frame=fr)
    steps["판"].scale = (0.012, 0.012, 0.012 * max(a, 0.01)); steps["판"].keyframe_insert("scale", frame=fr)
    steps["밀기"].scale = (0.012, 0.012, 0.012 * max(e, 0.05)); steps["밀기"].keyframe_insert("scale", frame=fr)
    # 칠판 글씨: 단계마다 한 줄
    show = [a > 0, e > 0, c > 0.5, g > 0.5]
    for i, (t, s) in enumerate(zip(texts, show)):
        t.hide_render = not s or (i == 2 and n > 0.5); t.keyframe_insert("hide_render", frame=fr)
    alt.hide_render = n <= 0.5; alt.keyframe_insert("hide_render", frame=fr)
    # 그림 액자 · 화살: 7줄
    s = u_(7, 0.0, 0.12, fr); s = s if fr < T.lines[9][0] else s
    pic.scale = (max(s, 0.001),) * 3; picbox.scale = (1.42 * max(s, 0.001), 0.05, 1.42 * max(s, 0.001))   # 액자 원래 크기에 곱함(덮어쓰니 1 m 상자가 그림을 가렸다)
    for o in (pic, picbox): o.keyframe_insert("scale", frame=fr)
    arrow.hide_render = u_(7, 0.15, 0.2, fr) < 0.5; arrow.keyframe_insert("hide_render", frame=fr)
    # 카메라 조금씩 움직임
    for nm, amp, sp in (("part", 0.5, 35), ("clay", 0.3, 28), ("board", 0.15, 30), ("wide", 0.4, 50)):
        cc, _ = cams[nm]; cc.location.x = cc.location.x if fr == 1 and False else cc.location.x; 
    cc, _ = cams["part"]; cc.location.x = PX + 0.5 * math.sin(fr / 35); cc.keyframe_insert("location", frame=fr)
    cc, _ = cams["clay2"]; cc.location.x = CX + 1.6 + 0.3 * math.sin(fr / 25); cc.keyframe_insert("location", frame=fr)
    cc, _ = cams["close"]; cc.location.y = -3.1 + 0.25 * math.sin(fr / 30); cc.keyframe_insert("location", frame=fr)
끝(T, cams)
