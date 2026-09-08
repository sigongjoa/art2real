# -*- coding: utf-8 -*-
"""계단(골판지)의 고유 주파수 성분만 뽑는다.

z 를 1024행으로 양자화하면 주기 (Z1-Z0)/1024 = 1.17mm 의 줄무늬가 생긴다.
그 파장 부근의 스펙트럼 파워를 전체 파워로 나눠 본다.
"""
import os, sys
import bpy, numpy as np
STEP=0.0002                      # 0.2mm 표본
PER=(1.1-(-0.1))/1024            # 계단 주기 1.17mm
for p in sys.argv[sys.argv.index("--")+1:]:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(p))
    o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get("co",v); v=v.reshape(-1,3)
    res=[]
    for lo,hi,nm in ((0.18,0.40,"정강이"),(0.60,0.80,"몸통")):
        m=(v[:,2]>lo)&(v[:,2]<hi)&(np.abs(v[:,0]-0.14)<0.05)
        z=v[m,2]; y=v[m,1]
        nb=int((hi-lo)/STEP)
        idx=np.clip(((z-lo)/STEP).astype(int),0,nb-1)
        f=np.full(nb,np.nan)
        for i in range(nb):
            s=y[idx==i]
            if len(s)>=2: f[i]=np.percentile(s,3)
        ok=~np.isnan(f)
        if ok.sum()<nb*0.3: res.append((nm,0,0)); continue
        f=np.interp(np.arange(nb),np.nonzero(ok)[0],f[ok])
        f=f-np.convolve(np.pad(f,(40,40),mode='edge'),np.ones(81)/81,mode='same')[40:-40]
        F=np.abs(np.fft.rfft(f*np.hanning(nb)))**2
        fr=np.fft.rfftfreq(nb,STEP)          # 1/길이
        tgt=1.0/PER
        band=(fr>tgt*0.75)&(fr<tgt*1.35)
        res.append((nm, F[band].sum()/max(F[1:].sum(),1e-30)*100,
                    fr[1:][np.argmax(F[1:])]))
    print(f"{os.path.basename(p):18s} " +
          "  ".join(f"{n} 계단대역 {a:5.1f}% 최강주기 {1000/max(b,1e-9):5.2f}mm" for n,a,b in res))
