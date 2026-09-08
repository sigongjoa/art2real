# -*- coding: utf-8 -*-
"""이미 정규화된 .blend 를 공통 좌표창으로 3면 렌더한다. **재정규화하지 않는다.**

    blender -b --python win_render.py -- <blend> <out_prefix>

mesh_win.py 는 GLB 를 받아 높이·중심을 다시 맞춘다. 깊이 보정을 한 메시에
그걸 쓰면 y 재중심화가 보정을 되돌린다.
"""
import math, os, sys
import bpy
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
bpy.ops.wm.open_mainfile(filepath=SRC)
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='SINGLE'
sc.display.shading.single_color=(1,1,1)
sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=1024
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.2
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"side"),(180,"back")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("WINRENDER OK")
