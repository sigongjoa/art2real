# -*- coding: utf-8 -*-
"""깊이 보정 뒤 표면 평활. 계단은 마칭큐브가 원래 갖고 있던 것이고
깊이를 누르면 남은 깊이 대비 상대적으로 커져 보인다.

    blender -b --python desmooth.py -- <src> <out_prefix> <반복>
"""
import math, os, sys
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
N=int(argv[2])
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
bpy.context.view_layer.objects.active=o
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
if N:
    m=o.modifiers.new("s",'SMOOTH'); m.iterations=N; m.factor=0.5
    bpy.ops.object.modifier_apply(modifier="s")
v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v); v=v.reshape(-1,3)
print(f"평활 {N}회  y [{v[:,1].min():+.4f},{v[:,1].max():+.4f}]")
bpy.ops.wm.save_as_mainfile(filepath=PRE+".blend")
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='SINGLE'
sc.display.shading.single_color=(1,1,1); sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=1024
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.2
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"side")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("DESMOOTH OK")
