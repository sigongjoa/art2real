# -*- coding: utf-8 -*-
"""프록시(FreeCAD CAD)의 크기를 원화·생성메시와 맞춰 본다.

    blender -b --python proxy_check.py -- out/named2.blend

assign_named.py 와 **같은 정렬**을 재현한다 (전체 프록시 bbox 를 생성메시 bbox 에 맞춤).
"""
import glob, os, sys
import bpy, numpy as np
SRC=os.path.abspath(sys.argv[sys.argv.index("--")+1])
HERE=os.path.dirname(os.path.abspath(__file__))
PXD=os.path.join(HERE,"..","trail3_freecad","proxy")
DROP={"c_cuirass","c_helm"}
bpy.ops.wm.open_mainfile(filepath=SRC)
gen=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
me=gen.data
cen=np.empty(len(me.polygons)*3); me.polygons.foreach_get("center",cen); cen=cen.reshape(-1,3)
V={}
allv=[]
for p in sorted(glob.glob(os.path.join(PXD,"*.stl"))):
    nm=os.path.splitext(os.path.basename(p))[0]
    if nm in DROP: continue
    bpy.ops.wm.stl_import(filepath=p)
    o=bpy.context.selected_objects[0]
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v)
    v=v.reshape(-1,3)*0.001
    bpy.data.objects.remove(o,do_unlink=True)
    if len(v)<8: continue
    V[nm]=v; allv.append(v)
pts=np.vstack(allv)
gl,gh=cen.min(0),cen.max(0); lo,hi=pts.min(0),pts.max(0)
s=(gh[2]-gl[2])/(hi[2]-lo[2])
pts=pts*s; lo2,hi2=pts.min(0),pts.max(0)
off=np.array([(gl[0]+gh[0])/2-(lo2[0]+hi2[0])/2,(gl[1]+gh[1])/2-(lo2[1]+hi2[1])/2,gl[2]-lo2[2]])
print(f"[bbox중심 맞춤] 배율 {s:.3f}  오프셋 {np.round(off,4).tolist()}")
print(f"  프록시 원본 bbox x[{lo2[0]/s:+.3f},{hi2[0]/s:+.3f}] y[{lo2[1]/s:+.3f},{hi2[1]/s:+.3f}] "
      f"z[{lo2[2]/s:+.3f},{hi2[2]/s:+.3f}]")
print(f"  생성메시 bbox   x[{gl[0]:+.3f},{gh[0]:+.3f}] y[{gl[1]:+.3f},{gh[1]:+.3f}] "
      f"z[{gl[2]:+.3f},{gh[2]:+.3f}]")
import os as _os
if _os.environ.get("PROXY_NOSHIFT"):
    off=np.array([0.0,0.0,gl[2]-lo2[2]])
    print(f"[이동 없음]     배율 {s:.3f}  오프셋 {np.round(off,4).tolist()}")
HEAD=[n for n in V if n.startswith(("a_helm","a_brow","a_muzzle","a_eye"))]
print(f"\n{'프록시':18s} {'x':>18s} {'y':>18s} {'z':>18s} {'폭':>7s} {'높이':>7s}")
for n in sorted(HEAD)+["a_cuirass","a_shoulder","c_waist","c_shin","c_foot"]:
    if n not in V: continue
    v=V[n]*s+off
    print(f"{n:18s} [{v[:,0].min():+.3f},{v[:,0].max():+.3f}] "
          f"[{v[:,1].min():+.3f},{v[:,1].max():+.3f}] "
          f"[{v[:,2].min():+.3f},{v[:,2].max():+.3f}] "
          f"{v[:,0].max()-v[:,0].min():7.3f} {v[:,2].max()-v[:,2].min():7.3f}")
# 머리 전체
hv=np.vstack([V[n] for n in HEAD])*s+off
print(f"\n프록시 머리 전체: x[{hv[:,0].min():+.3f},{hv[:,0].max():+.3f}] "
      f"z[{hv[:,2].min():+.3f},{hv[:,2].max():+.3f}]  폭 {hv[:,0].max()-hv[:,0].min():.3f} "
      f"높이 {hv[:,2].max()-hv[:,2].min():.3f}")
