# -*- coding: utf-8 -*-
"""패드를 짓는다. 라이브 Blender(MCP)에서도, 헤드리스에서도 같은 코드다.

    blender -b --python buildpad.py -- out/workbench.blend      # 씬 통째로 재생성
    (또는 라이브 세션에서)  import buildpad; buildpad.build(); buildpad.plant_horns()


    윤곽 + 판 선을 **엣지 제약**으로 넣고 제약 삼각화 -> 어깨 돔으로 들어올림
    -> 판 선 모서리에 크리스·베벨웨이트, 정점은 안으로 눌러 홈

triangle_fill 은 입력 엣지 객체를 **새로 만든다** — 인덱스로도 객체로도 못 찾는다.
좌표로 다시 찾아야 한다 (101번과 같은 함정).
"""
import json
import math
import os

import bmesh
import bpy
import numpy as np


def _segs(pts, closed):
    a = np.asarray(pts, float)
    b = np.roll(a, -1, axis=0) if closed else a[1:]
    if not closed:
        a = a[:-1]
    return np.stack([a, b], 1)


def _on(p, segs):
    """점이 선분 다발 위에 있나. 세분으로 생긴 중점도 잡아야 하니 거리로 본다."""
    a, b = segs[:, 0], segs[:, 1]
    d = b - a
    L2 = (d * d).sum(1)
    t = np.clip(((np.asarray(p) - a) * d).sum(1) / np.where(L2 < 1e-12, 1e-12, L2), 0, 1)
    q = a + t[:, None] * d
    return bool((((q - p) ** 2).sum(1) < EPS * EPS).any())

H = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
GROOVE = float(os.environ.get("GROOVE", 0.0035))
SUBD = int(os.environ.get("SUBD", 3))           # 들어올리기 전 평면 세분 횟수
EPS = 1e-4                                      # 선 위 판정 거리 (좌표 단위 ~0.1 스케일)
BACK_K = float(os.environ.get("BACK_K", 1.0))   # 노브. 1.0 = 뒷면이 앞면과 대칭이라는 **가정**
B = json.load(open(H + "/parts/base.json"))
L = json.load(open(H + "/parts/lines.json"))
D = json.load(open(H + "/parts/depth.json"))
_ZS = [b["z"] for b in D["bands"]]


def band(z):
    """그 높이의 대역. 범위 밖은 끝 대역으로 잡아둔다."""
    if z <= _ZS[0]:
        return D["bands"][0]
    if z >= _ZS[-1]:
        return D["bands"][-1]
    i = max(i for i, zz in enumerate(_ZS) if zz <= z)
    a, b = D["bands"][i], D["bands"][i + 1]
    t = (z - a["z"]) / (b["z"] - a["z"])
    return {k: a[k] + t * (b[k] - a[k]) for k in ("x0", "x1", "yf", "yb")}


def surf(u, z, back=False):
    """깊이를 **높이마다** 측면 윤곽에서 읽는다 (타원체 반경 하나가 아니다).

    단면은 그 높이의 폭·깊이로 만든 타원. 윤곽선(t=±1)에서 앞뒤가 만난다.
    앞면 yf 는 측정값이고, **뒷면은 대칭 가정**이다 — 후면 원화에서 이 견갑은
    방패에 가려 있어서 뒤쪽 x 단면을 못 봤다 (BACK_K 노브).
    """
    b = band(z)
    xc, xr = (b["x0"] + b["x1"]) / 2, max((b["x1"] - b["x0"]) / 2, 1e-6)
    yc, hd = (b["yf"] + b["yb"]) / 2, (b["yb"] - b["yf"]) / 2
    t = (u - xc) / xr
    k = max(1.0 - t * t, 0.0) ** 0.5
    return yc + hd * k * BACK_K if back else yc - hd * k


def mid(z):
    """실루엣 위의 깊이. 윤곽에서는 앞면과 뒷면이 여기서 만난다."""
    b = band(z)
    return (b["yf"] + b["yb"]) / 2


dome = surf   # 옛 이름으로 부르던 자리 (plant_horns 는 B 를 직접 쓴다)


def build():
    if "PAD" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["PAD"], do_unlink=True)
    K = lambda p: (round(p[0], 5), round(p[1], 5))
    bm = bmesh.new()
    vmap = {}

    def V(p):
        k = K(p)
        if k not in vmap:
            vmap[k] = bm.verts.new((k[0], 0.0, k[1]))
        return vmap[k]

    def chain(pts, closed):
        es = []
        seq = list(zip(pts, pts[1:] + pts[:1])) if closed else list(zip(pts[:-1], pts[1:]))
        for a, b in seq:
            va, vb = V(a), V(b)
            if va is not vb:
                try:
                    es.append(bm.edges.new((va, vb)))
                except ValueError:
                    pass
        return es

    out_e = chain(L["outline"], True)
    line_e = []
    LSEG, LV = set(), set()
    for arc in L["arcs"]:
        line_e += chain(arc, False)
        for a, b in zip(arc[:-1], arc[1:]):
            LSEG.add(frozenset((K(a), K(b))))
            LV.add(K(a)); LV.add(K(b))
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False,
                            edges=out_e + line_e, normal=(0, -1, 0))
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    cr = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    bw = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    n = 0
    for e in bm.edges:
        if frozenset(((round(v.co.x, 5), round(v.co.z, 5)) for v in e.verts)) in LSEG:
            e[cr] = 1.0; e[bw] = 1.0; e.smooth = False; n += 1
    # 평면에서 잘게 나눈 **뒤** 들어올린다. triangle_fill 은 내부 정점을 안 만들어서
    # 큰 삼각형 가운데가 평평했다 — 단면이 부풀 자리가 없다 (측면 면적 72%)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=SUBD, use_grid_fill=True)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()

    # 나눈 뒤에는 좌표 키가 안 맞는다. 선 위인지 **거리로** 판정한다
    OSEG = _segs(L["outline"], True)
    ASEG = np.concatenate([_segs(a, False) for a in L["arcs"]])

    def place(v, back=False):
        p = (v.co.x, v.co.z)
        if _on(p, OSEG):
            return mid(v.co.z)
        g = GROOVE if _on(p, ASEG) else 0.0
        return surf(p[0], p[1], back) + (-g if back else g)

    for v in bm.verts:
        v.co.y = place(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if sum(f.normal.y * f.calc_area() for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])

    # 뒷면 — 같은 위상을 복제해 y 만 뒤로 보낸다. 테두리(t=±1)에서 앞뒤가 같은 값이라
    # remove_doubles 가 저절로 꿰맨다. 브리지를 따로 안 놓는 이유가 이것
    dup = bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
    nv = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
    nf = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
    for v in nv:
        v.co.y = place(v, back=True)
    bmesh.ops.reverse_faces(bm, faces=nf)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    bnd = [e for e in bm.edges if e.is_boundary]
    if bnd:                                     # 세분이 남긴 자잘한 구멍
        bmesh.ops.holes_fill(bm, edges=bnd, sides=8)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        bm.edges.ensure_lookup_table()
    open_e = sum(1 for e in bm.edges if e.is_boundary)
    print("  테두리 열린 엣지 %d (0 이면 닫힌 껍질)" % open_e)

    me = bpy.data.meshes.new("PAD")
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("PAD", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.get("M_pad") or bpy.data.materials.new("M_pad")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.52, 0.52, 0.70, 1)
    me.materials.append(mat)
    # SOLIDIFY 를 뺐다 — 앞면을 0.010 평행 복사하던 것이 "뒤를 결정 못 한" 자리였다.
    # 이제 뒷면은 측면 윤곽의 yb 로 간다 (x 단면만 대칭 가정, BACK_K)
    me.use_auto_smooth = True
    me.auto_smooth_angle = math.radians(25)
    for p in me.polygons:
        p.use_smooth = True
    print("PAD verts=%d faces=%d  판 선 %d/%d" % (len(me.vertices), len(me.polygons), n, len(LSEG)))
    return ob


def plant_horns(lean_max=1.0):
    """뿔을 어깨 돔 위에 심는다. **화면 투영 길이를 보존한다** —
    카메라 쪽으로 눕히면 투영이 짧아져서 원화 뿔 끝에 못 닿았다."""
    from mathutils import Matrix, Vector
    import numpy as np
    src = H + "/out/horns.blend"
    for o in [o for o in bpy.data.objects if o.name.startswith("horn")]:
        bpy.data.objects.remove(o, do_unlink=True)
    with bpy.data.libraries.load(src) as (s, d):
        d.objects = [n for n in s.objects if n.startswith("horn")]
    for o in d.objects:
        bpy.context.scene.collection.objects.link(o)
    for o in d.objects:
        co = np.array([v.co[:] for v in o.data.vertices])
        root = Vector(co[co[:, 2] <= co[:, 2].min() + 1e-4].mean(0))
        tip = Vector(co[co[:, 2] >= co[:, 2].max() - 1e-4].mean(0))
        t = ((root.x - B["cx"]) / B["ax"]) ** 2 + ((root.z - B["cz"]) / B["az"]) ** 2
        k = max(1.0 - t, 0.02) ** 0.5
        n = Vector(((root.x - B["cx"]) / B["ax"] ** 2, -k / B["ay"], (root.z - B["cz"]) / B["az"] ** 2))
        n.normalize()
        nscr = math.hypot(n.x, n.z)
        lean = max(-lean_max, min(lean_max, n.y / nscr)) if nscr > 1e-3 else -lean_max
        v = tip - root
        scr = math.hypot(v.x, v.z)
        if v.length < 1e-6 or scr < 1e-6:
            continue
        tgt = Vector((v.x, scr * lean, v.z))
        q = v.rotation_difference(tgt)
        # 회전은 길이를 보존한다 -> 화면 투영이 cos 만큼 줄어든다. 축으로 늘려서 되돌린다
        grow = tgt.length / scr
        ax = tgt.normalized()
        S = Matrix.Scale(grow, 4, ax)
        M = (Matrix.Translation(root) @ S @ q.to_matrix().to_4x4() @ Matrix.Translation(-root))
        o.data.transform(M)
        yd = B["cy"] - B["ay"] * k
        o.data.transform(Matrix.Translation(Vector((0, yd - root.y, 0))))
    print("뿔 %d개 심음 (화면 투영 보존)" % len(d.objects))


def shots(tag, with_horns=True):
    sc = bpy.context.scene
    sc.render.film_transparent = True
    for o in bpy.data.objects:
        show = o.name == "PAD" or (with_horns and o.name.startswith("horn"))
        o.hide_render = not show
        try:
            o.hide_set(not show)
        except Exception:
            pass
    for name, out in (("CAM_front", tag + "_front"), ("CAM_side", tag + "_side")):
        sc.camera = bpy.data.objects[name]
        sc.render.filepath = H + "/out/" + out + ".png"
        bpy.ops.render.render(write_still=True)
    c = bpy.data.objects["CAM_front"]
    c.location = (0.184 + 1.2 * math.sin(math.radians(40)), 0.027 - 1.2 * math.cos(math.radians(40)), 0.885)
    c.rotation_euler = (math.radians(90), 0, math.radians(40))
    c.data.ortho_scale = 0.30
    sc.camera = c
    sc.render.filepath = H + "/out/" + tag + "_q.png"
    bpy.ops.render.render(write_still=True)
    c.location = (0.0, -2.0, 0.5); c.rotation_euler = (math.radians(90), 0, 0); c.data.ortho_scale = 1.2


def scene():
    """원화 참조판 + 정규화 창과 같은 정사영 카메라. 이게 자다."""
    import math as _m
    def refplane(name, path, front):
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        me = bpy.data.meshes.new(name)
        vs = ([(-0.6, 0.30, -0.1), (0.6, 0.30, -0.1), (0.6, 0.30, 1.1), (-0.6, 0.30, 1.1)] if front
              else [(0.30, 0.6, -0.1), (0.30, -0.6, -0.1), (0.30, -0.6, 1.1), (0.30, 0.6, 1.1)])
        me.from_pydata(vs, [], [(0, 1, 2, 3)])
        uvl = me.uv_layers.new()
        for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
            uvl.data[i].uv = uv
        mat = bpy.data.materials.new("M_" + name)
        mat.use_nodes = True
        nt = mat.node_tree; nt.nodes.clear()
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path, check_existing=True)
        tex.interpolation = "Closest"
        em = nt.nodes.new("ShaderNodeEmission")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.hide_select = True; ob.hide_render = True
    refplane("REF_front", H + "/out/ref_front.png", True)
    refplane("REF_side", H + "/out/ref_side.png", False)
    for n, loc, rot in (("CAM_front", (0.0, -2.0, 0.5), (_m.radians(90), 0, 0)),
                        ("CAM_side", (2.0, 0.0, 0.5), (_m.radians(90), 0, _m.radians(90)))):
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
        c = bpy.data.objects.new(n, bpy.data.cameras.new(n))
        c.data.type = "ORTHO"; c.data.ortho_scale = 1.2       # 정규화 창 폭과 같다
        c.location = loc; c.rotation_euler = rot
        bpy.context.scene.collection.objects.link(c)
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    # 실측 어깨 타원체 (와이어 참조)
    if "REF_shoulder_dome" not in bpy.data.objects:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16,
                                             location=(B["cx"], B["cy"], B["cz"]))
        s = bpy.context.active_object
        s.name = "REF_shoulder_dome"
        s.scale = (B["ax"], B["ay"], B["az"])
        s.display_type = "WIRE"; s.hide_render = True


if __name__ == "__main__":
    import sys as _s
    out = _s.argv[_s.argv.index("--") + 1] if "--" in _s.argv else H + "/out/workbench.blend"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene()
    build()
    plant_horns(1.0)
    shots("pad", with_horns=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
    print("WORKBENCH OK -> %s" % out)
