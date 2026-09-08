import math, os, sys, json
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
pid=np.empty(len(me.polygons),np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
cen=np.empty(len(me.polygons)*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
a3=np.empty(len(me.polygons)); me.polygons.foreach_get("area",a3)
HEADP={"a_helm","a_brow","a_muzzle","a_eye","a_eye_M","a_helm_horn","a_helm_horn_M","a_helm_spike"}
idx={n:i+1 for i,n in enumerate(names)}
for n in sorted(HEADP):
    if n not in idx: continue
    m=pid==idx[n]
    if not m.sum(): continue
    c=cen[m]
    print(f"  {n:16s} 면 {int(m.sum()):>7,}  x[{c[:,0].min():+.3f},{c[:,0].max():+.3f}] "
          f"z[{c[:,2].min():+.3f},{c[:,2].max():+.3f}]")
hm=np.isin(pid,[idx[n] for n in HEADP if n in idx])
c=cen[hm]
print(f"  머리 합계        면 {int(hm.sum()):>7,}  x[{c[:,0].min():+.3f},{c[:,0].max():+.3f}] "
      f"z[{c[:,2].min():+.3f},{c[:,2].max():+.3f}]  면적 {a3[hm].sum()/a3.sum()*100:.1f}%")
# 머리 파츠만 빨강, 나머지 회색
COL=np.tile(np.array([0.85,0.86,0.88]),(len(me.polygons),1))
COL[hm]=(0.90,0.20,0.20)
ca=me.color_attributes.new("h",'BYTE_COLOR','CORNER')
buf=np.empty(len(me.loops)*4,np.float32); buf[3::4]=1.0
ls=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get("loop_start",ls)
lt=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get("loop_total",lt)
for i in range(len(me.polygons)):
    s=ls[i]*4
    for j in range(lt[i]): buf[s+j*4:s+j*4+3]=COL[i]
ca.data.foreach_set("color",buf); me.update()
me.materials.clear()
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='VERTEX'
sc.display.shading.show_cavity=True
sc.render.film_transparent=True; sc.render.resolution_x=sc.render.resolution_y=700
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=0.42
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"side")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.90); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("HELM OK")
