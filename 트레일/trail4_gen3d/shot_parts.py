import math, os, sys
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
bpy.ops.wm.open_mainfile(filepath=SRC)
ob=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]; me=ob.data
nf=len(me.polygons)
pid=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
rng=np.random.default_rng(7)
pal=rng.uniform(0.15,0.95,(int(pid.max())+2,3))
pal[0]=(0.62,0.62,0.64)                     # 라벨 없는 면은 회색
col=me.color_attributes.new("pcol",'BYTE_COLOR','CORNER')
buf=np.empty(len(me.loops)*4,np.float32); buf[3::4]=1.0
lstart=np.empty(nf,np.int32); ltot=np.empty(nf,np.int32)
me.polygons.foreach_get("loop_start",lstart); me.polygons.foreach_get("loop_total",ltot)
for i in range(nf):
    c=pal[pid[i]]; s=lstart[i]*4
    for j in range(ltot[i]): buf[s+j*4:s+j*4+3]=c
col.data.foreach_set("color",buf); me.update()
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='VERTEX'
sc.display.shading.show_cavity=True; sc.display.shading.cavity_type='BOTH'
sc.render.film_transparent=True; sc.render.resolution_x=sc.render.resolution_y=768
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.2
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag,osc,z in ((0,"front",1.2,0.5),(90,"side",1.2,0.5),(180,"back",1.2,0.5),
                     (0,"foot",0.42,0.10),(0,"torso",0.55,0.62)):
    cd.ortho_scale=osc; a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,z); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("PARTSHOT OK")
