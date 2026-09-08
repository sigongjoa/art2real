# -*- coding: utf-8 -*-
"""부품 아무거나 — 생성물의 **회전·배율을 IoU 로** 고르고 정면 실루엣을 잰다.

    blender -b --python fit_any.py -- out/parts3/p1.glb out/parts3/p1_mask.png out/parts3/p1

`tri_fit.py` 를 견갑에서 떼어낸 것. 116번(눈으로 방향을 찍지 마라)을 부품마다 건다.
마스크에서 상자를 직접 재므로 부품별 상수가 필요 없다.
"""
import bpy, os, sys, math
import numpy as np

RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1
CY = 0.0                                  # 깊이 중심은 판정에 안 쓴다 (정면 정사영)


def img_gray(path):
    im = bpy.data.images.load(path)
    a = np.array(im.pixels[:]).reshape(RES, RES, 4)[::-1]
    bpy.data.images.remove(im)
    return a


def load(glb):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.context.view_layer.objects.active = obs[0]
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o, np.array([v.co[:] for v in o.data.vertices])


def box_of(mask):
    ys, xs = np.nonzero(mask)
    wx = lambda c: U0 + c * (U1 - U0) / (RES - 1)
    wz = lambda r: Z1 - r * (Z1 - Z0) / (RES - 1)
    return wx(xs.min()), wx(xs.max()), wz(ys.max()), wz(ys.min())


def place(o, base, az, mode, box):
    x0, x1, z0, z1 = box
    c, s = math.cos(math.radians(az)), math.sin(math.radians(az))
    p = base.copy()
    p[:, 0], p[:, 1] = base[:, 0] * c - base[:, 1] * s, base[:, 0] * s + base[:, 1] * c
    k = ((x1 - x0) / max(p[:, 0].max() - p[:, 0].min(), 1e-9) if mode == "width"
         else (z1 - z0) / max(p[:, 2].max() - p[:, 2].min(), 1e-9))
    p *= k
    p[:, 0] += (x0 + x1) / 2 - (p[:, 0].min() + p[:, 0].max()) / 2
    p[:, 2] += (z0 + z1) / 2 - (p[:, 2].min() + p[:, 2].max()) / 2
    p[:, 1] += CY - (p[:, 1].min() + p[:, 1].max()) / 2
    o.data.vertices.foreach_set("co", p.ravel())
    o.data.update()
    return k


def setup(o):
    m = bpy.data.materials.new("f"); m.diffuse_color = (0.3, 0.31, 0.5, 1)
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


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    glb, maskp, tag = a[0], a[1], a[2]
    ref = img_gray(maskp)[..., 0] > 0.5
    box = box_of(ref)
    o, base = load(glb)
    sc = setup(o)
    best = None
    for az in (0, 90, 180, 270):
        for mode in ("width", "height"):
            k = place(o, base, az, mode, box)
            sc.render.filepath = "%s_fit_%03d_%s.png" % (tag, az, mode)
            bpy.ops.render.render(write_still=True)
            al = img_gray(sc.render.filepath + ".png" if not sc.render.filepath.endswith(".png")
                          else sc.render.filepath)[..., 3] > 0.5
            iou = (al & ref).sum() / (al | ref).sum()
            print("  az=%3d %-6s 배율 %.4f  IoU %.3f" % (az, mode, k, iou))
            if best is None or iou > best[0]:
                best = (iou, az, mode)
    place(o, base, best[1], best[2], box)
    sc.render.filepath = tag + "_best.png"
    bpy.ops.render.render(write_still=True)
    print("BEST %s IoU %.3f az=%d %s  면 %d  원화 %dpx"
          % (os.path.basename(tag), best[0], best[1], best[2],
             len(o.data.polygons), int(ref.sum())))


main()
