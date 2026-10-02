# -*- coding: utf-8 -*-
"""3-6 · 3-7 타원체 둘이 서로 꿰뚫으면 만나는 곳마다 오목한 주름(흰 점선).
blender -b -P 3-6_3-7.py 로 렌더 + 주름 좌표(json) → python 3-6_3-7.py 로 점선 · 화살표 → ../3-6.png (매끈 · 진회색) · ../3-7.png (각진 면 · 밝은 회색)"""
import sys, os, math, json
try:
    import bpy, mathutils
    from bpy_extras.object_utils import world_to_camera_view
    sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
except ImportError: bpy = None
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, Hh = 1920, 1080

def ell(name, loc, scale, rot, col, seg, smooth):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=loc, rotation=[math.radians(a) for a in rot])
    o = bpy.context.object; o.name = name; o.scale = scale; o.color = col
    for p in o.data.polygons: p.use_smooth = smooth
    return o

def make(out, col, seg, smooth):
    sc = H.scene(res=(W, Hh), transparent=False, cavity=False); sc.world.color = (1, 1, 1)
    sc.view_settings.view_transform = "Standard"; sc.display.shading.light = "STUDIO"
    A = ((0.75, 0.38, 1.35), (0, -15, 8)); B = ((2.1, 1.05, 0.62), (12, 0, 22))
    ell("A1", (-4.3, 0, 1.9), *A, col, seg, smooth); ell("B1", (-4.0, 0, -1.9), *B, col, seg, smooth)
    a = ell("A2", (3.6, 0, 0.75), *A, col, seg, smooth); b = ell("B2", (3.9, 0, -0.75), *B, col, seg, smooth)
    H.look((0, 0, 0), 0, 18, ortho=14.5, dist=40)
    bpy.context.view_layer.update()
    path = os.path.join(D, out); H.shot(path)
    # 만나는 고리: A 의 자오선마다 위에서 내려가며 B 안으로 들어가는 점
    Mi = b.matrix_world.inverted(); Ma = a.matrix_world
    inB = lambda p: (Mi @ p).length < 1
    loop = []
    for k in range(240):
        t = 2 * math.pi * k / 240
        P = lambda f: Ma @ mathutils.Vector((math.sin(f) * math.cos(t), math.sin(f) * math.sin(t), math.cos(f)))
        lo, hi = 0.0, math.pi
        if not inB(P(hi)): continue
        for _ in range(40):
            m = (lo + hi) / 2
            if inB(P(m)): hi = m
            else: lo = m
        loop.append(P(hi))
    cam = sc.camera; dg = bpy.context.evaluated_depsgraph_get(); back = cam.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, 1))
    px = []
    for p in loop:
        ok, hit, *_ = sc.ray_cast(dg, p + back * 30, -back)
        vis = ok and (hit - p).length < 0.06
        c = world_to_camera_view(sc, cam, p); px.append(((c.x * W, (1 - c.y) * Hh), vis))
    assert sum(v for _, v in px) > 20, "보이는 주름 점이 너무 적다"
    json.dump(px, open(path + ".json", "w"))

def draw(out):
    from PIL import Image, ImageDraw
    path = os.path.join(D, out); px = json.load(open(path + ".json"))
    im = Image.open(path).convert("RGB"); dr = ImageDraw.Draw(im); s = 0
    for (p, v), (q, w) in zip(px, px[1:] + px[:1]):
        if v and w and int(s // 14) % 2 == 0: dr.line([tuple(p), tuple(q)], fill=(255, 255, 255), width=6)
        s += math.dist(p, q)
    y0 = Hh // 2 - 40   # 가운데 겹화살표
    for dy in (-12, 12): dr.line([(820, y0 + dy), (1080, y0 + dy)], fill=(0, 0, 0), width=5)
    dr.line([(1060, y0 - 34), (1100, y0)], fill=(0, 0, 0), width=5); dr.line([(1060, y0 + 34), (1100, y0)], fill=(0, 0, 0), width=5)
    im.save(path); os.remove(path + ".json")

if bpy:
    make("3-6.png", (0.42, 0.42, 0.44, 1), 96, True)
    make("3-7.png", (0.86, 0.86, 0.88, 1), 24, False)
else:
    draw("3-6.png"); draw("3-7.png")
