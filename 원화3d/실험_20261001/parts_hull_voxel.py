# 부품별 정면 기둥 ∩ 옆 기둥 (A) · ∩ TripoSG (B, 마스크·투구만) — 복셀 교집합 → 마칭큐브 → OBJ. 좌표 (x오른, y아래, z앞)
import numpy as np, cv2, json, trimesh, os
from skimage import measure
D=json.load(open("cut/parts_hull.json",encoding="utf-8")); parts=D["parts"]; u=0.5
X=np.arange(-66,66,u); Y=np.arange(-2,110,u); Z=np.arange(-12,82,u)
def mask2d(polys, ax0, ax1, dy=0):
    m=np.zeros((len(ax0),len(ax1)),np.uint8)
    for poly in polys:
        p=np.array(poly,float)
        if dy: yc=p[:,1].mean(); p[:,1]+=np.where(p[:,1]>yc,dy,-dy)
        pts=np.c_[(p[:,1]-ax1[0])/u,(p[:,0]-ax0[0])/u].astype(np.int32)   # (col=axis1, row=axis0)
        cv2.fillPoly(m,[pts],1)
    return m.astype(bool)
# TripoSG 복셀(채움)
tri=trimesh.load("cut/tripo_units.obj",process=True); V3=tri.vertices; F3=tri.faces
zmax=np.full((len(X),len(Y)),-1e9); zmin=np.full((len(X),len(Y)),1e9)
for f in F3:
    tv=V3[f]; pts=np.c_[(tv[:,1]-Y[0])/u,(tv[:,0]-X[0])/u].astype(np.int32); mz=np.zeros((len(X),len(Y)),np.uint8); cv2.fillPoly(mz,[pts],1); mm=mz.astype(bool)
    zmax[mm]=np.maximum(zmax[mm],tv[:,2].max()); zmin[mm]=np.minimum(zmin[mm],tv[:,2].min())
T=(Z[None,None,:]<=zmax[:,:,None])&(Z[None,None,:]>=zmin[:,:,None]); print("tripo voxels",T.sum())
sideall=mask2d([D["side_all"]],Z,Y)
os.makedirs("cut/hullobj",exist_ok=True); out=[]
for p in parts:
    F=mask2d(p["front"],X,Y); S=mask2d(p["side"],Z,Y,dy=6)
    for var in ("A","B"):
        V=F[:,:,None]&S.T[None,:,:]
        if V.sum()<30: V=F[:,:,None]&sideall.T[None,:,:]; fb=True
        else: fb=False
        if var=="B" and p["layer"]!="속머리(눈)":
            V2=V&T
            if V2.sum()<30: V2=np.zeros_like(V)
            V=V2
        n=int(V.sum())
        if n<10: out.append({"name":p["name"],"var":var,"vox":0}); continue
        verts,faces,_,_=measure.marching_cubes(np.pad(V,1).astype(np.float32),0.5,spacing=(u,u,u)); verts+=np.array([X[0]-u,Y[0]-u,Z[0]-u])
        m=trimesh.Trimesh(verts,faces,process=True); trimesh.smoothing.filter_laplacian(m,lamb=0.3,iterations=3); m.export(f"cut/hullobj/{var}_{p['name']}.obj")
        out.append({"name":p["name"],"var":var,"vox":n,"fallback":fb,"layer":p["layer"]}); print(var,p["name"],n,"대체" if fb else "")
json.dump(out,open("cut/hullobj/index.json","w",encoding="utf-8"),ensure_ascii=False)
