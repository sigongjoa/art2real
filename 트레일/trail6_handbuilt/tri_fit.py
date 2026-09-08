# -*- coding: utf-8 -*-
"""생성 메시의 **방향과 배율을 눈이 아니라 IoU 로** 정한다.

    blender -b --python tri_fit.py

turntable 을 눈으로 보고 -90 도라고 찍었던 게 틀렸다. z 회전 4가지 x 배율 기준 2가지를
전부 찍어 원화 마스크와 실루엣 IoU 를 재고 제일 높은 것을 고른다.

원화 마스크: panels.json 의 lav+gold 판 전부 (= 견갑 + 뿔), 10,163 화소.
"""
import bpy, os, sys, math
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "out", "tri_pauldron.glb")
MASK = os.path.join(HERE, "out", "_mask_pauldron.png")
RES = 1024
# 원화 견갑+뿔 실측 상자 (마스크에서 잰 것)
X0, X1, Z0, Z1 = 0.1179, 0.2504, 0.7856, 0.9850
CY = 0.027


def load_mesh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB)
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.objects.active = obs[0]
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    base = np.array([v.co[:] for v in o.data.vertices])
    return o, base


def place(o, base, az, mode):
    """z 로 az 도 돌리고, mode 기준으로 한 배율만 준 뒤 정면 bbox 중심을 맞춘다."""
    c, s = math.cos(math.radians(az)), math.sin(math.radians(az))
    p = base.copy()
    p[:, 0], p[:, 1] = base[:, 0] * c - base[:, 1] * s, base[:, 0] * s + base[:, 1] * c
    w = p[:, 0].max() - p[:, 0].min()
    h = p[:, 2].max() - p[:, 2].min()
    k = (X1 - X0) / w if mode == "width" else (Z1 - Z0) / h
    p *= k
    p[:, 0] += (X0 + X1) / 2 - (p[:, 0].min() + p[:, 0].max()) / 2
    p[:, 2] += (Z0 + Z1) / 2 - (p[:, 2].min() + p[:, 2].max()) / 2
    p[:, 1] += CY - (p[:, 1].min() + p[:, 1].max()) / 2
    o.data.vertices.foreach_set("co", p.ravel())
    o.data.update()
    return k


def setup(o):
    m = bpy.data.materials.new("f")
    m.diffuse_color = (0.3, 0.31, 0.5, 1)
    o.data.materials.clear(); o.data.materials.append(m)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.view_settings.view_transform = 'Standard'
    cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 1.2
    c = bpy.data.objects.new("c", cd)
    c.location = (0, -2, 0.5); c.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(c); sc.camera = c
    return sc


def alpha(path):
    im = bpy.data.images.load(path)
    a = np.array(im.pixels[:]).reshape(RES, RES, 4)[::-1, :, 3] > 0.5
    bpy.data.images.remove(im)
    return a


def main():
    ref = np.array(bpy.data.images.load(MASK).pixels[:]).reshape(RES, RES, 4)[::-1, :, 0] > 0.5
    o, base = load_mesh()
    sc = setup(o)
    best = None
    for az in (0, 90, 180, 270):
        for mode in ("width", "height"):
            k = place(o, base, az, mode)
            p = os.path.join(HERE, "out", "fit_%03d_%s.png" % (az, mode))
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            a = alpha(p)
            iou = (a & ref).sum() / (a | ref).sum()
            print("FIT az=%3d %-6s 배율 %.4f  IoU %.3f  화소 %d (원화 %d)"
                  % (az, mode, k, iou, a.sum(), ref.sum()))
            if best is None or iou > best[0]:
                best = (iou, az, mode)
    print("BEST IoU %.3f  az=%d  %s" % best)


main()
