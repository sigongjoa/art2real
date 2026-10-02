# -*- coding: utf-8 -*-
"""부조.ply 를 정면 · 왼 · 오른 · 3/4 로. blender -b -P 부조_렌더.py"""
import bpy, os, sys
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\오메가몬2\지표\부조"
sc = H.scene(res=(700, 700), transparent=False); sc.world.color = (1, 1, 1); sh = sc.display.shading; sh.color_type = "VERTEX"; sh.light = "STUDIO"; sh.show_cavity = True
bpy.ops.wm.ply_import(filepath=os.path.join(O, "부조.ply"), forward_axis="Y", up_axis="Z"); o = bpy.context.selected_objects[0]
bb = [o.matrix_world @ Vector(v) for v in o.bound_box]; c = sum(bb, Vector()) / 8; ext = max((bb[6] - bb[0])[:])
for nm, (yaw, pitch) in {"정면": (0, 0), "왼": (90, 0), "오른": (-90, 0), "34": (-35, 12)}.items(): H.look(tuple(c), yaw, pitch, ext * 1.15, dist=ext * 6); H.shot(os.path.join(O, f"부조_{nm}.png"))
print("ok")
