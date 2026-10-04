# -*- coding: utf-8 -*-
"""블렌더 래티스 변형 (blender -b -P 격자변형_bl.py) — 격자값.json 의 4 층 값으로 래티스 3×3×4 점을 옮겨 엑시아_정렬을 부드럽게 휜다.
점 하나 = (x, y, z): x' = c + dc + (x − c)·sx · y' = y·sy (y > 0 뒤쪽만). 출력 엑시아_격자.ply"""
import bpy, json, os
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
J = json.load(open(os.path.join(B, "격자값.json"))); 층 = J["층"]; lo, hi = J["범위"]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=os.path.join(B, "엑시아_정렬.ply")); ob = bpy.context.selected_objects[0]; ob.data = ob.data.copy()   # 여러 사용자 데이터면 모디파이어 적용이 막힘
ld = bpy.data.lattices.new("격자"); ld.points_u, ld.points_v, ld.points_w = 3, 3, 4; ld.interpolation_type_u = ld.interpolation_type_v = ld.interpolation_type_w = "KEY_BSPLINE"
lo_ = bpy.data.objects.new("격자", ld); bpy.context.scene.collection.objects.link(lo_)
pad = 1.05; lo_.location = [(a + b) / 2 for a, b in zip(lo, hi)]; lo_.scale = [(b - a) * pad for a, b in zip(lo, hi)]
mod = ob.modifiers.new("격자", "LATTICE"); mod.object = lo_
cx, cy, cz = lo_.location; sx_, sy_, sz_ = lo_.scale
for i, p in enumerate(ld.points):
    u, vv, w = p.co_deform.x, p.co_deform.y, p.co_deform.z          # −0.5 … 0.5 (래티스 지역 좌표)
    k = i // 9; L = 층[k]
    X = cx + u * sx_; Y = cy + vv * sy_
    X2 = L["c"] + L["dc"] + (X - L["c"]) * L["sx"]
    Y2 = Y * L["sy"] if Y > 0 else Y
    p.co_deform.x = (X2 - cx) / sx_; p.co_deform.y = (Y2 - cy) / sy_
bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="격자")
bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
bpy.ops.wm.ply_export(filepath=os.path.join(B, "엑시아_격자.ply"), export_selected_objects=True, export_colors="SRGB", ascii_format=False)
print("ok", [round(L["sx"], 2) for L in 층], [round(L["sy"], 2) for L in 층])
