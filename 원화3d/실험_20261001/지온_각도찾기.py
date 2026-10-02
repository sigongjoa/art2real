# -*- coding: utf-8 -*-
"""대표 그림 실루엣(알파)과 겹치는 카메라 각 찾기: yaw 140~220 · pitch 0~40 격자 렌더(투명 · 200px) → IoU(상자 맞춤 뒤)는 밖에서."""
import bpy, os, sys
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\샘플\메크머리_CC0\지온"; G_ = os.path.join(O, "각도"); os.makedirs(G_, exist_ok=True)
sc = H.scene(res=(200, 200), transparent=True); sc.display.shading.light = "FLAT"
obs = []
for k in ("투구_가운데", "핀_왼", "핀_오른", "총_왼", "총_오른"):
    bpy.ops.wm.obj_import(filepath=os.path.join(O, f"자세_{k}.obj"), forward_axis="Y", up_axis="Z"); obs.append(bpy.context.selected_objects[0])
bb = [o.matrix_world @ Vector(v) for o in obs for v in o.bound_box]; c = sum(bb, Vector()) / len(bb)
for yaw in range(140, 221, 5):
    for pitch in range(0, 41, 5):
        H.look(tuple(c), yaw, pitch, 150, dist=500); H.shot(os.path.join(G_, f"y{yaw}_p{pitch}.png"))
print("ok", tuple(round(v, 1) for v in c))
