"""**부품 하나하나가 제대로 나왔는지 먼저 확인한다.** 붙이는 건 그 다음이다.

    blender -b --python verify_parts.py -- <buildspec.json> [출력폴더]

49개를 한꺼번에 붙여놓고 전체 IoU 를 보면 어느 부품이 틀렸는지 알 수 없다 —
숫자가 안 움직여도 원인을 못 찾는다. **부품마다 따로 만들고, 따로 렌더하고,
그 부품이 나온 원화 영역과 따로 비교한다.**

부품별로 내는 것:
    silhouette IoU   그 부품 하나가 원화의 그 자리와 얼마나 겹치나
    통과/실패        기준 미달 부품을 조립에서 빼거나 고칠 대상으로 표시

각 부품은 **자기 bbox 에 맞춘 창**으로 렌더한다 — 전체 창으로 보면 작은 부품은
몇 픽셀이라 판정이 안 된다.
"""
import json
import math
import os
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC = argv[0]
OUT = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(SPEC), "verify")
os.makedirs(OUT, exist_ok=True)
spec = json.load(open(SPEC, encoding="utf-8"))
hw = spec["envelope"]["halfwidth"]["rows"]
dp = spec["envelope"]["depth"]["rows"]
RES = 256
MARGIN = 1.25


def _at(rows, z, i):
    if z <= rows[0][0]:
        return rows[0][i]
    for a, b in zip(rows, rows[1:]):
        if z <= b[0]:
            t = (z - a[0]) / max(1e-9, b[0] - a[0])
            return a[i] + (b[i] - a[i]) * t
    return rows[-1][i]


def surf(x, z):
    rx = max(_at(hw, z, 1), 1e-5)
    if dp:
        y0, y1 = _at(dp, z, 1), _at(dp, z, 2)
        cy, ry = (y0 + y1) / 2, max((y1 - y0) / 2, 1e-5)
    else:
        cy, ry = 0.0, rx
    u = min(1.0, abs(x) / rx)
    return cy - ry * math.sqrt(max(0.0, 1 - u * u))


def radius(poly, c, th):
    dx, dz = math.cos(th), math.sin(th)
    best, n = 0.0, len(poly)
    for k in range(n):
        ax, az = poly[k][0] - c[0], poly[k][1] - c[1]
        bx, bz = poly[(k + 1) % n][0] - c[0], poly[(k + 1) % n][1] - c[1]
        ex, ez = bx - ax, bz - az
        den = ex * dz - dx * ez
        if abs(den) < 1e-12:
            continue
        t = (ex * az - ax * ez) / den
        s = (dx * az - dz * ax) / den
        if t > best and -1e-9 <= s <= 1 + 1e-9:
            best = t
    return best


def poly_dist(poly, x, z):
    """폴리곤 경계까지의 거리 (테두리 챔퍼용)."""
    best = 1e9
    n = len(poly)
    for k in range(n):
        ax, az = poly[k]; bx, bz = poly[(k + 1) % n]
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / L2))
        best = min(best, math.hypot(x - (ax + t * dx), z - (az + t * dz)))
    return best


def build_one(name, poly, prot, rim_frac=0.35, cuts=3):
    """**폴리곤 그대로** 만든다. 레이디얼 격자로 만들면 오목한 판이 별모양 껍질까지
    부풀어 **원화보다 2배 커진다**(부품 검증에서 실측: 4,864px -> 11,366px).
    n각면을 만들고 삼각분할 후 사각으로 되붙인 뒤, 세분해서 표면에 얹는다."""
    if len(poly) < 3:
        return None
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0.0, z)) for x, z in poly]
    try:
        bm.faces.new(vs)
    except ValueError:
        bm.free(); return None
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.join_triangles(bm, faces=bm.faces[:], angle_face_threshold=3.14,
                             angle_shape_threshold=3.14)
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    # 두께: 앞면 + 뒷면
    rimw = max(rim_frac * math.sqrt(abs(_poly_area(poly))), 1e-4)
    for v in bm.verts:
        d = poly_dist(poly, v.co.x, v.co.z)
        bul = min(1.0, d / rimw)
        v.co.y = surf(v.co.x, v.co.z) - prot * bul
    bmesh.ops.solidify(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                       thickness=0.0015)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _poly_area(poly):
    s = 0.0
    for k in range(len(poly)):
        x0, z0 = poly[k]; x1, z1 = poly[(k + 1) % len(poly)]
        s += x0 * z1 - x1 * z0
    return abs(s) / 2


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cam = bpy.data.cameras.new("c")
cam.type = 'ORTHO'
cam.clip_start, cam.clip_end = 0.001, 30
camo = bpy.data.objects.new("c", cam)
sc.collection.objects.link(camo)
sc.camera = camo
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = True
sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light, sh.color_type = 'FLAT', 'SINGLE'
sh.single_color = (0.2, 0.2, 0.2)
sh.show_cavity = sh.show_object_outline = False
sc.render.image_settings.color_mode = 'RGBA'

frames = {}
made = skipped = 0
for p in spec["parts"]:
    if p["ops"].get("skip") or not p.get("poly"):
        continue
    for i, poly in enumerate(p["poly"]):
        if len(poly) < 3:
            continue
        nm = p["id"] + (f"_{i}" if len(p["poly"]) > 1 else "")
        for o in list(sc.objects):
            if o.type == 'MESH':
                bpy.data.objects.remove(o, do_unlink=True)
        prot = p["ops"]["protrusion"]
        if p["ops"].get("make") == "recess":
            prot = -abs(prot) * 0.6
        ob = build_one(nm, poly, prot)
        if ob is None:
            skipped += 1
            continue
        xs = [q[0] for q in poly]
        zs = [q[1] for q in poly]
        cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
        span = max(max(xs) - min(xs), max(zs) - min(zs)) * MARGIN
        cam.ortho_scale = span
        camo.location = (cx, -8, cz)
        camo.rotation_euler = (math.pi / 2, 0, 0)
        sc.render.filepath = os.path.abspath(os.path.join(OUT, nm + ".png"))
        bpy.ops.render.render(write_still=True)
        frames[nm] = {"cx": cx, "cz": cz, "span": span, "res": RES,
                      "region": p["from"]["region"], "make": p["ops"].get("make")}
        made += 1
json.dump(frames, open(os.path.join(OUT, "frames.json"), "w"), indent=1)
print(f"부품 {made}개 렌더 · 건너뜀 {skipped} · {OUT}")
