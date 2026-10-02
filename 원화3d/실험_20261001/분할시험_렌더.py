# -*- coding: utf-8 -*-
"""분할시험.py 의 ply(면 색)를 단계마다 같은 카메라로 렌더. blender -b -P 분할시험_렌더.py"""
import bpy, os, sys, json, glob
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\오메가몬2\지표\분할시험"; 점수 = json.load(open(os.path.join(O, "점수.json"), encoding="utf-8"))
for 이름, r in 점수.items():
    sc = H.scene(res=(420, 420), transparent=False); sc.world.color = (1, 1, 1); sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "VERTEX"; sh.show_cavity = False
    단 = sorted(glob.glob(os.path.join(O, f"{이름}_*.ply"))); c = None
    for f in 단:
        bpy.ops.wm.ply_import(filepath=f, forward_axis="Y", up_axis="Z"); o = bpy.context.selected_objects[0]
        if c is None:
            bb = [o.matrix_world @ Vector(v) for v in o.bound_box]; c = sum(bb, Vector()) / 8; ext = max((bb[6] - bb[0])[:])
        for x in bpy.context.scene.objects:
            if x.type == "MESH": x.hide_render = x is not o
        H.look(tuple(c), r["yaw"], 20, ext * 1.25, dist=ext * 6); H.shot(f[:-4] + ".png")
    for x in list(bpy.data.objects):
        if x.type == "MESH": bpy.data.objects.remove(x)
print("ok")
