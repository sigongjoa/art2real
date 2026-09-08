# -*- coding: utf-8 -*-
"""측면도에 파츠 번호를 단다. 어디가 문제인지 지목할 수 있게.

    blender -b --python numbered_side.py -- out/nd_named2.blend out/numside
파츠별 측면 투영 중심과 '원화 실루엣 밖' 비율을 같이 내보낸다.
"""
import json, math, os, sys
import bpy, numpy as np
argv=sys.argv[sys.argv.index("--")+1:]
SRC,PRE=os.path.abspath(argv[0]),os.path.abspath(argv[1])
HERE=os.path.dirname(os.path.abspath(__file__))
RES,U0,U1,Z0,Z1=1024,-0.6,0.6,-0.1,1.1
c=RES/2; axr=np.arange(RES)
def warp(a,dx,dy,s):
    sx=np.clip(np.rint(s*(axr-c)+c+dx),0,RES-1).astype(int)
    sy=np.clip(np.rint(s*(axr-c)+c+dy),0,RES-1).astype(int)
    return a[np.ix_(sy,sx)]
FIT=json.load(open(os.path.join(HERE,"fit.json")))
A=warp(np.load(os.path.join(HERE,"true_side_clean.npy")),*FIT["side"])
bpy.ops.wm.open_mainfile(filepath=SRC)
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; me=o.data
names=json.load(open(os.path.join(HERE,"named_parts.json")))
nf=len(me.polygons)
pid=np.empty(nf,np.int32); me.attributes["part_id"].data.foreach_get("value",pid)
cen=np.empty(nf*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
ar=np.empty(nf); me.polygons.foreach_get("area",ar)
lv=np.empty(len(me.loops),np.int32); me.loops.foreach_get("vertex_index",lv)
ls=np.empty(nf,np.int32); me.polygons.foreach_get("loop_start",ls)
co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
tri=np.stack([lv[ls],lv[ls+1],lv[ls+2]],1)
def dil(m,k=2):
    out=m.copy()
    for dy in range(-k,k+1):
        for dx in range(-k,k+1): out|=np.roll(np.roll(m,dy,0),dx,1)
    return out
rows=[]
for k,nm in enumerate(names):
    p=k+1
    fm=pid==p
    if fm.sum()<800: continue
    vs=np.unique(tri[fm])
    px=np.clip(((co[vs,1]-U0)/(U1-U0)*RES).astype(np.int32),0,RES-1)
    py=np.clip(((Z1-co[vs,2])/(Z1-Z0)*RES).astype(np.int32),0,RES-1)
    m=np.zeros((RES,RES),bool); m[py,px]=True; m=dil(m,2)
    a_=int(m.sum()); out=int((m&~A).sum())
    cc=cen[fm]
    rows.append(dict(name=nm, faces=int(fm.sum()), area=float(ar[fm].sum()),
                     cy=float(np.median(cc[:,1])), cz=float(np.median(cc[:,2])),
                     cx=float(np.median(cc[:,0])),
                     proj=a_, out=out, outr=out/max(a_,1)))
rows.sort(key=lambda r:-r["out"])
json.dump(rows, open(PRE+".json","w"), ensure_ascii=False, indent=1)
print(f"파츠 {len(rows)}개")
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='MATCAP'; sc.display.shading.studio_light='basic_1.exr'
sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.86,0.86,0.88)
sc.display.shading.show_cavity=True; sc.display.shading.cavity_type='BOTH'
sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=1024
sc.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.2
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
for az,tag in ((90,"side"),(270,"sideL")):
    a=math.radians(az)
    cam.location=(math.sin(a)*6,-math.cos(a)*6,0.5); cam.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=f"{PRE}_{tag}.png"; bpy.ops.render.render(write_still=True)
print("NUMSIDE OK")
