# 먹선을 TripoSG 에 — 09-21 매끈먹선 방식: 표면을 먼저 매끈하게(라플라시안) → 잘게 → 09-29 선화 먹선 거리장 V 홈 · 검은면 깊게. 정면 카메라 좌표에서 작업(hull_groove.py 와 같은 틀)
import numpy as np, cv2, json, trimesh
from scipy.ndimage import distance_transform_edt, map_coordinates
K=r"G:\art2real\원화3d\out\오메가몬2\지표"; cams=json.load(open("cut/cams.json")); fit=json.load(open("cut/fit.json"))
cF=cams["카메라_02_정면"]; MF=np.array(cF["M"]); MFi=np.linalg.inv(MF); W,H,sF=cF["W"],cF["H"],cF["ortho"]; k=W/sF
d=np.load("cut/tri_world.npz"); V=d["V"]; F=d["F"]
V=(V-np.array([140,0,0]))*fit["s"]+np.array([fit["dx"],fit["dy"],fit["dz"]])            # #9 때 실루엣 맞춤
Vc=(MFi[:3,:3]@V.T).T+MFi[:3,3]                                                            # 정면 카메라 좌표
m=trimesh.Trimesh(Vc,F,process=True)
# 깃 제거: 정면 마스크 맨 아래 행(턱)보다 낮은 점
def mask(key):
    mm=np.zeros((H,W),np.uint8); cv2.fillPoly(mm,[np.load(f"{K}/윤곽3_{key}_전체.npy").astype(np.int32)],1); return mm.astype(bool)
mF,mS=mask("정면"),mask("옆"); yF=np.nonzero(mF.any(1))[0]; ychin=(0.5-(yF.max()+8)/H)*sF*H/W
keep=m.vertices[:,1]>ychin; fk=keep[m.faces].all(1); m=trimesh.Trimesh(m.vertices,m.faces[fk],process=True); m=max(m.split(only_watertight=False),key=lambda t:len(t.faces))
print("머리 점",len(m.vertices)); m.export("cut/tripoA_groove.obj"); trimesh.smoothing.filter_laplacian(m,lamb=0.5,iterations=25); m.export("cut/tripoB_groove.obj")     # 매끈하게 — 10-01 #10 긁힘의 원인은 울퉁불퉁한 바탕
m=trimesh.Trimesh(*trimesh.remesh.subdivide_to_size(m.vertices,m.faces,max_edge=0.4)); print("잘게",len(m.vertices))
def fpx(P): return np.c_[(P[:,0]/sF+0.5)*W,(0.5-P[:,1]/(sF*H/W))*H]
# 옆 뷰(수식): u = ucen - z*k + 깊이 맞춤 · v = 정면 행 + 턱 맞춤
yS=np.nonzero(mS.any(1))[0]; ty=yS.max()-yF.max(); uc=np.nonzero(mS.any(0))[0]; ucen=(uc.min()+uc.max())/2
zc=m.vertices[:,2]; off=(zc.max()+zc.min())/2
def spx(P): return np.c_[ucen-(P[:,2]-off)*k, (0.5-P[:,1]/(sF*H/W))*H+ty]
def dist(key):
    z=np.load(f"{K}/선화_{key}.npz"); return distance_transform_edt(~z["선"]), distance_transform_edt(~z["검은면"])
dF,kF=dist("정면"); dS,kS=dist("옆")
N=m.vertex_normals; w,depth,kdepth=12.0,1.5,3.0
def smooth(t): t=np.clip(t,0,1); return t*t*(3-2*t)
disp=np.zeros(len(m.vertices))
for which,(f,dmap,kmap) in {"앞":(fpx,dF,kF),"옆":(spx,dS,kS)}.items():
    p=f(m.vertices); facing=np.clip((N[:,2]-0.2)/0.4,0,1) if which=="앞" else np.clip((np.abs(N[:,0])-0.2)/0.4,0,1)
    dd=map_coordinates(dmap,[p[:,1]*3,p[:,0]*3],order=1,mode="nearest"); kk=map_coordinates(kmap,[p[:,1]*3,p[:,0]*3],order=1,mode="nearest")
    g=depth*smooth(1-dd/w)+(kdepth*smooth(1-kk/9.0) if which=="앞" else 0); disp=np.maximum(disp,g*facing); print(which,"홈 점",int((g*facing>0.05).sum()))
m.vertices=m.vertices-N*disp[:,None]; m.export("cut/tripo_groove.obj"); np.save("cut/hull_fit.npy",np.array([1.0,ty,ucen,off])); print("saved")
