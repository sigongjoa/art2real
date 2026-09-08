# -*- coding: utf-8 -*-
"""원화와 **같은 정사영**으로 견갑만 찍는다. 눈으로 붙여 보라고 만드는 것.

    blender -b out/workbench.blend --python ab_front.py

CAM_front / CAM_side 는 원화 정규화 창과 화소 대 화소로 맞춰져 있다 (README 2절).
그 카메라로 부품만(REF 판·돔 끄고) 찍어 out/ab_<뷰>_<변형>.png 로 낸다.
"""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SHELL = (89, 93, 126)
GOLD = (198, 158, 62)


def lin(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


NOHORN = bool(os.environ.get("NOHORN"))


def parts():
    return [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and not o.name.startswith("REF_")
            and not (NOHORN and o.name.startswith("horn"))]


def setup():
    sc = bpy.context.scene
    for o in bpy.data.objects:                       # 참조판·돔은 렌더에서 뺀다
        if o.name.startswith("REF_") or (NOHORN and o.name.startswith("horn")):
            o.hide_render = True
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.film_transparent = True                # 원화 위에 얹으려면 알파가 있어야 한다
    sc.render.resolution_x = sc.render.resolution_y = 1024
    sc.view_settings.view_transform = 'Standard'
    for o in parts():                                # 평면색 — 형태만 보려는 것
        o.data.materials.clear()
        m = bpy.data.materials.new("f")
        m.diffuse_color = lin(GOLD if o.name.startswith("horn") else SHELL)
        o.data.materials.append(m)
    return sc


def main():
    sc = setup()
    for v in ("front", "side"):
        sc.camera = bpy.data.objects["CAM_" + v]
        sc.render.filepath = os.path.join(OUT, os.environ.get("TAG","ab") + "_%s.png" % v)
        bpy.ops.render.render(write_still=True)
        print("AB", v, sc.render.filepath)


main()
