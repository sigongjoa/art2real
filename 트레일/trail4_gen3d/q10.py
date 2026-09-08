# -*- coding: utf-8 -*-
"""좌우 다리의 깊이(y)가 실제로 다른가. 파츠 라벨 말고 정점으로."""
import os, sys
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index("--")+1]))
o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v); v=v.reshape(-1,3)
print(f"{'z':>5s} | {'왼다리(x<-0.05) y':>22s} {'중심':>7s} | {'오른다리(x>0.05) y':>22s} {'중심':>7s} | {'중심차':>7s}")
for z in (0.10,0.18,0.25,0.32,0.40,0.50):
    row=[f"{z:5.2f} |"]
    ctr=[]
    for lo,hi in ((-0.34,-0.05),(0.05,0.34)):
        m=(np.abs(v[:,2]-z)<0.008)&(v[:,0]>lo)&(v[:,0]<hi)
        if m.sum()<30: row.append(f"{'-':>22s} {'-':>7s} |"); ctr.append(None); continue
        y=v[m,1]; a,b=np.percentile(y,1),np.percentile(y,99)
        row.append(f" [{a:+.3f},{b:+.3f}] 폭{b-a:.3f} {(a+b)/2:+7.3f} |")
        ctr.append((a+b)/2)
    d=(ctr[0]-ctr[1]) if all(x is not None for x in ctr) else 0
    row.append(f" {d:+7.3f}")
    print("".join(row))
# 검을 뺀 왼다리
print("\n검(x -0.33~-0.22) 제외 왼다리:")
for z in (0.18,0.25,0.32):
    m=(np.abs(v[:,2]-z)<0.008)&(v[:,0]>-0.20)&(v[:,0]<-0.05)
    if m.sum()<30: continue
    y=v[m,1]; a,b=np.percentile(y,1),np.percentile(y,99)
    m2=(np.abs(v[:,2]-z)<0.008)&(v[:,0]>0.05)&(v[:,0]<0.20)
    y2=v[m2,1]; a2,b2=np.percentile(y2,1),np.percentile(y2,99)
    print(f"  z{z:.2f} 왼 [{a:+.3f},{b:+.3f}] 중심{(a+b)/2:+.3f}   "
          f"오른 [{a2:+.3f},{b2:+.3f}] 중심{(a2+b2)/2:+.3f}   차 {(a+b)/2-(a2+b2)/2:+.3f}")
