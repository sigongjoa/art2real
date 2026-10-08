"""장난감 CG 쇼츠 — 블렌더 쪽 공용(무대 · 재질 · 지온 도형 · 지온 고양이 · 카메라 · 시간표). 장면.py 가 import 한다.
장면.py 는 `T = 시작()` → 무대 · 카메라를 짓고 → 프레임마다 키를 넣고 → `끝()`."""
import bpy, sys, json, math
from mathutils import Vector

FPS = 24
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ease = lambda u: 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0), 1))

class 시간표:
    def __init__(s, d):
        s.cuts, s.lines = d["cuts"], d["lines"]          # cuts=[{"cam","n"}] · lines=[[f0,f1]] (줄마다)
        s.end = sum(c["n"] for c in s.cuts)
    def u(s, i, a=0.0, b=1.0, fr=None):                    # 줄 i 안 비율 a..b 구간 진행도 0..1
        f0, f1 = s.lines[i]; L = f1 - f0
        return ease((fr - f0 - a * L) / max(1, (b - a) * L))

def 시작():
    T = 시간표(json.load(open(ARGS[0], encoding="utf-8")))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.eevee.taa_render_samples = 24
    import os as _os   # 10-08: 편 폴더에 「가로」 파일이 있으면 굽기가 TOY_LAND=1 을 넘김 → 1920×1080
    sc.render.resolution_x, sc.render.resolution_y = (1920, 1080) if _os.environ.get("TOY_LAND") else (1080, 1920); sc.render.fps = FPS
    sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.45
    sc.render.image_settings.file_format = "PNG"
    sc.frame_start, sc.frame_end = 1, T.end
    return T

def 끝(T, cams):
    sc = bpy.context.scene; f = 1
    for c in T.cuts:
        sc.timeline_markers.new(c["cam"], frame=f).camera = cams[c["cam"]][0]; f += c["n"]
    out = ARGS[2]
    if "--still" in ARGS:                       # 컷마다 3/4 지점 한 장
        f = 1
        for k, c in enumerate(T.cuts):
            sc.frame_set(f + c["n"] * 3 // 4); sc.render.filepath = out + "/still_%02d.png" % k
            bpy.ops.render.render(write_still=True); f += c["n"]
    else:
        import os as _os
        if _os.environ.get("FRAMES"):   # 10-08: 일부 구간만 렌더(모션 시안) · 「a-」 는 끝까지
            a_, b_ = _os.environ["FRAMES"].split("-"); sc.frame_start, sc.frame_end = int(a_), int(b_) if b_ else T.end
        sc.render.filepath = out.rstrip("/\\") + "/"; bpy.ops.render.render(animation=True)

# ── 재질 · 도형 ──
def mat(name, rgb, rough=0.6, emit=0.0, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    if emit: p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = emit
    if alpha:
        if hasattr(m, "surface_render_method"): m.surface_render_method = "BLENDED"
        else: m.blend_method = "BLEND"
    return m
def alpha_of(m): return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]

def put(o, m, parent=None, loc=(0, 0, 0)):
    if m: o.data.materials.append(m)
    if parent: o.parent = parent
    o.location = loc
    return o
def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.parent = parent; e.location = loc
    return e
def cyl(r, d, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=48, rotation=rot); o = bpy.context.object
    if bevel: b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = bevel, 4
    bpy.ops.object.shade_smooth(); return put(o, m, parent, loc)
def ball(r, m, parent=None, loc=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16); o = bpy.context.object
    o.scale = scale; bpy.ops.object.shade_smooth(); return put(o, m, parent, loc)
def cone(r, d, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=d, vertices=32, rotation=rot); return put(bpy.context.object, m, parent, loc)
def box(size, m, parent=None, loc=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.scale = size
    if bevel: b = o.modifiers.new("b", "BEVEL"); b.width, b.segments = bevel, 3
    return put(o, m, parent, loc)
def bar(p, q, r, m):                            # 두 점 잇는 원기둥
    p, q = Vector(p), Vector(q); d = q - p
    o = cyl(r, d.length, m, loc=(p + q) / 2)
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o

# ── 무대: 땅 · SDXL 하늘 판 · 빛 · 둥근 나무 ──
def 무대(bg, trees=True):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=400); put(bpy.context.object, mat("땅", (0.42, 0.72, 0.38), 0.9))
    sky = bpy.data.materials.new("하늘"); sky.use_nodes = True; nt = sky.node_tree; nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(bg)
    em = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], o.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(math.pi / 2, 0, 0))
    put(bpy.context.object, sky, loc=(0, 30, 20)).scale = (38, 56, 1)
    w = sc.world = bpy.data.worlds.new("w"); w.use_nodes = True
    nt = w.node_tree; bgn = nt.nodes["Background"]; bgn.inputs[0].default_value = (0.75, 0.85, 1.0, 1); bgn.inputs[1].default_value = 0.45
    # 카메라에 보이는 하늘은 밝은 파스텔(빛은 그대로 0.45) — 하늘 판이 없는 쪽이 회색 벽으로 나오던 것
    cam_bg = nt.nodes.new("ShaderNodeBackground"); cam_bg.inputs[0].default_value = (0.62, 0.78, 1.0, 1); cam_bg.inputs[1].default_value = 1.55
    lp = nt.nodes.new("ShaderNodeLightPath"); mix = nt.nodes.new("ShaderNodeMixShader"); outw = nt.nodes["World Output"]
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); nt.links.new(bgn.outputs[0], mix.inputs[1]); nt.links.new(cam_bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], outw.inputs[0])
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(-30)))
    bpy.context.object.data.energy = 3.5; bpy.context.object.data.angle = math.radians(12)
    if trees:
        trunk, leaf = mat("줄기", (0.45, 0.3, 0.18)), mat("잎", (0.3, 0.62, 0.32))
        for x, y, s in [(-3.2, 5, 1.0), (-1.2, 8, 1.3), (1.5, 6, 1.1), (3.6, 9, 1.4), (-5, 11, 1.5), (5.5, 4.5, 0.9)]:
            cyl(0.12 * s, 1.0 * s, trunk, loc=(x, y, 0.5 * s)); ball(0.7 * s, leaf, loc=(x, y, 1.35 * s))

# ── 지온 고양이(+x 를 본다) — 반환: root · neck · legs · tail ──
_fur = {}
def 고양이(name, loc, color=(0.95, 0.58, 0.25)):
    if color not in _fur: _fur[color] = mat("털%d" % len(_fur), color)
    fur, dark, pink = _fur[color], mat("눈", (0.05, 0.05, 0.05), 0.2), mat("코", (0.95, 0.5, 0.55))
    root = empty(name, loc=loc)
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
    tail, par, l = [], root, (-0.2, 0, 0.27)
    for k in range(5):
        e = empty(name + "꼬%d" % k, par, l); cyl(0.022, 0.09, fur, e, (0, 0, 0.045)); tail.append(e); par, l = e, (0, 0, 0.085)
    return root, neck, legs, tail

def 고양이_키(c, fr, walking, ph=0.0):           # 다리 · 꼬리 한 프레임
    t = fr / FPS
    for i, leg in enumerate(c[2]):
        leg.rotation_euler.y = 0.45 * math.sin(t * 9 + (math.pi if i in (1, 2) else 0)) if walking else 0
        leg.keyframe_insert("rotation_euler", frame=fr)
    for k, e in enumerate(c[3]):
        e.rotation_euler.y = (-0.9 if k == 0 else 0.3) + 0.22 * math.sin(t * 3.2 + ph - k * 0.6)
        e.keyframe_insert("rotation_euler", frame=fr)

# ── 카메라: Track-To 표적 · 반환 (cam, target) ──
def camera(name, frm, to, lens=35):
    sc = bpy.context.scene
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.data.lens = lens; c.location = frm
    t = empty(name + "표적", loc=to); k = c.constraints.new("TRACK_TO"); k.target = t
    k.track_axis, k.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return c, t


# ── 10-08 모션 키트용(모션키트.py): 프레임마다 3D 점의 화면 좌표 · 물체 깜빡 ──
def 앵커프레임(T, cams, 점들, out):
    """점들 = {"이름": (x, y, z)} → out/앵커프레임.json = {프레임: {이름: [x, y]}} (0..1 · 그 프레임 카메라 기준)"""
    from bpy_extras.object_utils import world_to_camera_view
    import os
    sc = bpy.context.scene; cut = []; f0 = 1
    for c in T.cuts: cut.append((f0, f0 + c["n"], cams[c["cam"]][0])); f0 += c["n"]
    per = {}
    for fr in range(1, T.end + 1):
        sc.frame_set(fr); cam = next((c for a, b, c in cut if a <= fr < b), cut[-1][2])
        per[fr] = {nm: [round(v, 4) for v in (lambda co: (co.x, 1 - co.y))(world_to_camera_view(sc, cam, Vector(p)))] for nm, p in 점들.items()}
    os.makedirs(out, exist_ok=True); json.dump(per, open(out + "/앵커프레임.json", "w", encoding="utf-8"))

def 깜빡(T, i, a, fr):
    """줄 i 의 비율 a 부터: 0.3 초 차오름 → 0.6 초 주기 두 번 → 0.5 로 남음(건축사전 빨간 틀 실측) · 0..1"""
    f0, f1 = T.lines[i]; t = (fr - (f0 + a * (f1 - f0))) / FPS
    if t < 0: return 0.0
    if t < 0.3: return t / 0.3
    if t < 1.5: return 0.55 + 0.45 * math.cos(2 * math.pi * (t - 0.3) / 0.6)
    return 0.5
