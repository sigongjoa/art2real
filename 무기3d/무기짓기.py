# -*- coding: utf-8 -*-
"""**잰 프로필을 축 따라 훑어서 무기를 세운다.**

    blender -b --factory-startup --python 무기짓기.py -- 무기.json out/무기.png [--len 2.4]

## 형태 지식이 필요 없다

크로켓이 「말린 잎사귀」인 걸 몰라도 윤곽만 알면 짓는다는 게 조사의 결론이었다
(`건축3d/research_형태속성` — 일반화 원기둥: **축 + 축을 따라 변하는 단면**).
무기도 같다. `무기재기.py` 가 준 건 축 따라의 반폭 20점이고,
여기서는 그 반폭에 **단면 하나**를 곱해서 고리를 만들고 위아래를 잇는다.

    반폭 프로필   원화에서 잰 것 (measured)
    단면          마름모 — 날은 가운데가 두껍고 양날이 얇다 (guessed, 옆모습 원화가 없다)
    두께 비       폭의 0.22 (guessed)

## 자루는 따로다

원화의 프로필에는 자루까지 들어 있다(밑동이 다시 좁아지는 게 그것이다).
그래서 **자루를 새로 안 붙인다** — 프로필이 이미 자루를 말하고 있다.
가드만 표본 수가 많은 종류에 얹는다.
"""
import json
import math
import os
import sys

import bmesh
import bpy

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, ARGV[0] if ARGV else "무기.json")
DST = os.path.abspath(ARGV[1] if len(ARGV) > 1 else os.path.join(HERE, "out", "무기.png"))
LEN = float(ARGV[ARGV.index("--len") + 1]) if "--len" in ARGV else 2.4
CEL = r"G:\art2motion\5_blender\cel.py"
SEC = 8                       # 단면 꼭짓점 수. 셀은 각져야 선이 산다
THICK = 0.22                  # 두께 / 폭. guessed


def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = tuple(rgb) + (1.0,)
    p.inputs["Roughness"].default_value = rough
    return m


def sweep(name, prof, length, material, thick=THICK, sec=SEC):
    """반폭 프로필 -> 솔리드. **칸마다 고리를 놓고 이웃 고리를 면으로 잇는다.**

    단면은 마름모(가운데가 두껍다). 반폭이 0 인 칸은 한 점으로 모아 끝을 뾰족하게 한다."""
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    n = len(prof)
    rings = []
    for i, hw in enumerate(prof):
        z = length * i / (n - 1.0)
        w = hw * length
        if w < 1e-5:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        # **진짜 마름모.** cos/sin 팔각으로 돌렸더니 날 끝이 둥글게 깎여
        # 검이 아니라 물레 기둥이 됐다. 날은 **x 끝에서 두께가 0** 이어야 선다
        t = w * thick
        ring = [bm.verts.new((w, 0.0, z)),          # 오른쪽 날
                bm.verts.new((w * 0.35, t, z)),
                bm.verts.new((0.0, t, z)),          # 등 (가운데가 제일 두껍다)
                bm.verts.new((-w * 0.35, t, z)),
                bm.verts.new((-w, 0.0, z)),         # 왼쪽 날
                bm.verts.new((-w * 0.35, -t, z)),
                bm.verts.new((0.0, -t, z)),
                bm.verts.new((w * 0.35, -t, z))]
        rings.append(ring)
    for i in range(n - 1):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1 or len(b) == 1:
            one, many = (a[0], b) if len(a) == 1 else (b[0], a)
            for k in range(len(many)):
                bm.faces.new((one, many[k], many[(k + 1) % len(many)]))
        else:
            for k in range(sec):
                bm.faces.new((a[k], a[(k + 1) % sec], b[(k + 1) % sec], b[k]))
    for ring in (rings[0], rings[-1]):             # 뚫린 끝을 막는다
        if len(ring) > 2:
            bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    return ob


def guard(name, w, z, material):
    """가드. 표본이 많은 종류에만 얹는다 — 원화의 바늘 날 다수는 가드가 안 보인다."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z))
    o = bpy.context.object
    o.name = name
    o.scale = (w * 2.6, w * 1.1, w * 0.5)
    o.data.materials.append(material)
    return o


def main():
    spec = json.load(open(SPEC, encoding="utf-8"))
    ws = spec["무기"]
    # **두께를 spec 에서 읽는다.** 0.22 는 내가 지어낸 값이었고, 이제 잰 값이 있다
    global THICK
    if spec.get("두께비", {}).get("v"):
        THICK = float(spec["두께비"]["v"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    gold = mat("gold", (0.94, 0.82, 0.26), 0.35)
    hilt = mat("hilt", (0.42, 0.28, 0.08), 0.8)
    # **보구마다 색이 다르다.** 원화 판에서 잰 날색·자루색을 그대로 쓴다 —
    # 은날에 금가드, 금날에 흰자루처럼 갈려 있어서 지어낼 필요가 없다
    for w in ws:
        if w.get("날색"):
            w["_m"] = mat("blade%d" % w["종류"], tuple(w["날색"]), 0.30)
        if w.get("자루색"):
            w["_h"] = mat("grip%d" % w["종류"], tuple(w["자루색"]), 0.75)

    # 0.30 으로 뒀더니 넓은 날끼리 겹쳤다. **제일 넓은 날**을 기준으로 벌린다
    gap = LEN * max(max(w["반폭"]) for w in ws) * 2.6
    for i, w in enumerate(ws):
        o = sweep("w%02d" % w["종류"], w["반폭"], LEN, w.get("_m", gold))
        o.location.x = (i - (len(ws) - 1) / 2.0) * gap
        if w["표본"] >= 3:                          # 자주 쓴 것에만 가드
            g = guard("g%02d" % w["종류"], max(w["반폭"]) * LEN, LEN * 0.10,
                      w.get("_h", hilt))
            g.location.x = o.location.x

    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1280, 620
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
    # **센서 맞춤을 세로로.** AUTO 로 두면 가로 화면에서 가로에 맞춰서,
    # 세로 공식으로 거리를 잡으면 위아래가 잘린다 (그렇게 두 번 잘렸다)
    cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    # **바운딩 박스로 잡는다.** 폭만 보거나 높이만 보면 한쪽이 잘린다
    pts = [o.matrix_world @ v.co for o in bpy.data.objects
           if o.type == 'MESH' for v in o.data.vertices]
    W = max(p.x for p in pts) - min(p.x for p in pts)
    H = max(p.z for p in pts) - min(p.z for p in pts)
    ar = sc.render.resolution_x / float(sc.render.resolution_y)
    need = max(H, W / ar)
    # 센서 **세로는 24mm** 라 절반이 12 다. 18(가로 36의 절반)로 뒀더니 또 잘렸다
    d = need / (2.0 * math.tan(math.atan(12.0 / cd.lens))) * 1.12
    cam.location = (0.0, -d, H * 0.5)
    cam.rotation_euler = (math.radians(90), 0, 0)
    ns = {"__file__": CEL, "__name__": "cel"}
    exec(open(CEL, encoding="utf-8").read().split("\ndef main():")[0], ns)
    ns["cel"](sc)
    sc.render.filepath = DST
    bpy.ops.render.render(write_still=True)
    print("WEAPONS %d 자루 · 면 %d · 길이 %.1f m -> %s"
          % (len(ws), sum(len(o.data.polygons) for o in bpy.data.objects
                          if o.type == 'MESH'), LEN, DST))


main()
