# -*- coding: utf-8 -*-
"""v2 그림 공통(8-x · 9-x 블록 그림). 블렌더 4.0 헤드리스 · EEVEE + Freestyle 선 · 투명 렌더 → _마감.py 가 흰 바탕 + 이름표.
쓰는 법:  blender -b -P <장면>.py   (장면 스크립트 안에서 import _블록 as B)
좌표: 블렌더 그대로(z 위). 인물 · 머리의 앞은 -y."""
import bpy, bmesh, math, json, os, sys, mathutils
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.dirname(HERE)
_mats = {}
_labels = []

CLAY = (0.86, 0.85, 0.83)
WARM = (0.93, 0.78, 0.62)
COOL = (0.66, 0.78, 0.92)
DARK = (0.35, 0.35, 0.38)
DARK2 = (0.62, 0.61, 0.60)


def scene(res=(1920, 1080), line=1.8, crease=140):
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.eevee.taa_render_samples = 32
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.4
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
    sun.data.energy = 3.4; sun.rotation_euler = Euler((math.radians(40), math.radians(-25), math.radians(-35)))
    sun.data.angle = math.radians(8)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.clip_end = 1000; sc.camera = cam
    sc.render.use_freestyle = True; sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = line
    vl = sc.view_layers[0]; fs = vl.freestyle_settings; fs.crease_angle = math.radians(crease)
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("ls")
    ls.linestyle = ls.linestyle or bpy.data.linestyles.new("x")
    ls.linestyle.color = (0.0, 0.0, 0.0); ls.linestyle.alpha = 1.0; ls.linestyle.thickness = line
    ls.select_by_visibility = True; ls.visibility = "VISIBLE"
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    nofs = bpy.data.collections.new("선없음"); sc.collection.children.link(nofs)
    ls.select_by_collection = True; ls.collection = nofs; ls.collection_negation = "EXCLUSIVE"
    _labels.clear()
    return sc


def sun(rx=40, ry=-25, rz=-35, energy=2.6):
    o = bpy.data.objects["sun"]; o.rotation_euler = Euler((math.radians(rx), math.radians(ry), math.radians(rz))); o.data.energy = energy


def mat(color, alpha=1.0):
    key = (tuple(round(c, 3) for c in color), alpha)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new("m%d" % len(_mats)); m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*color, 1); p.inputs["Roughness"].default_value = 0.9
    for k in ("Specular IOR Level", "Specular"):
        if k in p.inputs: p.inputs[k].default_value = 0.15
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha; m.blend_method = "BLEND"; m.shadow_method = "NONE"
    _mats[key] = m; return m


def _obj(name, me, color, parent=None):
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat(color)); o.parent = parent; return o


def hull(points, name="hull", color=CLAY, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), merge=1.0):
    """점 모음의 볼록 껍질 = 평면 조각 덩어리."""
    bm = bmesh.new()
    for p in points: bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(merge), verts=bm.verts, edges=bm.edges)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = _obj(name, me, color, parent); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]; return o


def cbox(x0, x1, y0, y1, z0, z1, c=0.0):
    """모서리를 c 만큼 깎은 상자 점(볼록 껍질용)."""
    if c <= 0: return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    pts = []
    for x in (x0, x1):
        for y in (y0, y1):
            for z in (z0, z1):
                sx, sy, sz = (1 if x == x0 else -1), (1 if y == y0 else -1), (1 if z == z0 else -1)
                pts += [(x + sx * c, y, z + sz * c), (x, y + sy * c, z + sz * c), (x + sx * c, y + sy * c, z)]
    return pts


def tbox(z0, z1, w0, d0, w1, d1, x0=0.0, y0=0.0, x1=None, y1=None):
    """z0→z1 로 가늘어지는 사각 기둥 점. 아래(z0) 너비 w0 · 두께 d0, 위 w1 · d1."""
    x1 = x0 if x1 is None else x1; y1 = y0 if y1 is None else y1
    return [(x0 + sx * w0 / 2, y0 + sy * d0 / 2, z0) for sx in (-1, 1) for sy in (-1, 1)] + \
           [(x1 + sx * w1 / 2, y1 + sy * d1 / 2, z1) for sx in (-1, 1) for sy in (-1, 1)]


def empty(name="g", loc=(0, 0, 0), rot=(0, 0, 0), parent=None, scale=(1, 1, 1)):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.location = loc; e.rotation_euler = [math.radians(a) for a in rot]; e.parent = parent; e.scale = scale; return e


def smooth_copy(objs, name="smooth", color=CLAY, voxel=0.03, iters=12, parent=None):
    """여러 조각을 한 덩어리로 녹여 매끈하게(「진짜 몸」 대역)."""
    bpy.ops.object.select_all(action="DESELECT")
    cps = []
    for o in objs:
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
        c.matrix_world = o.matrix_world.copy(); c.parent = None; c.matrix_world = o.matrix_world.copy(); cps.append(c)
    for c in cps: c.select_set(True)
    bpy.context.view_layer.objects.active = cps[0]; bpy.ops.object.join(); j = bpy.context.active_object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    m = j.modifiers.new("r", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel
    s = j.modifiers.new("s", "SMOOTH"); s.iterations = iters; s.factor = 0.8
    c = j.modifiers.new("c", "CORRECTIVE_SMOOTH"); c.iterations = iters; c.use_only_smooth = True
    bpy.ops.object.modifier_apply(modifier="r"); bpy.ops.object.modifier_apply(modifier="s"); bpy.ops.object.modifier_apply(modifier="c")
    for p in j.data.polygons: p.use_smooth = True
    j.name = name; j.data.materials.clear(); j.data.materials.append(mat(color))
    if parent:
        mw = j.matrix_world.copy(); j.parent = parent; j.matrix_parent_inverse = parent.matrix_world.inverted()
    return j


def look(target=(0, 0, 0), yaw=0, pitch=0, ortho=10, dist=50):
    """yaw 0 = 앞(-y 쪽)에서 · +90 = 인물의 왼쪽(+x)에서 · pitch + = 위에서."""
    cam = bpy.context.scene.camera; y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = Vector(target) + d * dist; cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); cam.data.ortho_scale = ortho


def label(text, pos, size=44, color="#333"):
    """세계 좌표 pos 에 이름표(렌더 뒤 _마감.py 가 그린다)."""
    _labels.append((text, tuple(pos), size, color))


def shot(name):
    sc = bpy.context.scene; bpy.context.view_layer.update()
    raw = os.path.join(HERE, "_raw", name + ".png"); os.makedirs(os.path.dirname(raw), exist_ok=True)
    sc.render.filepath = raw; bpy.ops.render.render(write_still=True)
    W, H = sc.render.resolution_x, sc.render.resolution_y; labs = []
    for t, p, s, c in _labels:
        v = world_to_camera_view(sc, sc.camera, Vector(p)); labs.append([t, v.x * W, (1 - v.y) * H, s, c])
    with open(raw[:-4] + ".json", "w", encoding="utf-8") as f: json.dump(labs, f, ensure_ascii=False)
    return raw


def nofs(o):
    """Freestyle 선을 긋지 않을 물체(철사 · 띠 · 선 자체)."""
    for c in list(o.users_collection): c.objects.unlink(o)
    bpy.data.collections["선없음"].objects.link(o); return o


def flat(color):
    """빛 안 받는 단색(선 · 철사용)."""
    key = ("flat", tuple(color))
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new("flat"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*color, 1); o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0]); _mats[key] = m; return m


def cage(x0, x1, y0, y1, z0, z1, parent=None, t=0.014, color=(0.3, 0.3, 0.34), mids=True):
    """철사 상자(덩어리를 감싸는 우리). mids = 앞면 가운데 세로선 · 가로선."""
    vs = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    es = [(i, j) for i in range(8) for j in range(i + 1, 8) if sum(a != b for a, b in zip(vs[i], vs[j])) == 1]
    if mids:
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2; n = len(vs)
        vs += [(xm, y0, z0), (xm, y0, z1), (x0, y0, zm), (x1, y0, zm), (x0, y0, zm), (x0, y1, zm), (x1, y0, zm), (x1, y1, zm)]
        es += [(n, n + 1), (n + 2, n + 3), (n + 4, n + 5), (n + 6, n + 7)]
    me = bpy.data.meshes.new("cage"); me.from_pydata(vs, es, []); me.update()
    o = _obj("cage", me, color, parent)
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.scene.objects: x.select_set(x == o)
    bpy.ops.object.convert(target="CURVE"); o.data.bevel_depth = t; o.data.bevel_resolution = 1
    o.data.materials.clear(); o.data.materials.append(flat(color)); return nofs(o)


ACCENT = (0.80, 0.22, 0.16)


def section_lines(o, planes, color=ACCENT, t=0.018, lift=1.01):
    """물체 o 를 평면들(점, 법선 — o 의 로컬 좌표)로 잘라 그 단면 고리를 굵은 선으로. 표면을 따라 휘는 구성선."""
    out = []
    for co, no in planes:
        bm = bmesh.new(); bm.from_mesh(o.data)
        r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
        cut = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        idx = {}; vs = []; es = []
        for e in cut:
            ij = []
            for v in e.verts:
                if v not in idx: idx[v] = len(vs); vs.append(v.co.copy())
                ij.append(idx[v])
            es.append(tuple(ij))
        bm.free()
        c = sum(vs, Vector()) / max(1, len(vs)); vs = [c + (v - c) * lift for v in vs]
        me = bpy.data.meshes.new("cut"); me.from_pydata(vs, es, []); me.update()
        l = bpy.data.objects.new("cut", me); bpy.context.scene.collection.objects.link(l)
        l.parent = o.parent; l.matrix_basis = o.matrix_basis.copy()
        bpy.context.view_layer.objects.active = l
        for x in bpy.context.scene.objects: x.select_set(x == l)
        bpy.ops.object.convert(target="CURVE"); l.data.bevel_depth = t; l.data.bevel_resolution = 1
        l.data.materials.append(flat(color)); out.append(nofs(l))
    return out


def rod(p0, p1, color=ACCENT, t=0.03, parent=None, dashed=0):
    """곧은 선(곡선 + 두께). dashed>0 이면 그 길이로 끊는다."""
    p0, p1 = Vector(p0), Vector(p1); segs = [(p0, p1)]
    if dashed:
        L = (p1 - p0).length; n = max(1, int(L / dashed)); d = (p1 - p0) / n
        segs = [(p0 + d * i, p0 + d * (i + 0.6)) for i in range(n)]
    cu = bpy.data.curves.new("rod", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = t; cu.bevel_resolution = 1
    for a, b in segs:
        sp = cu.splines.new("POLY"); sp.points.add(1); sp.points[0].co = (*a, 1); sp.points[1].co = (*b, 1)
    o = bpy.data.objects.new("rod", cu); bpy.context.scene.collection.objects.link(o); o.parent = parent
    cu.materials.append(flat(color)); return nofs(o)
