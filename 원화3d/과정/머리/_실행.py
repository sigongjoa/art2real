# -*- coding: utf-8 -*-
"""블렌더 안에서(blender -b [이전.blend] --python _실행.py -- <단계.py> <저장.blend> <프레임머리>) — 단계 파일 하나를 실행하고 저장 · 카메라마다 한 컷 렌더.
   처음(이전 .blend 없음)이면 장면을 만든다: 카메라(블록아웃.json · 자세5 등록) · 배경 캡처는 렌더에 안 넣음(따라 하기용으로 카메라에만)."""
import bpy, sys, os, json, math
from mathutils import Matrix
a = sys.argv[sys.argv.index("--") + 1:]; 단계, 저장, 프레임 = a[0], a[1], a[2]
B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"; sc = bpy.context.scene
if "카메라" not in bpy.data.collections:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    col = bpy.data.collections.new("카메라"); sc.collection.children.link(col)
    for k in json.load(open(os.path.join(B, "블록아웃.json"), encoding="utf-8"))["카메라"]:
        if k["이름"] not in ("02_정면", "02_3-4", "02_옆"): continue
        cam = bpy.data.cameras.new(k["이름"]); cam.type = "ORTHO"; cam.ortho_scale = k["ortho_scale"]; cam.clip_start = 1; cam.clip_end = 2000
        ob = bpy.data.objects.new("카메라_" + k["이름"], cam); col.objects.link(ob); ob.matrix_world = Matrix(k["행렬"]); ob["W"], ob["H"] = k["W"], k["H"]
        bg = cam.background_images.new(); bg.image = bpy.data.images.load(k["파일"]); bg.alpha = 0.5; cam.show_background_images = True
    sc["단계기록"] = "[]"
exec(compile(open(단계, encoding="utf-8").read(), 단계, "exec"), {"bpy": bpy, "math": math, "값": json.load(open(os.path.join(os.path.dirname(단계), "..", "값.json"), encoding="utf-8"))})
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_object_outline = True
sc.render.film_transparent = False; sc.world = sc.world or bpy.data.worlds.new("W"); sc.display.shading.background_type = "VIEWPORT" if hasattr(sc.display.shading, "background_type") else None
for o in bpy.data.objects:
    if o.get("칼"): o.hide_render = True; o.display_type = "WIRE"
for n in ("02_3-4", "02_옆", "02_정면"):
    cam = bpy.data.objects["카메라_" + n]; sc.camera = cam; sc.render.resolution_x = cam["W"]; sc.render.resolution_y = cam["H"]; sc.render.resolution_percentage = 100
    sc.render.filepath = "%s_%s.png" % (프레임, n); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=저장); print("단계 끝", os.path.basename(단계))
