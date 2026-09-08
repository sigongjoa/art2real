# -*- coding: utf-8 -*-
"""표면의 가로 골판지 무늬를 수치로. 다리 앞면 y(z) 의 2차차분."""
import os, sys
import bpy, numpy as np
for p in sys.argv[sys.argv.index("--")+1:]:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(p))
    o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v); v=v.reshape(-1,3)
    out=[]
    for lo,hi,nm in ((0.18,0.40,"정강이"),(0.60,0.80,"몸통")):
        m=(v[:,2]>lo)&(v[:,2]<hi)&(np.abs(v[:,0]-0.14)<0.05)
        if m.sum()<200: out.append((nm,0)); continue
        z=v[m,2]; y=v[m,1]
        # 계단 주기가 약 1.2mm(1024행) 라 140칸(1.6mm)으로는 나이퀴스트에 걸려
        # 아예 안 보인다. 0.4mm 칸으로 잘게 쪼갠다.
        nb=int((hi-lo)/0.0002)
        edges=np.linspace(lo,hi,nb+1)
        idx=np.clip(np.digitize(z,edges)-1,0,nb-1)
        front=np.full(nb,np.nan)
        for i in range(nb):
            s=y[idx==i]
            if len(s)>=3: front[i]=np.percentile(s,3)
        ok=~np.isnan(front)
        f=np.interp(np.arange(nb),np.nonzero(ok)[0],front[ok])
        d=hi-lo
        depth=np.percentile(y,97)-np.percentile(y,3)
        # 깊이로 정규화 — 깊이를 눌렀으니 절대 진폭만 보면 항상 줄어 보인다
        out.append((nm, np.std(np.diff(f,2))/max(depth,1e-9)*1e3))
    print(f"{os.path.basename(p):20s} " + "  ".join(f"{n} 거칠기 {r:7.1f}" for n,r in out))
