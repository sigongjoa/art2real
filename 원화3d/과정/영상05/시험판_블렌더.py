"""시험판 블렌더 — 울타리 뒤 지온 고양이 두 마리(앞은 머리, 뒤는 꼬리만 보인다) · 컷마다 카메라.
    blender -b -P 시험판_블렌더.py -- <컷.json> <배경.png> <프레임 폴더>
컷.json = [{"cam": 이름, "n": 프레임 수}, ...] · 24 fps · 1080×1920 · Eevee."""
import bpy, sys, json, math
from mathutils import Vector

CUTS, BG, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
CUTS = json.load(open(CUTS, encoding="utf-8"))
FPS = 24
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.eevee.taa_render_samples = 24
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1080, 1920, FPS
sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.45
sc.render.filepath = OUT.rstrip("/\\") + "/"
sc.render.image_settings.file_format = "PNG"

def mat(name, rgb, rough=0.6, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    if emit: p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    return m

def put(o, m, parent=None, loc=(0, 0, 0)):
    o.data.materials.append(m)
    if parent: o.parent = parent
    o.location = loc
    return o

def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.parent = parent; e.location = loc
    return e

def cyl(r, d, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=32, rotation=rot)
    o = bpy.context.object
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = bevel, 4
    bpy.ops.object.shade_smooth()
    return put(o, m, parent, loc)

def ball(r, m, parent=None, loc=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16)
    o = bpy.context.object; o.scale = scale; bpy.ops.object.shade_smooth()
    return put(o, m, parent, loc)

def cone(r, d, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=d, vertices=24, rotation=rot)
    return put(bpy.context.object, m, parent, loc)

# ── 무대: 땅 · 뒤 판(SDXL 하늘) · 나무 · 울타리 ──
bpy.ops.mesh.primitive_plane_add(size=400); put(bpy.context.object, mat("땅", (0.42, 0.72, 0.38), 0.9))
img = bpy.data.images.load(BG); sky = bpy.data.materials.new("하늘"); sky.use_nodes = True
nt = sky.node_tree; nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
em = nt.nodes.new("ShaderNodeEmission"); outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], outn.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
p = put(bpy.context.object, sky, loc=(0, 30, 20)); p.scale = (38, 56, 1)
w = sc.world = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.85, 1.0, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.45
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(-30)))
bpy.context.object.data.energy = 3.5; bpy.context.object.data.angle = math.radians(12)

trunk, leaf = mat("줄기", (0.45, 0.3, 0.18)), mat("잎", (0.3, 0.62, 0.32))
for x, y, s in [(-3.2, 5, 1.0), (-1.2, 8, 1.3), (1.5, 6, 1.1), (3.6, 9, 1.4), (-5, 11, 1.5), (5.5, 4.5, 0.9)]:
    cyl(0.12 * s, 1.0 * s, trunk, loc=(x, y, 0.5 * s)); ball(0.7 * s, leaf, loc=(x, y, 1.35 * s))

wood = [mat("나무%d" % i, c, 0.8) for i, c in enumerate([(0.82, 0.6, 0.38), (0.76, 0.55, 0.34), (0.86, 0.66, 0.42)])]
FX, FH = 1.5, 0.62
n = 20
for i in range(n):
    x = -FX + (i + 0.5) * 2 * FX / n
    bpy.ops.mesh.primitive_cube_add(size=1)
    b = put(bpy.context.object, wood[i % 3], loc=(x, 0, FH / 2)); b.scale = (2 * FX / n - 0.004, 0.05, FH + 0.02 * (i % 2))
    bv = b.modifiers.new("b", "BEVEL"); bv.width, bv.segments = 0.012, 3
    cone(0.075, 0.08, wood[i % 3], loc=(x, 0, FH + 0.04), rot=(0, 0, math.pi / 4)).scale = (1, 0.35, 1)

# ── 지온 고양이: 원기둥 몸 · 구 머리 · 원뿔 귀 · 원기둥 다리 · 원기둥 사슬 꼬리 ──
fur, dark, pink = mat("털", (0.95, 0.58, 0.25)), mat("눈", (0.05, 0.05, 0.05), 0.2), mat("코", (0.95, 0.5, 0.55))
def cat(name, x):
    root = empty(name, loc=(x, 0.3, 0))
    cyl(0.11, 0.42, fur, root, (0, 0, 0.24), (0, math.pi / 2, 0), bevel=0.05)
    neck = empty(name + "목", root, (0.2, 0, 0.3))
    ball(0.1, fur, neck, (0.07, 0, 0.03))
    for s in (-1, 1):
        cone(0.035, 0.08, fur, neck, (0.06, s * 0.05, 0.13), (s * -0.3, 0, 0))
        ball(0.016, dark, neck, (0.155, s * 0.038, 0.05))
    ball(0.012, pink, neck, (0.17, 0, 0.02))
    legs = []
    for lx in (-0.14, 0.14):
        for ly in (-0.06, 0.06):
            h = empty(name + "엉", root, (lx, ly, 0.16)); cyl(0.028, 0.16, fur, h, (0, 0, -0.08)); legs.append(h)
    tail, par, loc = [], root, (-0.2, 0, 0.27)
    for k in range(5):
        e = empty(name + "꼬%d" % k, par, loc); cyl(0.022, 0.09, fur, e, (0, 0, 0.045)); tail.append(e); par, loc = e, (0, 0, 0.085)
    return root, neck, legs, tail

A = cat("앞고양이", 0.6); B = cat("뒤고양이", -1.38)

# 상상 몸통 — 머리와 꼬리를 잇는 반투명 빛 원기둥(울타리 앞)
gm = mat("상상", (1.0, 0.6, 0.25), 0.5, emit=0.5)
if hasattr(gm, "surface_render_method"): gm.surface_render_method = "BLENDED"
else: gm.blend_method = "BLEND"
ghost = cyl(0.13, 3.2, gm, loc=(0.03, -0.12, 0.26), rot=(0, math.pi / 2, 0), bevel=0.05)
alpha = next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]

# ── 카메라 ──
def camera(name, frm, to, lens=35):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.lens = lens; c.location = frm
    t = empty(name + "표적", loc=to); k = c.constraints.new("TRACK_TO"); k.target = t
    k.track_axis, k.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return c, t
cams = {"wide": camera("wide", (0, -3.7, 0.38), (0, 0, 0.62), 22),
        "head": camera("head", (1.75, -1.3, 0.5), (1.68, 0.3, 0.36), 40),
        "tail": camera("tail", (-1.72, -1.3, 0.55), (-1.68, 0.3, 0.42), 40),
        "push": camera("push", (0, -3.7, 0.38), (0, 0, 0.62), 22),
        "top": camera("top", (0, -3.7, 0.38), (0, 0, 0.62), 22),
        "ghost": camera("ghost", (0, -3.5, 0.38), (0, 0, 0.6), 22)}

# ── 시간표 ──
f, spans = 1, {}
for c in CUTS:
    spans.setdefault(c["cam"], []).append((f, f + c["n"] - 1))
    sc.timeline_markers.new(c["cam"], frame=f).camera = cams[c["cam"]][0]; f += c["n"]
sc.frame_start, sc.frame_end = 1, f - 1
ease = lambda u: 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0), 1))
w0, w1 = spans["wide"][0]; h0, h1 = spans["head"][0]; p0, p1 = spans["push"][0]; t0, t1 = spans["top"][0]; g0, g1 = spans["ghost"][0]

for fr in range(1, f):
    t = fr / FPS
    walk = ease((fr - w0) / ((w1 - w0) * 0.85))
    A[0].location.x = 0.6 + (1.38 - 0.6) * walk; A[0].keyframe_insert("location", frame=fr)
    moving = 0 < walk < 1
    for i, leg in enumerate(A[2]):
        leg.rotation_euler.y = 0.45 * math.sin(t * 9 + (math.pi if i in (1, 2) else 0)) if moving else 0
        leg.keyframe_insert("rotation_euler", frame=fr)
    A[1].rotation_euler.z = -1.2 * ease((fr - h0 - 6) / 10) * (1 - ease((fr - p0) / 12)); A[1].keyframe_insert("rotation_euler", frame=fr)
    for cat_, ph in ((A, 0.0), (B, 1.3)):
        for k, e in enumerate(cat_[3]):
            e.rotation_euler.y = (-0.9 if k == 0 else 0.3) + 0.22 * math.sin(t * 3.2 + ph - k * 0.6)
            e.keyframe_insert("rotation_euler", frame=fr)
    pc = cams["push"][0]; pc.location = Vector((0, -3.7, 0.38)).lerp(Vector((0, -2.7, 0.35)), ease((fr - p0) / (p1 - p0))); pc.keyframe_insert("location", frame=fr)
    tc = cams["top"][0]; u = ease((fr - t0) / ((t1 - t0) * 0.75))
    tc.location = Vector((0, -3.7, 0.38)).lerp(Vector((0, -1.3, 4.0)), u); tc.keyframe_insert("location", frame=fr)
    tt = cams["top"][1]; tt.location = Vector((0, 0, 0.62)).lerp(Vector((0, 0.35, 0.2)), u); tt.keyframe_insert("location", frame=fr)
    alpha.default_value = 0.6 * ease((fr - g0 - 4) / 18) if fr >= g0 else 0.0; alpha.keyframe_insert("default_value", frame=fr)
    ghost.hide_render = fr < g0; ghost.keyframe_insert("hide_render", frame=fr)

if "--still" in sys.argv:  # 컷마다 끝에서 1/4 지점 한 장 — 싼 확인
    f = 1
    for k, c in enumerate(CUTS):
        sc.frame_set(f + c["n"] * 3 // 4); sc.render.filepath = OUT + "/still_%d.png" % k
        bpy.ops.render.render(write_still=True); f += c["n"]
else:
    bpy.ops.render.render(animation=True)
