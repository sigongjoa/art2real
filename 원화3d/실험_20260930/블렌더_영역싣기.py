# -*- coding: utf-8 -*-
"""헤드리스: blender -b 오메가몬_머리디테일.blend --python 블렌더_영역싣기.py — 투구영역.npz 를 영역마다 색을 달아 싣고 세 카메라 렌더."""
import bpy, os, json, numpy as np
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"; P = os.path.join(B, "머리손"); sc = bpy.context.scene
pal = {int(k): v for k, v in json.load(open(os.path.join(B, "영역팔레트.json"), encoding="utf-8"))["팔레트"].items()}
col = bpy.data.collections.get("영역") or bpy.data.collections.new("영역")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
z = np.load(os.path.join(P, "투구영역.npz")); me = bpy.data.meshes.new("영역_투구"); me.from_pydata(z["V"].tolist(), [], z["F"].tolist()); me.validate()
labels = [0] + sorted(set(z["M"].tolist()) - {0}); idx = {l: i for i, l in enumerate(labels)}
for l in labels:
    m = bpy.data.materials.new("영역_%d" % l); m.diffuse_color = (*(pal.get(l, [0.9, 0.9, 0.93]) if l else [0.9, 0.9, 0.93]), 1); me.materials.append(m)
for p, l in zip(me.polygons, z["M"]): p.material_index = idx[int(l)]; p.use_smooth = False
ob = bpy.data.objects.new("영역_투구", me); col.objects.link(ob)
for n in ("안테나L", "안테나R", "뿔"):
    zz = np.load(os.path.join(P, n + ".npz")); m2 = bpy.data.meshes.new("영역_" + n); m2.from_pydata(zz["V"].tolist(), [], zz["F"].tolist()); m2.validate()
    mt = bpy.data.materials.new("영역_" + n); mt.diffuse_color = (0.85, 0.65, 0.15, 1) if n != "뿔" else (0.9, 0.9, 0.93, 1); m2.materials.append(mt); col.objects.link(bpy.data.objects.new("영역_" + n, m2))
for o in bpy.data.objects:
    if o.type == "MESH" and not o.name.startswith("영역_"): o.hide_render = True; o.hide_set(True)
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.film_transparent = True; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_object_outline = True
for n in ("02_정면", "02_3-4", "02_옆"):
    cam = bpy.data.objects["카메라_" + n]; sc.camera = cam; sc.render.resolution_x = cam["W"]; sc.render.resolution_y = cam["H"]
    sc.render.filepath = os.path.join(B, "렌더_" + n + ".png"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(B, "오메가몬_영역.blend")); print("ok", len(labels) - 1)
