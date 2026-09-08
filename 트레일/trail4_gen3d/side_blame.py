# -*- coding: utf-8 -*-
"""측면에서 '메시에만 있는' 영역(파랑)이 어느 파츠 탓인지.

    blender -b --python side_blame.py -- out/nd_named2.blend out/blame
파츠마다 고유 색으로 측면을 찍고, 원화 실루엣 밖 화소를 파츠별로 센다.
"""
import math, os, sys, json
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
nf=len(me.polygons)
pid=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
uniq=sorted(set(pid.tolist()))
# 파츠 -> 고유색 (24비트 인덱스)
idx={p:i+1 for i,p in enumerate(uniq)}
me.materials.clear()
ca=me.color_attributes.new("bl",'BYTE_COLOR','CORNER')
buf=np.empty(len(me.loops)*4,np.float32); buf[3::4]=1.0
ls=np.empty(nf,np.int32); me.polygons.foreach_get("loop_start",ls)
lt=np.empty(nf,np.int32); me.polygons.foreach_get("loop_total",lt)
for i in range(nf):
    k=idx[int(pid[i])]
    col=((k&255)/255.0,((k>>8)&255)/255.0,((k>>16)&255)/255.0)
    s=ls[i]*4
    for j in range(lt[i]): buf[s+j*4:s+j*4+3]=col
ca.data.foreach_set("color",buf); me.update()
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='VERTEX'
sc.display.shading.show_cavity=False
sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=1024
sc.render.image_settings.color_management='OVERRIDE'
sc.render.image_settings.view_settings.view_transform='Standard'
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.2
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
a=math.radians(90)
cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
sc.render.filepath=PRE+"_side.png"
bpy.ops.render.render(write_still=True)
json.dump({str(v):(names[k-1] if 0<k<=len(names) else f"p{k}") for k,v in idx.items()},
          open(PRE+"_map.json","w"))
print("BLAME OK", len(uniq), "파츠")
