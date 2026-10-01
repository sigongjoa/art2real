# -*- coding: utf-8 -*-
"""헤드리스: blender -b 오메가몬_머리디테일.blend --python 블렌더_선화싣기.py — 선화 메시(+ 뒤 투구 · 안테나)를 싣고 세 카메라 렌더.
환경변수 PARTS = 쉼표로 부품(기본 선화,투구,안테나L,안테나R) · HEAD_SAVE = 저장 이름."""
import bpy, os, numpy as np
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"; P = os.path.join(B, "머리손"); sc = bpy.context.scene
parts = os.environ.get("PARTS", "선화,투구,안테나L,안테나R").split(",")
col = bpy.data.collections.get("선화") or bpy.data.collections.new("선화")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def mat(n, c): m = bpy.data.materials.new(n); m.diffuse_color = (*c, 1); return m
for n in parts:
    z = np.load(os.path.join(P, n + ".npz")); me = bpy.data.meshes.new("선화_" + n); me.from_pydata(z["V"].tolist(), [], z["F"].tolist()); me.validate()
    me.materials.append(mat(n + "_흰", (0.9, 0.9, 0.93) if n != "안테나L" and n != "안테나R" else (0.85, 0.65, 0.15))); me.materials.append(mat(n + "_검", (0.03, 0.04, 0.08)))
    if "M" in z.files:
        for p, m in zip(me.polygons, z["M"]): p.material_index = int(m)
    for p in me.polygons: p.use_smooth = (n == "투구")
    ob = bpy.data.objects.new("선화_" + n, me); col.objects.link(ob)
    if n == "투구": ob.location.y += 4.0                                                                # 뒤 껍질은 선화 뒤로 조금 물린다(Blender y = −z)
for o in bpy.data.objects:
    if o.type == "MESH" and not o.name.startswith("선화_"): o.hide_render = True; o.hide_set(True)
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.film_transparent = True; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_object_outline = True
for n in ("02_정면", "02_3-4", "02_옆"):
    cam = bpy.data.objects["카메라_" + n]; sc.camera = cam; sc.render.resolution_x = cam["W"]; sc.render.resolution_y = cam["H"]
    sc.render.filepath = os.path.join(B, "렌더_" + n + ".png"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(B, os.environ.get("HEAD_SAVE", "오메가몬_선화.blend"))); print("ok", parts)
