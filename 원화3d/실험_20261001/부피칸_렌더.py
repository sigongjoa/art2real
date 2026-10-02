# -*- coding: utf-8 -*-
"""부피칸.py 조각(부품 색) + 코어(회색) 렌더 — 정면 · 옆 · 3/4. blender -b -P 부피칸_렌더.py"""
import bpy, os, sys, glob, json, colorsys
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\오메가몬2\지표\부피칸"
sc = H.scene(res=(800, 800), transparent=False); sc.world.color = (1, 1, 1); sh = sc.display.shading; sh.color_type = "OBJECT"; sh.light = "STUDIO"; sh.show_cavity = True
obs = []
for f in sorted(glob.glob(os.path.join(O, "part_*.obj"))) + [os.path.join(O, "코어.obj")]:
    bpy.ops.wm.obj_import(filepath=f, forward_axis="Y", up_axis="Z"); o = bpy.context.selected_objects[0]
    i = int(os.path.basename(f)[5:7]) if "part_" in f else -1
    o.color = (0.55, 0.55, 0.58, 1) if i < 0 else colorsys.hsv_to_rgb((i * 0.137) % 1, 0.65, 0.95) + (1,); obs.append(o)
bb = [o.matrix_world @ Vector(v) for o in obs for v in o.bound_box]; c = sum(bb, Vector()) / len(bb); ext = max(max(v[k] for v in bb) - min(v[k] for v in bb) for k in range(3))
for nm, (yaw, pitch) in {"정면": (0, 0), "옆": (-90, 0), "34": (-35, 10), "뒤34": (145, 10)}.items(): H.look(tuple(c), yaw, pitch, ext * 1.1, dist=ext * 6); H.shot(os.path.join(O, f"렌더_{nm}.png"))
print("ok")
