# -*- coding: utf-8 -*-
"""**둘을 섞는다.** 배치는 잰 spec 이, 부피는 생성 모델이 준다.

    blender -b --factory-startup --python mix.py -- gate_spec.json out/mix.png

## 왜 섞나

각도 넷으로 보니 둘이 정반대로 틀렸다 —

    프리미티브   형태 O · 부피 X    정면은 문인데 옆에서 보면 무대 배경 판이다
    TripoSG      부피 O · 형태 X    닫집이 나왔지만 옆·뒤가 다 있고 일관된다

**TripoSG 가 만든 게 닫집(네 기둥 + 휜 지붕)인데, 그건 아케이드 한 칸의 모양이다.**
그래서 가운데 문은 프리미티브가 짓고, **양옆 열주를 그 닫집으로 채운다.**
허공에 뜬 상자 막대가 진짜 부피를 가진 칸으로 바뀐다.

## 손대는 것 둘

    바닥       16.5 m 짜리 판때기가 화면을 덮었다. 문 발치만 남긴다
    열주       상자 -> **닫집 복제**. 메시를 공유해 열넷을 놔도 가볍다

## 화각도 고친다

높이만 보고 거리를 잡았더니 바닥 판(16.5 m)이 화면을 덮었다.
**바운딩 박스 전체**로 잡는다.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, ARGV[0] if ARGV else "gate_spec.json")
DST = os.path.abspath(ARGV[1] if len(ARGV) > 1 else os.path.join(HERE, "out", "mix.png"))
TRI = os.path.join(HERE, "out", "tri", "gate_only.glb")
CEL = r"G:\art2motion\5_blender\cel.py"
FACES = 4000                      # 닫집 한 칸을 이만큼으로 줄인다. 203만은 못 쓴다

_g = open(os.path.join(HERE, "gate_build.py"), encoding="utf-8").read()
_ns = {"__file__": os.path.join(HERE, "gate_build.py"), "__name__": "gate_build",
       "ARGV": [], "SPEC": SPEC, "DST": "", "HERE": HERE}
exec(_g.split("\ndef probe():")[0].replace("\nmain()", ""), _ns)
build, mat, box = _ns["build"], _ns["mat"], _ns["box"]


def bay_mesh(target_faces=FACES):
    """생성 닫집을 한 칸으로 만든다. **면을 줄이고 세워서 원점에 놓는다.**"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=TRI)
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    o = max(new, key=lambda x: len(x.data.polygons))
    for x in new:
        if x is not o:
            bpy.data.objects.remove(x, do_unlink=True)
    o.location = (0, 0, 0)
    o.rotation_euler = (0, 0, 0)
    o.scale = (1, 1, 1)
    co = [v.co for v in o.data.vertices]
    ext = [max(c[i] for c in co) - min(c[i] for c in co) for i in range(3)]
    ax = ext.index(max(ext))
    if ax != 2:
        o.data.transform(Matrix.Rotation(math.radians(90), 4, 'X' if ax == 1 else 'Y'))
    m = o.modifiers.new("dec", 'DECIMATE')
    m.ratio = min(1.0, target_faces / float(len(o.data.polygons)))
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="dec")
    co = [v.co for v in o.data.vertices]
    o.data.transform(Matrix.Translation((
        -(max(c.x for c in co) + min(c.x for c in co)) / 2.0,
        -(max(c.y for c in co) + min(c.y for c in co)) / 2.0,
        -min(c.z for c in co))))
    o.data.update()
    co = [v.co for v in o.data.vertices]
    h = max(c.z for c in co) - min(c.z for c in co)
    o.name = "bay_src"
    return o, h


def frame_all(cam, aim_z, lens=32):
    """**바운딩 박스로** 거리를 잡는다. 높이만 보면 넓은 바닥에 화면이 먹힌다."""
    pts = [o.matrix_world @ v.co for o in bpy.data.objects
           if o.type == 'MESH' for v in o.data.vertices]
    xs = [p.x for p in pts]
    zs = [p.z for p in pts]
    ys = [p.y for p in pts]
    w = max(xs) - min(xs)
    h = max(zs) - min(zs)
    sc = bpy.context.scene
    ar = sc.render.resolution_x / float(sc.render.resolution_y)
    need = max(h, w / max(ar, 1e-6))                  # 세로 기준 센서
    d = need / (2.0 * math.tan(math.radians(0.5 * 2 * math.degrees(
        math.atan(18.0 / lens))))) * 1.15
    return d + (max(ys) - min(ys)) * 0.5


def main():
    spec = json.load(open(SPEC, encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    gold = mat("gold", (0.94, 0.82, 0.26), 0.35)
    build(spec, gold)

    # 상자 열주와 거대 바닥을 걷는다 — 옆에서 보면 이 둘이 그림을 망친다
    for o in list(bpy.data.objects):
        if o.name.startswith(("pier", "lintel", "bal", "bnet", "bband", "floor", "fray")):
            bpy.data.objects.remove(o, do_unlink=True)

    W, H = spec["size_px"]
    Hm = spec["height_m"]["v"]
    wpp = Hm / float(H)
    fz = (1.0 - spec["floor"]["v"]) * Hm
    box("plinth", (W * wpp * 0.55, W * wpp * 0.45, Hm * 0.02),
        (0.0, -W * wpp * 0.10, fz), gold)             # 문 발치만

    # **입구를 막는다.** 원화는 「입구는 순수한 검정」인데 뚫려 있으면 배경이 비친다.
    # 판을 3D 로 넣어야 각도가 바뀌어도 따라온다 — 합성으로 칠하면 정면에서만 맞는다
    prof = spec["arch"]["profile"]
    hw = max(pr[1] for pr in prof) * W * wpp
    top_z = (1.0 - spec["arch"]["top"]) * Hm
    bot_z = (1.0 - spec["arch"]["bottom"]) * Hm
    dark = mat("void", (0.010, 0.009, 0.018), 1.0)
    # 사각 판으로 뒀더니 뒤에서 볼 때 문을 통째로 가렸다.
    # **잰 프로필 그대로 아치 모양**으로 만들고 문 평면에 얇게 세운다
    def z_of(t):
        return top_z + (bot_z - top_z) * t
    loop = [(-pr[1] * W * wpp, z_of(pr[0])) for pr in prof[::-1]]
    loop += [(pr[1] * W * wpp, z_of(pr[0])) for pr in prof]
    _ns["ribbon"]("gate_void", loop, spec["thickness_m"]["v"] * 0.30, dark)

    src, bh = bay_mesh()
    # **재질을 갈아끼운다.** 임포트한 흰 재질 그대로 두니 금 문 옆에 천막이 섰다
    src.data.materials.clear()
    src.data.materials.append(gold)
    bay = spec["bay"]
    # 0.62 로 뒀더니 문 옆에서 작아 보였다. **아치 높이만큼** 키워 열주로 세운다
    scale = (spec["arch"]["bottom"] - spec["arch"]["top"]) * Hm * 1.15 / bh
    x = W * wpp * 0.42
    n = 0
    for k in range(bay["n"]):
        y = -bay["spacing_m"] * (k + 0.6)
        for s in (-1.0, 1.0):
            o = bpy.data.objects.new("bay%d_%d" % (k, s > 0), src.data)   # 메시 공유
            bpy.context.scene.collection.objects.link(o)
            o.location = (s * x, y, fz)
            o.scale = (scale, scale, scale)
            o.rotation_euler = (0, 0, math.radians(90 * s))
            n += 1
    bpy.data.objects.remove(src, do_unlink=True)

    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 360, 640
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.028, 0.032, 0.070, 1.0)
    bpy.ops.object.light_add(type='SUN', location=(6, -20, 18))
    sun = bpy.context.object
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.92, 0.72)
    sun.rotation_euler = (0.80, 0.0, 0.35)
    BG = ARGV[ARGV.index("--bg") + 1] if "--bg" in ARGV else None
    if BG:
        sc.render.film_transparent = True          # 뒤를 비우고 굽는다
    cd = bpy.data.cameras.new("cam")
    cd.lens = 32
    cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    ns = {"__file__": CEL, "__name__": "cel"}
    exec(open(CEL, encoding="utf-8").read().split("\ndef main():")[0], ns)
    ns["cel"](sc)

    # **시점을 바닥으로 내린다.** 원화(`r6_gate_low`)도 배경판도 밑에서 올려본 것이라,
    # 카메라를 눈높이에 두면 배경만 올려본 그림이 되어 앞뒤가 안 맞는다.
    # 낮추면 문이 솟고, 열주 사이로 하늘이 보여 하늘 0.00 도 풀린다
    aim = Vector((0.0, -bay["spacing_m"] * bay["n"] * 0.25, Hm * 0.88))
    d = frame_all(cam, aim.z) * 0.62
    outs = []
    for i in range(4):
        a = 2.0 * math.pi * i / 4
        loc = Vector((math.sin(a) * d, -math.cos(a) * d, Hm * 0.11)) + Vector((0, aim.y, 0))
        cam.location = loc
        cam.rotation_mode = 'QUATERNION'
        cam.rotation_quaternion = (aim - loc).to_track_quat('-Z', 'Y')
        p = DST.replace(".png", "_%d.png" % i)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)

    ims = [bpy.data.images.load(p) for p in outs]
    w, hh = ims[0].size
    if BG:
        # **배경판을 뒤에 깐다.** 하늘이 화면의 절반이던 게 여기서 채워진다.
        # 각도 넷에 같은 판을 쓰는 건 옳지 않지만(원근이 안 따라온다) 정면 판정용이다
        bg = bpy.data.images.load(BG)
        # **흐리게** — 반으로 줄였다 늘리면 디테일이 뭉개져 뒤로 물러난다 (공기원근)
        bg.scale(max(8, w // 3), max(8, hh // 3))   # 1/5 는 너무 뭉갰다 — 밀도가 96 -> 51
        bg.scale(w, hh)
        SKY = (0.028, 0.032, 0.070)
        FAR = 0.62                                  # 0.42 는 「먼 성당」이 아니라 「어두운 벽」이었다
        bp = list(bg.pixels)
        for i in range(0, len(bp), 4):
            g = (bp[i] + bp[i + 1] + bp[i + 2]) / 3.0
            for c in range(3):
                v = bp[i + c] * 0.45 + g * 0.55     # 채도를 죽인다
                bp[i + c] = v * FAR + SKY[c] * (1.0 - FAR)
        for im in ims:
            px = list(im.pixels)
            for i in range(0, len(px), 4):
                a = px[i + 3]
                for c in range(3):
                    px[i + c] = px[i + c] * a + bp[i + c] * (1.0 - a)
                px[i + 3] = 1.0
            im.pixels = px
    out = bpy.data.images.new("sheet", width=w * len(ims), height=hh)
    buf = [0.0] * (w * len(ims) * hh * 4)
    for k, im in enumerate(ims):
        px = list(im.pixels)
        for yy in range(hh):
            s0 = yy * w * 4
            t0 = (yy * w * len(ims) + k * w) * 4
            buf[t0:t0 + w * 4] = px[s0:s0 + w * 4]
    out.pixels = buf
    out.filepath_raw = DST
    out.file_format = 'PNG'
    out.save()
    print("MIX 칸 %d · 거리 %.1f m · 물체 %d -> %s"
          % (n, d, len(bpy.data.objects), DST))


main()
