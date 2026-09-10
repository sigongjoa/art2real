# -*- coding: utf-8 -*-
"""**지은 것을 여러 각도에서 본다.** 한 각도만 보면 판인지 부피인지 모른다.

    blender -b --factory-startup --python look.py -- <파일.blend|.glb> <나갈.png> [--h 11] [--n 4]

정면만 보고 「됐다」 했다가 3/4 에서 종이 오린 것이 드러난 적이 있다(`gate_model.py`).
그래서 **정면·3/4·옆·뒤** 넷을 한 장에 붙인다.

셀 먹선은 `G:\\art2motion\\5_blender\\cel.py` 를 그대로 쓴다 — 편과 같은 화면으로 봐야
편에 걸었을 때 어떻게 보일지 안다.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = ARGV[0], os.path.abspath(ARGV[1])
HGT = float(ARGV[ARGV.index("--h") + 1]) if "--h" in ARGV else 11.0
N = int(ARGV[ARGV.index("--n") + 1]) if "--n" in ARGV else 4
CEL = r"G:\art2motion\5_blender\cel.py"
RES = (360, 640)


def load(src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if src.lower().endswith(".blend"):
        with bpy.data.libraries.load(src) as (a, b):
            b.objects = list(a.objects)
        for o in b.objects:
            if o is not None:
                bpy.context.scene.collection.objects.link(o)
    elif src.lower().endswith((".glb", ".gltf")):
        bpy.ops.import_scene.gltf(filepath=src)
    else:
        bpy.ops.wm.obj_import(filepath=src)
    return [o for o in bpy.data.objects if o.type == 'MESH']


def stand(obs, height):
    """**긴 축을 세우고 높이를 맞춘다.** 생성 모델은 눕혀서 나오는 게 보통이다."""
    co = [v.co for o in obs for v in o.data.vertices]
    ext = [max(c[i] for c in co) - min(c[i] for c in co) for i in range(3)]
    ax = ext.index(max(ext))
    if ax != 2:
        R = Matrix.Rotation(math.radians(90), 4, 'X' if ax == 1 else 'Y')
        for o in obs:
            o.data.transform(R)
    co = [v.co for o in obs for v in o.data.vertices]
    h = max(c.z for c in co) - min(c.z for c in co)
    S = Matrix.Scale(height / max(h, 1e-6), 4)
    for o in obs:
        o.data.transform(S)
    co = [v.co for o in obs for v in o.data.vertices]
    T = Matrix.Translation((-(max(c.x for c in co) + min(c.x for c in co)) / 2.0,
                            -(max(c.y for c in co) + min(c.y for c in co)) / 2.0,
                            -min(c.z for c in co)))
    for o in obs:
        o.data.transform(T)
        o.data.update()
    return h


def world(sc):
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.028, 0.032, 0.070, 1.0)
    bpy.ops.object.light_add(type='SUN', location=(6, -20, 18))
    s = bpy.context.object
    s.data.energy = 3.0
    s.data.color = (1.0, 0.92, 0.72)
    s.rotation_euler = (0.80, 0.0, 0.35)


def main():
    obs = load(SRC)
    assert obs, SRC
    h = stand(obs, HGT)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = RES
    world(sc)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 32
    cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    src = open(CEL, encoding="utf-8").read()
    ns = {"__file__": CEL, "__name__": "cel"}
    exec(src.split("\ndef main():")[0], ns)
    ns["cel"](sc)

    d = HGT * 1.55                                 # 높이 전체가 들어오는 거리
    aim = Vector((0.0, 0.0, HGT * 0.45))
    outs = []
    for i in range(N):
        a = 2.0 * math.pi * i / N
        loc = Vector((math.sin(a) * d, -math.cos(a) * d, HGT * 0.42))
        cam.location = loc
        cam.rotation_mode = 'QUATERNION'
        cam.rotation_quaternion = (aim - loc).to_track_quat('-Z', 'Y')
        p = DST.replace(".png", "_%d.png" % i)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)
    tile(outs, DST)
    print("LOOK %s  물체 %d · 원 높이 %.2f -> %.1f m · %d 각도 -> %s"
          % (os.path.basename(SRC), len(obs), h, HGT, N, DST))


def tile(paths, dst):
    """넷을 가로로 붙인다. 블렌더 안에서 하려고 이미지 API 를 쓴다."""
    ims = [bpy.data.images.load(p) for p in paths]
    w, hh = ims[0].size
    out = bpy.data.images.new("sheet", width=w * len(ims), height=hh)
    buf = [0.0] * (w * len(ims) * hh * 4)
    for k, im in enumerate(ims):
        px = list(im.pixels)
        for y in range(hh):
            s = y * w * 4
            t = (y * w * len(ims) + k * w) * 4
            buf[t:t + w * 4] = px[s:s + w * 4]
    out.pixels = buf
    out.filepath_raw = dst
    out.file_format = 'PNG'
    out.save()


main()
