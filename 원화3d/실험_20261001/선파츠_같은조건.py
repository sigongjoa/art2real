# -*- coding: utf-8 -*-
"""세 면을 같은 조건으로 먹선 분할 (10-02 사용자 「그림에 따라 너무 많이도 작게도 나눠진다」).
머리 높이(윤곽 위~아래)를 HP 픽셀로 맞춘 뒤, 필터 · 닫힘 · 최소 면적을 머리 단위로 고정. 나머지 규칙은 선파츠.py 와 같다.
    python 선파츠_같은조건.py [HP=600] -> out/오메가몬2/지표/세면/같은조건_<면>.png · 선파츠2_<면>.npz · 같은조건.json"""
import os, sys, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
R=r"G:\art2real\원화3d\out\오메가몬2"; K=R+r"\지표"; A=R+r"\자료"; O=K+r"\세면"; os.makedirs(O,exist_ok=True)
기록=json.load(open(A+r"\자료.json",encoding="utf-8")); HP=int(sys.argv[1]) if len(sys.argv)>1 else 600
# 머리 단위(머리 높이 = 100) 고정값
BH=1.8; 닫힘=1.5; 최소=0.35   # 블랙햇 지름 · 닫힘 크기 · 최소 칸 면적(머리 높이² 의 %)
면={"정면":("02_정면","윤곽3_정면_전체.npy"),"옆":("02_옆","윤곽3_옆_전체.npy"),"3/4":("02_3-4","윤곽2_3-4_전체.npy")}
결과={}; tiles=[]
for 이름,(장,npy) in 면.items():
    im=cv2.imdecode(np.fromfile(기록[장]["파일"],np.uint8),cv2.IMREAD_COLOR); 윤곽=np.load(K+"\\"+npy).astype(float)
    hh=윤곽[:,1].max()-윤곽[:,1].min(); s=HP/hh; big=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC if s>1 else cv2.INTER_AREA); 윤=(윤곽*s).astype(np.int32)
    g=cv2.cvtColor(cv2.bilateralFilter(big,7,30,7),cv2.COLOR_BGR2GRAY); 안=np.zeros(g.shape,np.uint8); cv2.fillPoly(안,[윤],1); 안=안.astype(bool)
    lo,hi=np.percentile(g[안],[2,98]); g=np.clip((g.astype(float)-lo)*255/max(1,hi-lo),0,255).astype(np.uint8)
    u=HP/100; kb=max(3,int(BH*u)|1); kc=max(2,int(닫힘*u)); ka=max(9,int(4*u)|1)
    bh=cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(kb,kb))); 먹=bh>max(18,np.percentile(bh[안],90))
    적=cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,ka,6)>0
    L=g.astype(float); 어둠=(L<0.35*np.median(L[안]))&안; 어둠=cv2.morphologyEx(어둠.astype(np.uint8),cv2.MORPH_OPEN,np.ones((max(3,int(u)),)*2,np.uint8))>0
    선=(먹|적)&안&~cv2.erode(어둠.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool); 벽=선.copy(); cv2.polylines(벽.view(np.uint8),[윤],True,1,3); 벽=cv2.morphologyEx(벽.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((kc,kc),np.uint8))>0
    n,lab=cv2.connectedComponents((안&~벽).astype(np.uint8),connectivity=4); 면적=np.bincount(lab.ravel(),minlength=n); 최소px=최소/100*HP*HP
    for _ in range(6):
        작은=[i for i in range(1,n) if 0<면적[i]<최소px]
        if not 작은: break
        for i in 작은:
            m=lab==i; 둘레=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&~m; 이웃=lab[둘레]; 이웃=이웃[(이웃!=0)&(이웃!=i)]
            if len(이웃): j=np.bincount(이웃).argmax(); lab[m]=j; 면적[j]+=면적[i]; 면적[i]=0
    ids=[i for i in range(1,n) if 면적[i]>0]; 라벨=np.zeros_like(lab)
    for k,i in enumerate(ids): 라벨[lab==i]=k+1
    dist,idx=cv2.distanceTransformWithLabels((라벨==0).astype(np.uint8),cv2.DIST_L2,3,labelType=cv2.DIST_LABEL_PIXEL); ys,xs=np.nonzero(라벨>0); 참조=np.zeros(idx.max()+1,np.int32); 참조[idx[ys,xs]]=라벨[ys,xs]; 라벨=np.where((라벨==0)&안,참조[idx],라벨); 라벨[~안]=0
    np.savez_compressed(O+"\선파츠2_%s.npz"%이름.replace("/","-"),라벨=라벨,s=s)
    결과[이름]={"칸":len(ids),"머리px_원래":round(hh),"배율":round(s,2)}; print(이름,결과[이름])
    rng=np.random.RandomState(3); 팔=rng.randint(70,240,(len(ids)+2,3)); ov=big.copy(); m=라벨>0; ov[m]=팔[라벨[m]]; t=cv2.addWeighted(big,0.45,ov,0.55,0)
    mx=cv2.dilate(라벨.astype(np.float32),np.ones((3,3),np.uint8)); mn=-cv2.dilate((-라벨).astype(np.float32),np.ones((3,3),np.uint8)); t[(mx!=mn)&m]=(0,0,0)
    ys,xs=np.nonzero(m); t=t[max(0,ys.min()-15):ys.max()+15,max(0,xs.min()-15):xs.max()+15]; t=cv2.resize(t,(int(t.shape[1]*640/t.shape[0]),640)); tiles.append((t,"%s · %d칸 (원래 머리 %dpx → %d)"%(이름,len(ids),hh,HP)))
img=Image.fromarray(np.hstack([t for t,_ in tiles])[:,:,::-1]); W=img.width; out=Image.new("RGB",(W,690),(20,20,24)); out.paste(img,(0,50)); d=ImageDraw.Draw(out); f=ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf",24); x=0
for t,name in tiles: d.text((x+8,12),name,font=f,fill=(255,232,58)); x+=t.shape[1]
out.save(O+"\같은조건_세면.png"); json.dump({"HP":HP,"머리단위":{"블랙햇":BH,"닫힘":닫힘,"최소면적%":최소},"면":결과},open(O+"\같은조건.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
