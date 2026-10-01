# -*- coding: utf-8 -*-
"""블렌더 안(MCP exec) — 머리손 · 머리디테일 부품을 싣고 눈구멍을 파고 세 카메라로 렌더 · 저장. 뺄 부품은 전역 뺌 = {...} 로."""
import bpy, os, json, numpy as np, mathutils, math
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"; P = os.path.join(B, "머리손"); sc = bpy.context.scene
뺌 = globals().get("뺌", {"눈L", "눈R", "부리"})
기본 = json.load(open(os.path.join(B, "머리손.json"), encoding="utf-8"))["부품"]; 디 = json.load(open(os.path.join(B, "머리디테일.json"), encoding="utf-8"))["부품"]
col = bpy.data.collections.get("머리손") or bpy.data.collections.new("머리손")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
흰 = (0.9, 0.9, 0.93); 색 = {"눈바닥": (0.03, 0.04, 0.08), "홍채": (0.25, 0.55, 0.9), "안테나": (0.85, 0.65, 0.15), "차양": (0.8, 0.8, 0.86), "윗테": (0.78, 0.78, 0.84), "송곳니": (0.86, 0.86, 0.9), "윗부리": (0.93, 0.93, 0.96), "아랫부리": (0.84, 0.84, 0.89), "턱": (0.84, 0.84, 0.89)}
def 넣기(n):
    z = np.load(os.path.join(P, n + ".npz")); me = bpy.data.meshes.new("머리손_" + n); me.from_pydata(z["V"].tolist(), [], z["F"].tolist()); me.validate()
    for p in me.polygons: p.use_smooth = (n == "투구")
    ob = bpy.data.objects.new("머리손_" + n, me); col.objects.link(ob); c = next((v for k, v in 색.items() if n.startswith(k)), 흰); m = bpy.data.materials.new("머리손_" + n); m.diffuse_color = (*c, 1); me.materials.append(m); return ob
for n in 기본 + 디:
    if n not in 뺌 and os.path.exists(os.path.join(P, n + ".npz")) and not bpy.data.objects.get("머리손_" + n): 넣기(n)
for 대상 in ("투구", "이마L", "이마R"):
  투 = bpy.data.objects.get("머리손_" + 대상)
  if not 투: continue
  for k in ("눈칼L", "눈칼R"):
    칼 = bpy.data.objects.get("머리손_" + k)
    if not 칼: continue
    md = 투.modifiers.new(k, "BOOLEAN"); md.operation = "DIFFERENCE"; md.solver = "EXACT"; md.object = 칼
    dg = bpy.context.evaluated_depsgraph_get(); new = bpy.data.meshes.new_from_object(투.evaluated_get(dg)); old = 투.data; 투.data = new; 투.modifiers.clear(); bpy.data.meshes.remove(old)
    칼.hide_render = True; 칼.hide_set(True)
for p in bpy.data.objects["머리손_투구"].data.polygons: p.use_smooth = True
for o in bpy.data.objects:
    if o.type == "MESH" and not o.name.startswith("머리손_"): o.hide_render = True; o.hide_set(True)
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.film_transparent = True; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_object_outline = True
for n in ("02_정면", "02_3-4", "02_옆"):
    cam = bpy.data.objects["카메라_" + n]; sc.camera = cam; sc.render.resolution_x = cam["W"]; sc.render.resolution_y = cam["H"]
    sc.render.filepath = os.path.join(B, "렌더_" + n + ".png"); bpy.ops.render.render(write_still=True)
if bpy.context.window_manager.windows:                                                                   # blender -b(헤드리스)엔 창이 없다
    win = bpy.context.window_manager.windows[0]; area = next(a for a in win.screen.areas if a.type == 'VIEW_3D'); sp = area.spaces.active; r3d = sp.region_3d
    r3d.view_perspective = 'PERSP'; r3d.view_rotation = mathutils.Euler((math.radians(82), 0, math.radians(-30)), 'XYZ').to_quaternion(); r3d.view_location = mathutils.Vector((0, -10, -45)); r3d.view_distance = 230; sp.shading.type = 'SOLID'; sp.shading.light = 'STUDIO'; sp.shading.color_type = 'MATERIAL'; sp.overlay.show_overlays = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(B, os.environ.get("HEAD_SAVE", "오메가몬_머리디테일.blend"))); print("ok", sorted(o.name for o in col.objects if not o.hide_get()))
