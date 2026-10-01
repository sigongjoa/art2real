# 선 대조: 원화 먹선 벽(선파츠 라벨 경계) vs 모델 Freestyle 선 — 파츠별 재현율 · 거짓 선 비율. 사용: python line_compare.py <접두(tri|cut)>
import sys, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
pre=sys.argv[1]; K=r"G:\art2real\원화3d\out\오메가몬2\지표"; A=r"G:\art2real\원화3d\out\오메가몬2\자료"; 기록=json.load(open(A+r"\자료.json",encoding="utf-8")); d=6; out={}
for 장,키 in (("02_정면","정면"),("02_옆","옆")):
    im=cv2.imdecode(np.fromfile(기록[장]["파일"],np.uint8),cv2.IMREAD_COLOR); H,W=im.shape[:2]; x0,y0,x1,y1=기록[장]["상자"]
    z=np.load(f"{K}/선파츠_{키}.npz"); 라벨=z["라벨"]; 면표=json.loads(str(z["면표"])); 안=라벨>0
    # 벽 = 라벨이 바뀌는 자리(3x3 안에 다른 라벨) · 바깥 윤곽 포함
    mx=cv2.dilate(라벨.astype(np.float32),np.ones((3,3),np.uint8)); mn=-cv2.dilate((-라벨).astype(np.float32),np.ones((3,3),np.uint8)); 벽=(mx!=mn)&cv2.dilate(안.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    r=np.array(Image.open(f"cut/{pre}_{키}.png").convert("RGBA")); 모델선=(r[:,:,3]>0)&(r[:,:,:3].mean(2)<80); 모델안=r[:,:,3]>0
    if pre.startswith("uv"):   # 텍스처 렌더: 어두운 면이 아니라 가는 먹선만(선파츠.py 와 같은 블랙햇 ∪ 적응 문턱)
        g=cv2.cvtColor(r[:,:,:3],cv2.COLOR_RGB2GRAY); g[~모델안]=255; bh=cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
        모델선=((bh>18)|(cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,25,6)>0))&cv2.erode(모델안.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
    # 2D 유사 맞춤(배율 · 이동): 모델 실루엣 → 윤곽3 안. 카메라가 뷰마다 따로라 세계 z 가 안 맞는다(10-01)
    def warp(m,s,tx,ty,shape): A=np.float32([[s,0,tx],[0,s,ty]]); return cv2.warpAffine(m.astype(np.uint8),A,(shape[1],shape[0]),flags=cv2.INTER_NEAREST)>0
    k=4; a4=cv2.resize(안.astype(np.uint8),(W//k,H//k),interpolation=cv2.INTER_NEAREST)>0; m4=cv2.resize(모델안.astype(np.uint8),(W//k,H//k),interpolation=cv2.INTER_NEAREST)>0
    ya,xa=np.nonzero(a4); ym,xm=np.nonzero(m4); best=None
    for s in np.arange(0.7,1.45,0.05):
        for tx in range(-40,41,3):
            for ty in range(-40,41,3):
                tx0=xa.mean()-s*xm.mean()+tx; ty0=ya.mean()-s*ym.mean()+ty; w=warp(m4,s,tx0,ty0,a4.shape); v=(w&a4).sum()/max(1,(w|a4).sum())
                if best is None or v>best[0]: best=(v,s,tx0*k,ty0*k)
    if 키!="옆": best=(float((모델안&안).sum()/max(1,(모델안|안).sum())),1.0,0.0,0.0)   # 정면은 카메라가 맞으니 그대로
    _,s,tx,ty=best; 모델선=warp(모델선,s,tx,ty,안.shape); 모델안=warp(모델안,s,tx,ty,안.shape); print(" 2D 맞춤",round(s,2),round(tx),round(ty),"IoU",round(best[0],3))
    근처=cv2.dilate(모델선.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*d+1,2*d+1)))>0; 벽근처=cv2.dilate(벽.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*d+1,2*d+1)))>0
    재현=(벽&근처).sum()/벽.sum(); 거짓=((모델선&안)&~벽근처).sum()/max(1,(모델선&안).sum()); 실루엣=(안&모델안).sum()/(안|모델안).sum()
    표=[]
    for f in 면표:
        m=cv2.dilate((라벨==f["번호"]).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&벽; 표.append({"번호":f["번호"],"재현율":round(float((m&근처).sum()/max(1,m.sum())),2)})
    out[장]={"벽재현율":round(float(재현),3),"거짓선비율":round(float(거짓),3),"실루엣IoU":round(float(실루엣),3),"파츠":표,"d":d}
    print(장,"벽 재현율",round(재현,3),"거짓선",round(거짓,3),"실루엣 IoU",round(실루엣,3),"파츠 재현율≥0.5:",sum(t["재현율"]>=0.5 for t in 표),"/",len(표))
    # 그림: 원화 + 빨강 벽 + 파랑 모델선 ; 오른쪽 파츠별 재현율 색(초록 1 → 빨강 0)
    t=im.copy(); t[벽]=(0,0,255); t[모델선]=(255,120,0); 
    t2=im.copy(); ov=t2.copy()
    for f,s in zip(면표,표):
        m=라벨==f["번호"]; c=np.array([0,int(255*s["재현율"]),int(255*(1-s["재현율"]))]); ov[m]=c
    t2=cv2.addWeighted(t2,0.4,ov,0.6,0); t2[모델선]=(255,120,0)
    pad=60; X0,Y0,X1,Y1=max(0,x0-pad),max(0,y0-pad),min(W,x1+pad),min(H,y1+pad); tiles=[]
    for name,tt in (("원화 벽(빨강) · 모델 선(파랑)",t),("파츠별 재현율 (초록 1 · 빨강 0)",t2)):
        tt=tt[Y0:Y1,X0:X1]; sc=560/tt.shape[0]; tt=cv2.resize(tt,(int(tt.shape[1]*sc),560)); cv2.rectangle(tt,(0,0),(tt.shape[1],36),(0,0,0),-1); tiles.append((tt,name))
    img=Image.fromarray(np.hstack([a for a,_ in tiles])[:,:,::-1]); dr=ImageDraw.Draw(img); ft=ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf",22); x=0
    for tt,name in tiles: dr.text((x+8,6),name,font=ft,fill=(255,255,255)); x+=tt.shape[1]
    dr.text((8,540),f"{pre} · 벽 재현율 {재현:.2f} · 거짓 선 {거짓:.2f} · 실루엣 IoU {실루엣:.2f}",font=ft,fill=(255,255,0),stroke_width=2,stroke_fill=(0,0,0))
    img.save(f"cut/선대조_{pre}_{키}.png")
json.dump(out,open(f"cut/선대조_{pre}.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
