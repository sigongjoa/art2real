# -*- coding: utf-8 -*-
"""이 메시에 접힘선이 실제로 얼마나 있는지 잰다. 임계값을 지어내지 않기 위해서."""
import os, sys, math
import bpy, bmesh, numpy as np
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1])
bpy.ops.wm.open_mainfile(filepath=SRC)
ob=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]; me=ob.data
bm=bmesh.new(); bm.from_mesh(me)
ang=np.array([e.calc_face_angle(0.0) for e in bm.edges if len(e.link_faces)==2])
ln =np.array([e.calc_length()      for e in bm.edges if len(e.link_faces)==2])
bm.free()
deg=np.degrees(ang)
print(f"내부 에지 {len(deg):,}  에지길이 중앙 {np.median(ln)*1000:.2f}mm")
print("이면각 분포(도):", {f"p{p}":round(float(np.percentile(deg,p)),1) for p in (50,75,90,95,98,99,99.5,99.9)})
for t in (8,12,15,20,25,30,40):
    n=int((deg>t).sum()); print(f"  >{t:2d}도 : {n:>7,} 에지 ({n/len(deg)*100:5.2f}%)")
