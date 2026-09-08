# -*- coding: utf-8 -*-
"""면마다 **어느 판을 읽었는지** 색으로 본다. 측면이 이상한 게 판 선택 탓인지 가른다.

    blender -b --python shot_viewmap.py -- out/atlas.blend out/vm
"""
import math, os, sys
import bpy, numpy as np
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
RES,U0,U1,Z0,Z1=1024,-0.6,0.6,-0.1,1.1
RGB={k:np.load(os.path.join(HERE,f"rgb_{k}.npy")) for k in ("front","side","back")}
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
nf=len(me.polygons)
cen=np.empty(nf*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
nor=np.empty(nf*3); me.polygons.foreach_get("normal",nor); nor=nor.reshape(-1,3)
VIEWS=[("front",np.array([0.,1.,0.])),("sidep",np.array([-1.,0.,0.])),
       ("siden",np.array([1.,0.,0.])),("back",np.array([0.,-1.,0.]))]
MAPKEY={"front":"front","sidep":"side","siden":"side","back":"back"}
COL={0:(0.20,0.45,0.95),1:(0.15,0.75,0.35),2:(0.95,0.75,0.15),3:(0.90,0.25,0.25),
     -1:(0.55,0.55,0.58),-2:(0.10,0.10,0.12)}   # 파랑front 초록+x 노랑-x 빨강back 회색미관측 검정판밖
score=np.stack([-nor[:,1],nor[:,0],-nor[:,0],nor[:,1]],1)
order=np.argsort(-score,1)
lab=np.full(nf,-1,np.int8)
for i in range(nf):
    c=Vector(cen[i])
    for slot in range(2):
        v=order[i,slot]
        if score[i,v]<=0.05: break
        dv=Vector(VIEWS[v][1])
        hit,loc,_,_=o.ray_cast(c-dv*4.0,dv)
        if hit and (loc-c).length<=0.004:
            # 투영점이 판 실루엣 안인지도 본다
            key=MAPKEY[VIEWS[v][0]]
            u=c.x if VIEWS[v][0]=="front" else (-c.x if VIEWS[v][0]=="back" else c.y)
            px=int(np.clip((u-U0)/(U1-U0)*RES,0,RES-1))
            py=int(np.clip((Z1-c.z)/(Z1-Z0)*RES,0,RES-1))
            lab[i]= v if RGB[key][py,px,3]>=128 else -2
            break
n={k:int((lab==k).sum()) for k in (0,1,2,3,-1,-2)}
print("판 선택:", {["front","+x","-x","back"][k] if k>=0 else ("미관측" if k==-1 else "판밖"):v
                for k,v in n.items()})
me.materials.clear()
ca=me.color_attributes.new("vm",'BYTE_COLOR','CORNER')
buf=np.empty(len(me.loops)*4,np.float32); buf[3::4]=1.0
ls=np.empty(nf,np.int32); me.polygons.foreach_get("loop_start",ls)
lt=np.empty(nf,np.int32); me.polygons.foreach_get("loop_total",lt)
for i in range(nf):
    c=COL[int(lab[i])]; s=ls[i]*4
    for j in range(lt[i]): buf[s+j*4:s+j*4+3]=c
ca.data.foreach_set("color",buf); me.update()
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='VERTEX'
sc.render.film_transparent=True
sc.render.resolution_x=520; sc.render.resolution_y=900
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.15
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((0,"front"),(90,"R"),(270,"L"),(180,"back")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("VIEWMAP OK")
