# -*- coding: utf-8 -*-
"""blend 파일을 정면/3-4/측면 세 각도로 워크벤치 렌더한다.

    blender -b --python shot.py -- in.blend out_prefix
"""
import math
import os
import sys

import bpy

RES = 700


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO" if os.environ.get("FLAT") else "MATCAP"
    if os.environ.get("FLAT"):
        for o in bpy.context.scene.objects:
            if o.type == "MESH":
                o.data.use_auto_smooth = False
                for f in o.data.polygons:
                    f.use_smooth = False
    sh.color_type = "MATERIAL"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = False
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 0.22
    tgt = (0.175, 0.03, 0.87)
    for name, az in (("front", 0), ("q", 40), ("side", 90)):
        r = 1.2
        cam.location = (tgt[0] + r * math.sin(math.radians(az)),
                        tgt[1] - r * math.cos(math.radians(az)), tgt[2])
        cam.rotation_euler = (math.radians(90), 0, math.radians(az))
        sc.render.filepath = os.path.abspath(a[1]) + "_" + name + ".png"
        bpy.ops.render.render(write_still=True)
        print("SHOT", sc.render.filepath)


if __name__ == "__main__":
    main()
