# -*- coding: utf-8 -*-
"""먹선을 「물체 선」과 「방향 선」으로 가른다 (10-02 사용자 「1번은 구분한 이미지 만들어줘」).
선(세선) 화소마다 선에 수직으로 양쪽을 d 만큼 떨어져 색을 잰다(Lab).
  방향 선 — 외곽: 윤곽 가까이 · 가림: 한쪽이 윤곽 밖(배경)  → 빨강
  방향 선 — 그림자: 양쪽 색상(a,b) 같고 밝기만 크게 다름   → 주황
  물체 선 — 색 경계: 양쪽 색상(a,b)이 다름(파랑 번개 · 검은 눈구멍 · 노란 뿔) → 초록
  물체 선 — 홈 · 접힘: 양쪽 색 · 밝기 거의 같음             → 하늘
팔레트(검정 · 유채색 6 구간 · 무채) 가 양쪽에서 다르면 색 경계 · 같고 밝기만 다르면 그림자. 문턱은 Lab 단위로 고정(사람이 정한 숫자 · 눈으로 확인용)."""
import os, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
R=r"G:\art2real\원화3d\out\오메가몬2"; K=R+r"\지표"; A=R+r"\자료"; O=K+r"\세면"
기록=json.load(open(A+r"\자료.json",encoding="utf-8")); HP=600; u=HP/100
면={"정면":("02_정면","윤곽3_정면_전체.npy"),"옆":("02_옆","윤곽3_옆_전체.npy"),"3/4":("02_3-4","윤곽2_3-4_전체.npy")}
색={"외곽·가림":(230,60,60),"그림자":(255,160,40),"색 경계":(60,210,90),"홈·접힘":(80,200,255)}
tiles=[]; 표={}
for 이름,(장,npy) in 면.items():
    im=cv2.imdecode(np.fromfile(기록[장]["파일"],np.uint8),cv2.IMREAD_COLOR); 윤곽=np.load(K+"\\"+npy).astype(float); hh=윤곽[:,1].max()-윤곽[:,1].min(); s=HP/hh
    big=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC); 윤=(윤곽*s).astype(np.int32); H,W=big.shape[:2]
    안=np.zeros((H,W),np.uint8); cv2.fillPoly(안,[윤],1); 안=안.astype(bool)
    g=cv2.cvtColor(cv2.bilateralFilter(big,7,30,7),cv2.COLOR_BGR2GRAY); lo,hi=np.percentile(g[안],[2,98]); gs=np.clip((g.astype(float)-lo)*255/max(1,hi-lo),0,255).astype(np.uint8)
    kb=int(1.8*u)|1; bh=cv2.morphologyEx(gs,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(kb,kb))); 먹=(bh>max(18,np.percentile(bh[안],90)))&안
    먹=cv2.morphologyEx(먹.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)); n,lab,st,_=cv2.connectedComponentsWithStats(먹,8); 먹=np.isin(lab,[i for i in range(1,n) if st[i,cv2.CC_STAT_AREA]>=int(0.6*u*u)])
    sk=cv2.ximgproc.thinning(먹.astype(np.uint8)*255)>0 if hasattr(cv2,"ximgproc") else 먹
    lab_im=cv2.cvtColor(big,cv2.COLOR_BGR2LAB).astype(float); Lb=cv2.GaussianBlur(lab_im,(5,5),0)
    gx=cv2.Sobel(먹.astype(np.float32),cv2.CV_32F,1,0,ksize=5); gy=cv2.Sobel(먹.astype(np.float32),cv2.CV_32F,0,1,ksize=5)
    # 선 방향: 구조 텐서로(선에 수직 = 고유벡터)
    Jxx=cv2.GaussianBlur(gx*gx,(9,9),0); Jyy=cv2.GaussianBlur(gy*gy,(9,9),0); Jxy=cv2.GaussianBlur(gx*gy,(9,9),0); ang=0.5*np.arctan2(2*Jxy,Jxx-Jyy)
    ys,xs=np.nonzero(sk); nx,ny=np.cos(ang[ys,xs]),np.sin(ang[ys,xs]); d=1.2*u
    def samp(px,py): px=np.clip(px.round().astype(int),0,W-1); py=np.clip(py.round().astype(int),0,H-1); return Lb[py,px],안[py,px]
    c1,i1=samp(xs+nx*d,ys+ny*d); c2,i2=samp(xs-nx*d,ys-ny*d)
    dist_edge=cv2.distanceTransform(안.astype(np.uint8),cv2.DIST_L2,3)[ys,xs]
    dL=np.abs(c1[:,0]-c2[:,0]); dab=np.hypot(c1[:,1]-c2[:,1],c1[:,2]-c2[:,2])
    # 팔레트 이름: 검정(머리 안 밝기 하위 기준) · 유채색(채도>14 → 색상 구간 6) · 무채(흰 갑주와 그 그림자 톤은 같은 팔레트)
    Lin=Lb[안][:,0]; Lblack=np.percentile(Lin,12)*0.9+5
    def pal(c):
        L,a,b=c[:,0],c[:,1]-128,c[:,2]-128; ch=np.hypot(a,b); hue=((np.degrees(np.arctan2(b,a))+360)//60).astype(int)
        return np.where(L<Lblack,-1,np.where(ch>14,hue,-2))
    p1,p2=pal(c1),pal(c2)
    cls=np.full(len(xs),"홈·접힘",object)
    cls[(p1==p2)&(dL>30)]="그림자"; cls[p1!=p2]="색 경계"; cls[(dist_edge<1.0*u)|(~i1)|(~i2)]="외곽·가림"
    t=(big*0.45).astype(np.uint8); 
    for k,c in 색.items():
        m=np.zeros((H,W),bool); sel=cls==k; m[ys[sel],xs[sel]]=True; m=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool); t[m]=c[::-1]
    cv2.polylines(t,[윤],True,색["외곽·가림"][::-1],2)
    cnt={k:int((cls==k).sum()) for k in 색}; tot=max(1,sum(cnt.values())); 표[이름]={k:round(v/tot,2) for k,v in cnt.items()}
    y0,y1,x0,x1=max(0,윤[:,1].min()-15),윤[:,1].max()+15,max(0,윤[:,0].min()-15),윤[:,0].max()+15; t=t[y0:y1,x0:x1]; t=cv2.resize(t,(int(t.shape[1]*640/t.shape[0]),640)); tiles.append((t,이름))
    print(이름,표[이름])
img=Image.fromarray(np.hstack([t for t,_ in tiles])[:,:,::-1]); out=Image.new("RGB",(img.width,740),(20,20,24)); out.paste(img,(0,50)); d=ImageDraw.Draw(out); f=ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf",24); fs=ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf",20); x=0
for t,name in tiles:
    p=표[name]; d.text((x+8,12),name,font=f,fill=(255,255,255)); x+=t.shape[1]
x=10
for k,c in 색.items():
    kind="방향 선" if k in ("외곽·가림","그림자") else "물체 선"; d.rectangle((x,702,x+22,724),fill=c); d.text((x+30,700),f"{kind} · {k}",font=fs,fill=(230,230,230)); x+=300
out.save(O+"\선종류_세면.png"); json.dump(표,open(O+"\선종류.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
