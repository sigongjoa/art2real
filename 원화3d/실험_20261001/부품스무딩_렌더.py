# -*- coding: utf-8 -*-
"""스무딩 부품 조립(투구 돔 + 뿔 + 판 · 눈) vs 거친 부조 — 정면 · 왼 · 오른 · 3/4. blender -b -P 부품스무딩_렌더.py"""
import bpy, os, sys, glob
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\오메가몬2\지표\부조"
눈 = [f for f in glob.glob(os.path.join(O, "스무딩", "*.ply")) if os.path.basename(f).startswith("눈_")]
판들 = {"거친": [os.path.join(O, "부조.ply"), os.path.join(O, "투구돔.ply")], "스무딩": glob.glob(os.path.join(O, "스무딩", "*.ply")) + [os.path.join(O, "뿔.ply"), os.path.join(O, "투구돔.ply")],
       "면스무딩": glob.glob(os.path.join(O, "면스무딩", "*.ply")) + 눈 + [os.path.join(O, "뿔.ply"), os.path.join(O, "투구돔.ply")]}
for 이름, files in [(k_, v_) for k_, v_ in 판들.items() if k_ in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else 판들.items():
    sc = H.scene(res=(600, 600), transparent=False); sc.world.color = (1, 1, 1); sh = sc.display.shading; sh.color_type = "VERTEX"; sh.light = "STUDIO"; sh.show_cavity = True
    obs = []
    for f in files:
        try: bpy.ops.wm.ply_import(filepath=f, forward_axis="Y", up_axis="Z"); obs.append(bpy.context.selected_objects[0])
        except RuntimeError: print("못 읽음", os.path.basename(f))
    bb = [o.matrix_world @ Vector(v) for o in obs for v in o.bound_box]; c = sum(bb, Vector()) / len(bb); ext = max(max(v[i] for v in bb) - min(v[i] for v in bb) for i in range(3))
    for nm, (yaw, pitch) in {"정면": (0, 0), "왼": (90, 0), "오른": (-90, 0), "34": (-35, 12)}.items(): H.look(tuple(c), yaw, pitch, ext * 1.1, dist=ext * 6); H.shot(os.path.join(O, f"조립_{이름}_{nm}.png"))
    for o in obs: bpy.data.objects.remove(o)
print("ok")
