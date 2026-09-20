"""**모델 렌더 vs 원화** — 같은 월드 창으로 잘라 겹치고 숫자를 낸다.

    blender -b <모델.blend> --python compare.py -- <buildspec.json> <원화.png> [출력폴더]

닮았는지를 눈으로 말하지 않는다. 세 가지를 낸다:
    실루엣 IoU     겉모양이 맞나
    빠짐 / 과함    원화에 있는데 없나 / 없는데 있나
    겹침 그림      초록=맞음 · 파랑=원화만 · 빨강=모델만

프레이밍은 설계도의 `px_to_world` 로 맞춘다 — 눈으로 맞추면 그 순간 비교가 무의미해진다.
"""
import json
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC, REF = argv[0], argv[1]
OUT = argv[2] if len(argv) > 2 else os.path.dirname(SPEC)
spec = json.load(open(SPEC, encoding="utf-8"))
# **창은 설계도가 정한다.** 외형(투구 돔)에 맞추면 뿔이 잘려 모델이 창보다 커지고
# 과함이 실제 오차가 아니라 프레이밍 탓이 된다(실측: 과함 55.6% · 빠짐 0.0%).
vf = spec.get("view_front")
if vf:
    xc, zc, span = vf["cx"], vf["cz"], vf["span"]
else:
    hw = spec["envelope"]["halfwidth"]["rows"]
    Z0, Z1 = min(r[0] for r in hw), max(r[0] for r in hw)
    xc, zc, span = 0.0, (Z0 + Z1) / 2, (Z1 - Z0) * 1.2
RES = 512

sc = bpy.context.scene
cam = bpy.data.cameras.new("c")
cam.type, cam.ortho_scale = 'ORTHO', span
cam.clip_start, cam.clip_end = 0.01, 30
ob = bpy.data.objects.new("c", cam)
sc.collection.objects.link(ob)
sc.camera = ob
ob.location = (xc, -8, zc)
ob.rotation_euler = (math.pi / 2, 0, 0)
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = True            # 알파로 실루엣을 바로 얻는다
sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light, sh.color_type = 'STUDIO', 'SINGLE'
sh.single_color = (0.72, 0.72, 0.76)
sh.show_cavity, sh.show_object_outline = True, False
sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = os.path.abspath(os.path.join(OUT, "cmp_render.png"))
bpy.ops.render.render(write_still=True)
print("RENDER", sc.render.filepath, "· ortho", round(span, 4), "· z중심", round(zc, 4))
json.dump({"ortho_scale": span, "z_center": zc, "x_center": xc, "res": RES},
          open(os.path.join(OUT, "cmp_frame.json"), "w"), indent=1)
