import numpy as np, 후보96 as H, 후보101 as P, 여섯방향 as S6
O=P.O; K=32
d=np.load(O+"데이터.npz"); X=d["X"]; e=np.load(O+"데이터_앞옆.npz"); F,S=e["F"],e["S"]; h=np.load(O+"숨은선88.npz"); HX,HF,HS=h["HX"],h["HF"],h["HS"]; 반=np.load(O+"데이터51.npz")["반"]
I=np.load(O+"후보96_색인.npy").astype(np.int64); 층=np.load(O+"층32.npy",mmap_mode="r"); 입=np.load(O+"입력51.npy",mmap_mode="r"); 껍=np.load(O+"껍질32.npy",mmap_mode="r")
z=np.load(O+"후보101_실패.npz"); 부=z["부품"]; 지=np.unpackbits(z["지도"],axis=-1)>0
날=lambda a,b,c:{2:(b,c),1:(a,c.T),0:(a.T,b.T)}
a=np.zeros(4)
for t,i in enumerate(부):
    if not 지[t].any(): continue
    H.열후보=날; C=H.하나(X[i],F[i],S[i],HX[i],HF[i],HS[i],반[i])
    for n in range(6):
        m=지[t,n]
        if not m.any(): continue
        q=(C[n,0][I[n,0]]|C[n,1][I[n,1]]).astype(np.int64); g=층[i,n].astype(np.int64); s=껍[i,n].astype(np.int64)
        bit=lambda L:((q>>np.clip(L,0,31))&1)>0; 곁=bit(g)|bit(g-1)|bit(g+1)
        cpl=(2*반[i][n]/K)/S6.칸
        a+=[m.sum(),(m&곁).sum(),(m&(cpl<.5)).sum(),(m&(g>=30)).sum()]
print("빠진 화소",a[0],"· 날 선(세로선 안 지움)이면 들어옴",a[1]/a[0],"· 얇은 부품(층<0.5화소)",a[2]/a[0],"· 정답 층 ≥30(뒤 끝)",a[3]/a[0])
