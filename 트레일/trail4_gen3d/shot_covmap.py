# -*- coding: utf-8 -*-
"""스냅까지 반영해 면마다 색을 **어떻게** 얻었는지 4분류로 본다.

    blender -b --python shot_covmap.py -- out/atlas.blend out/cm

  A 직접   판 실루엣 안에서 원화 색을 그대로
  B 스냅   실루엣 밖이었지만 45px 안이라 가까운 유효 화소로 당겨옴
  C 너무멂 45px 밖 -> 클래스 단색
  D 미관측 어느 판도 광선 검사를 통과 못함 -> 클래스 단색
"""
import math, os, sys
import bpy, numpy as np
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
RES,U0,U1,Z0,Z1=1024,-0.6,0.6,-0.1,1.1
SNAP_MAX=45
RGB={k:np.load(os.path.join(HERE,f"rgb_{k}.npy")) for k in ("front","side","back")}
SNAP={k:np.load(os.path.join(HERE,f"snap_{k}.npy")) for k in ("front","side","back")}
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
nf=len(me.polygons)
cen=np.empty(nf*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
nor=np.empty(nf*3); me.polygons.foreach_get("normal",nor); nor=nor.reshape(-1,3)
a3=np.empty(nf); me.polygons.foreach_get("area",a3)
VIEWS=[("front",np.array([0.,1.,0.])),("sidep",np.array([-1.,0.,0.])),
       ("siden",np.array([1.,0.,0.])),("back",np.array([0.,-1.,0.]))]
MAPKEY={"front":"front","sidep":"side","siden":"side","back":"back"}
score=np.stack([-nor[:,1],nor[:,0],-nor[:,0],nor[:,1]],1)
order=np.argsort(-score,1)
lab=np.full(nf,3,np.int8)     # 기본 D 미관측
for i in range(nf):
    c=Vector(cen[i])
    for slot in range(2):
        v=order[i,slot]
        if score[i,v]<=0.05: break
        dv=Vector(VIEWS[v][1])
        hit,loc,_,_=o.ray_cast(c-dv*4.0,dv)
        if hit and (loc-c).length<=0.004:
            name=VIEWS[v][0]; key=MAPKEY[name]
            u=c.x if name=="front" else (-c.x if name=="back" else c.y)
            px=int(np.clip((u-U0)/(U1-U0)*RES,0,RES-1))
            py=int(np.clip((Z1-c.z)/(Z1-Z0)*RES,0,RES-1))
            if RGB[key][py,px,3]>=128: lab[i]=0
            elif SNAP[key][py,px,2]<=SNAP_MAX: lab[i]=1
            else: lab[i]=2
            break
NM=["A 직접","B 스냅","C 너무멂","D 미관측"]
COL=[(0.82,0.84,0.86),(0.35,0.72,0.95),(0.95,0.55,0.15),(0.88,0.15,0.15)]
for k in range(4):
    m=lab==k
    print(f"{NM[k]:8s} 면 {int(m.sum()):>7,} ({m.mean()*100:5.1f}%)  면적 {a3[m].sum()/a3.sum()*100:5.1f}%")
me.materials.clear()
ca=me.color_attributes.new("cm",'BYTE_COLOR','CORNER')
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
# 측면 시야에서 보이는 면만 따로 집계
seen=np.zeros(nf,bool)
for dv in ((-1.,0.,0.),(1.,0.,0.)):
    v=Vector(dv)
    for k in np.nonzero(nor@np.array(dv)<-0.05)[0]:
        c=Vector(cen[k]); hit,loc,_,_=o.ray_cast(c-v*4.0,v)
        if hit and (loc-c).length<=0.006: seen[k]=True
print("\n측면에서 실제로 보이는 면만:")
for k in range(4):
    m=(lab==k)&seen
    print(f"  {NM[k]:8s} 면적 {a3[m].sum()/max(a3[seen].sum(),1e-9)*100:5.1f}%")
print("COVMAP OK")
