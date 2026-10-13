# 쇼츠 구멍 편 재료 2 — 블렌더: 각 반지름 비스듬 렌더 + 위에서 본 단면(마스크) · 10-13
# "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b -P 렌더.py
import bpy, sys, os
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = "G:/art2real/out/설명/구멍/"
for r in (3, 4, 5, 6):
    for 종 in ("비스듬", "위"):
        H.scene(res=(800, 800), transparent=True, cavity=(종 == "비스듬"))
        bpy.ops.import_mesh.stl(filepath=O + "r%d.stl" % r); o = bpy.context.selected_objects[0]
        o.color = (0.35, 0.55, 0.95, 1) if 종 == "비스듬" else (1, 1, 1, 1)
        if 종 == "위":
            sh = bpy.context.scene.display.shading; sh.light = "FLAT"
            H.look(center=(0, 0, 0), yaw=0, pitch=89.99, ortho=24, dist=100)
        else:
            H.look(center=(0, 0, 0), yaw=35, pitch=38, ortho=40, dist=100)
        H.shot(O + "%s_r%d.png" % (종, r))
print("ok")
