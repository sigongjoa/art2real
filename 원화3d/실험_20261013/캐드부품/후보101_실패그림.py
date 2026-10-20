import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
O="G:/art2real/out/설명/캐드부품/"; plt.rcParams["font.family"]="Malgun Gothic"
d=np.load(O+"데이터.npz"); X=d["X"]; e=np.load(O+"데이터_앞옆.npz"); F,S=e["F"],e["S"]; h=np.load(O+"숨은선88.npz"); HX,HF,HS=h["HX"],h["HF"],h["HS"]
z=np.load(O+"후보101_실패.npz"); 부=list(z["부품"]); 지=np.unpackbits(z["지도"],axis=-1)>0; 층=np.load(O+"층32.npy",mmap_mode="r"); 입=np.load(O+"입력51.npy",mmap_mode="r")
ps=[574,1588,1034,2741,2228,904]
fig,ax=plt.subplots(len(ps),5,figsize=(17,3.5*len(ps)))
for r,i in enumerate(ps):
    t=부.index(i); n=int(np.argmax(z["빠수"][t]))
    for j,(a,b,nm) in enumerate(((X,HX,"위"),(F,HF,"앞"),(S,HS,"옆"))):
        img=np.ones((128,128,3)); img[b[i]>0]=(.5,.7,1); img[a[i]>0]=0; ax[r,j].imshow(img); ax[r,j].set_title(f"부품 {i} {nm} 도면"); ax[r,j].axis("off")
    g=층[i,n].astype(float); 안=(입[i,n,1]>0)&(g<32); ax[r,3].imshow(np.where(안,g,np.nan)); ax[r,3].set_title(f"방향 {n} 정답 층"); ax[r,3].axis("off")
    im=np.ones((128,128,3)); im[안]=.85; im[지[t,n]]=(.85,.2,.2); ax[r,4].imshow(im); ax[r,4].set_title(f"빨강 = 후보에 정답 없음 {z['빠수'][t,n]}/{z['깎수'][t,n]}"); ax[r,4].axis("off")
plt.tight_layout(); plt.savefig(O+"후보101_실패부품.png",dpi=70)
