# -*- coding: utf-8 -*-
"""**부품마다 따로 짓는다.** 날 · 가드 · 자루 · 자루끝이 각각 제 색과 제 각을 갖는다.

    blender -b --factory-startup --python 무기짓기2.py -- 무기부품.json out/무기부품.png [--len 2.4] [--n 8]

## 1차 빌더와 뭐가 다른가

`무기짓기.py` 는 무기 하나를 **한 줄기로** 훑었다. 그러면 —

    가드가 혹이 된다        날과 이어 붙어서 각이 안 선다
    색이 하나다             은날에 금가드를 못 준다
    칸 24개로는 가드를 놓친다  가드는 길이의 3% 다

여기서는 `무기분할.py` 가 나눈 부품마다 **따로 솔리드**를 만든다.
부품 사이는 안 잇는다 — 겹쳐 놓으면 셀 먹선이 경계를 그려준다.

## 단면은 부품마다 다르다

    날      마름모 (양쪽에 날이 선다). 두께비는 잰 값
    가드    납작한 상자에 가깝게 (가로로 길다)
    자루    거의 원형 (손이 쥐는 것)

이것도 지어낸 게 아니라 **옆모습 판이 그렇게 말한다** — 날은 선처럼 얇고
가드만 옆으로 튀어나온다.
"""
import json
import math
import os
import sys

import bmesh
import bpy

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, ARGV[0] if ARGV else "무기부품.json")
DST = os.path.abspath(ARGV[1] if len(ARGV) > 1 else os.path.join(HERE, "out", "무기부품.png"))
LEN = float(ARGV[ARGV.index("--len") + 1]) if "--len" in ARGV else 2.4
NW = int(ARGV[ARGV.index("--n") + 1]) if "--n" in ARGV else 8
CEL = r"G:\art2motion\5_blender\cel.py"
THICK = 0.313                 # measured — 무기2.json 두께비

# 부품마다 단면 납작함 (두께 / 폭). 날은 얇고 자루는 둥글다
FLAT = {"날": 1.0, "날장식": 1.0, "가드": 0.55, "자루": 2.6, "자루장식": 2.2, "자루끝": 1.6}


def mat(name, rgb, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = tuple(rgb) + (1.0,)
    p.inputs["Roughness"].default_value = rough
    return m


def part(name, prof, z0, z1, material, flat):
    """부품 하나. **끝이 0 이 아니면 막는다** — 부품은 잘린 토막이라 뚜껑이 필요하다."""
    if len(prof) < 2 or max(prof) <= 0:
        return None
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    n = len(prof)
    rings = []
    for i, hw in enumerate(prof):
        z = z0 + (z1 - z0) * i / (n - 1.0)
        w = hw * LEN
        if w < 1e-5:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        t = w * THICK * flat
        rings.append([bm.verts.new((w, 0.0, z)),
                      bm.verts.new((w * 0.35, t, z)),
                      bm.verts.new((0.0, t, z)),
                      bm.verts.new((-w * 0.35, t, z)),
                      bm.verts.new((-w, 0.0, z)),
                      bm.verts.new((-w * 0.35, -t, z)),
                      bm.verts.new((0.0, -t, z)),
                      bm.verts.new((w * 0.35, -t, z))])
    for i in range(n - 1):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1 or len(b) == 1:
            one, many = (a[0], b) if len(a) == 1 else (b[0], a)
            for k in range(len(many)):
                bm.faces.new((one, many[k], many[(k + 1) % len(many)]))
        else:
            for k in range(8):
                bm.faces.new((a[k], a[(k + 1) % 8], b[(k + 1) % 8], b[k]))
    for r in (rings[0], rings[-1]):
        if len(r) > 2:
            bm.faces.new(r)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    return ob


def main():
    spec = json.load(open(SPEC, encoding="utf-8"))
    ws = spec["무기"][:NW]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = {}

    def mat_for(col):
        k = tuple(round(v, 3) for v in col)
        if k not in mats:
            mats[k] = mat("m%d" % len(mats), col, 0.5 if max(col) > 0.8 else 0.7)
        return mats[k]

    widest = max(max(max(p["반폭"]) for p in w["부품"]) for w in ws)
    gap = LEN * widest * 3.0
    nparts = 0
    for i, w in enumerate(ws):
        x = (i - (len(ws) - 1) / 2.0) * gap
        for p in w["부품"]:
            o = part("%02d_%s" % (i, p["이름"]), p["반폭"], LEN * p["t0"], LEN * p["t1"],
                     mat_for(p["색"]), FLAT.get(p["이름"], 1.0))
            if o:
                o.location.x = x
                nparts += 1

    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1280, 700
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.028, 0.032, 0.070, 1.0)
    bpy.ops.object.light_add(type='SUN', location=(6, -20, 18))
    s = bpy.context.object
    s.data.energy = 3.0
    s.data.color = (1.0, 0.92, 0.72)
    s.rotation_euler = (0.80, 0.0, 0.35)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 50
    cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    pts = [o.matrix_world @ v.co for o in bpy.data.objects
           if o.type == 'MESH' for v in o.data.vertices]
    W = max(p.x for p in pts) - min(p.x for p in pts)
    H = max(p.z for p in pts) - min(p.z for p in pts)
    ar = sc.render.resolution_x / float(sc.render.resolution_y)
    need = max(H, W / ar)
    d = need / (2.0 * math.tan(math.atan(12.0 / cd.lens))) * 1.12
    cam.location = (0.0, -d, H * 0.5)
    cam.rotation_euler = (math.radians(90), 0, 0)
    ns = {"__file__": CEL, "__name__": "cel"}
    exec(open(CEL, encoding="utf-8").read().split("\ndef main():")[0], ns)
    ns["cel"](sc)
    sc.render.filepath = DST
    bpy.ops.render.render(write_still=True)
    print("PARTS %d 자루 · 부품 %d 개 · 재질 %d -> %s"
          % (len(ws), nparts, len(mats), DST))


main()
