# 세 면 합치기: 부위마다 (정면 윤곽 × 옆 윤곽 · 높이 맞춤) → P2 · 3/4 윤곽으로 한 번 더 깎기 → P3. 좌표 (x오른, y아래, z앞)
import numpy as np, cv2, json, trimesh, os
from skimage import measure
D=json.load(open("cut/three_views.json",encoding="utf-8")); V=D["views"]; G=D["groups"]; u=0.5
Fall=np.vstack([np.array(c["poly"]) for c in V["정면"].values()]); xc=(Fall[:,0].min()+Fall[:,0].max())/2
Sall=np.vstack([np.array(c["poly"]) for c in V["옆"].values()]); umax=Sall[:,0].max()
X=np.arange(-70,70,u); Y=np.arange(-4,112,u); Z=np.arange(-10,100,u)
def raster(polys,a0,a1):
    m=np.zeros((len(a0),len(a1)),np.uint8)
    for p in polys: p=np.array(p,float); cv2.fillPoly(m,[np.c_[(p[:,1]-a1[0])/u,(p[:,0]-a0[0])/u].astype(np.int32)],1)
    return m.astype(bool)
parts=[]
for g in G:
    f=[np.array(V["정면"][str(n)]["poly"],float) for n in g["cells"]["정면"] if str(n) in V["정면"]]; s=[np.array(V["옆"][str(n)]["poly"],float) for n in g["cells"]["옆"] if str(n) in V["옆"]]
    if not f or not s: continue
    f=[np.c_[p[:,0]-xc,p[:,1]] for p in f]; s=[np.c_[umax-p[:,0],p[:,1]] for p in s]                    # 옆: z앞 = umax-u
    fy=np.vstack(f)[:,1]; sy=np.vstack(s)[:,1]; sz=np.vstack(s)[:,0]; k=(fy.max()-fy.min())/max(1e-6,sy.max()-sy.min()); k=float(np.clip(k,0.5,2.0))   # 부위별 크기 맞춤(만화 과장 흡수)
    zc=(sz.min()+sz.max())/2; s2=[np.c_[(p[:,0]-zc)*k+zc,(p[:,1]-(sy.min()+sy.max())/2)*k+(fy.min()+fy.max())/2] for p in s]
    Fm=raster(f,X,Y); Sm=raster(s2,Z,Y); Vx=Fm[:,:,None]&Sm.T[None,:,:]
    q=[np.array(V["3/4"][str(n)]["poly"],float) for n in g["cells"]["3/4"] if str(n) in V["3/4"]]
    color=V["정면"][str(g["cells"]["정면"][0])]["color"]; parts.append({"name":g["name"],"V2":Vx,"q":q,"k":round(k,2),"color":color})
    print(g["name"],"k",round(k,2),"복셀",int(Vx.sum()))
# 3/4: 얼굴이 화면 왼쪽을 봄 → w = x cosθ − z sinθ. 부위마다 높이 · 중심 맞춰 모양만 비교. θ 는 전체 IoU 최대
xi,yi,zi=np.meshgrid(X,Y,Z,indexing="ij")
def proj_iou(p,th,carve=False):
    Vx=p["V2"]; 
    if not p["q"] or Vx.sum()<20: return None
    w=xi*np.cos(th)-zi*np.sin(th); wv,yv=w[Vx],yi[Vx]; q=np.vstack(p["q"]); qh=q[:,1].max()-q[:,1].min(); kq=(yv.max()-yv.min())/max(1e-6,qh)
    qs=[np.c_[(pp[:,0]-(q[:,0].min()+q[:,0].max())/2)*kq,(pp[:,1]-(q[:,1].min()+q[:,1].max())/2)*kq] for pp in p["q"]]
    A=np.arange(-80,80,u); B=np.arange(-70,70,u); Qm=raster(qs,A,B); wc=(wv.min()+wv.max())/2; yc=(yv.min()+yv.max())/2
    ia=np.clip(((wv-wc-A[0])/u).astype(int),0,len(A)-1); ib=np.clip(((yv-yc-B[0])/u).astype(int),0,len(B)-1); Pm=np.zeros_like(Qm); Pm[ia,ib]=True; Pm=cv2.morphologyEx(Pm.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)).astype(bool)
    iou=(Pm&Qm).sum()/max(1,(Pm|Qm).sum())
    if not carve: return iou
    Qd=cv2.dilate(Qm.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)      # 여유 1 단위
    keep=Qd[np.clip(((w-wc-A[0])/u).astype(int),0,len(A)-1),np.clip(((yi-yc-B[0])/u).astype(int),0,len(B)-1)]; return iou,Vx&keep
best=max(((np.mean([v for v in (proj_iou(p,np.radians(t)) for p in parts) if v is not None]),t) for t in range(15,71,5))); th=np.radians(best[1]); print("3/4 각도",best[1],"평균 IoU",round(best[0],3))
os.makedirs("cut/merge/obj",exist_ok=True); idx=[]
def save(Vx,path):
    if Vx.sum()<20: return False
    verts,faces,_,_=measure.marching_cubes(np.pad(Vx,1).astype(np.float32),0.5,spacing=(u,u,u)); verts+=np.array([X[0]-u,Y[0]-u,Z[0]-u]); m=trimesh.Trimesh(verts,faces,process=True); trimesh.smoothing.filter_laplacian(m,lamb=0.4,iterations=5); m.export(path); return True
for i,p in enumerate(parts):
    r=proj_iou(p,th,carve=True); V3=r[1] if r else p["V2"]; iou=r[0] if r else None
    a=save(p["V2"],f"cut/merge/obj/P2_{i}.obj"); b=save(V3,f"cut/merge/obj/P3_{i}.obj")
    idx.append({"i":i,"name":p["name"],"color":p["color"],"k":p["k"],"P2":a,"P3":b,"iou34":None if iou is None else round(float(iou),2),"keep":round(float(V3.sum()/max(1,p["V2"].sum())),2)}); print(p["name"],"3/4 IoU",idx[-1]["iou34"],"남은 비율",idx[-1]["keep"])
json.dump({"parts":idx,"yaw34":best[1]},open("cut/merge/index.json","w",encoding="utf-8"),ensure_ascii=False)
