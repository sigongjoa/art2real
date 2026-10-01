# 09-21 매끈먹선 과정을 지금 머리 캡처(02 정면 · 옆)에: 두 실루엣 교집합 hull → 잘게 → 먹선(09-29 선화.py · 3배) 거리장 V 골 · 검은면은 깊게
import numpy as np, cv2, json, trimesh
from skimage import measure
from scipy.ndimage import distance_transform_edt, map_coordinates
K=r"G:\art2real\원화3d\out\오메가몬2\지표"; cams=json.load(open("cut/cams.json"))
def P(c):  # world→px
    M=np.array(c["M"]); Mi=np.linalg.inv(M); W,H,s=c["W"],c["H"],c["ortho"]
    def f(V): vc=(Mi[:3,:3]@V.T).T+Mi[:3,3]; return np.c_[(vc[:,0]/s+0.5)*W,(0.5-vc[:,1]/(s*H/W))*H]
    return f,M,W,H,s
fF,MF,W,H,sF=P(cams["카메라_02_정면"]); fS,MS,_,_,sS=P(cams["카메라_02_옆"])
def mask(key):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[np.load(f"{K}/윤곽3_{key}_전체.npy").astype(np.int32)],1); return m.astype(bool)
mF,mS=mask("정면"),mask("옆")
# 옆 뿔은 화면 밖에서 잘림 → 윗 행을 위로 복제(기둥) · 정면 턱~뿔끝 높이에 옆 높이를 맞춤(배율 s · 이동)
yF=np.nonzero(mF.any(1))[0]; yS=np.nonzero(mS.any(1))[0]; topS=yS.min(); mS2=mS.copy(); mS2[:topS]=mS[topS]
# 옆 턱 = 옆 마스크 맨 아래 · 정면 턱 = 정면 맨 아래 ; 옆 뿔 끝은 잘렸으니 눈 높이로 못 맞추고 턱만 맞춤 + 배율은 둘의 얼굴 폭/깊이 비 대신 1.0(캡처 두 장이 비슷한 줌)
s_side=1.0; ty=yS.max()-yF.max()*s_side   # 턱 행을 맞춘다(정면 행 → 옆 행)
# 격자: 정면 카메라 좌표(이미지 평면 x y · 깊이 z) 로 짓고 세계로 보낸다
unit=0.6; xs=np.nonzero(mF.any(0))[0]; 
def px2cam(u,v): return (u/W-0.5)*sF, (0.5-v/H)*sF*H/W
x0,y1=px2cam(xs.min()-6,yF.min()-6); x1,y0=px2cam(xs.max()+6,yF.max()+6)
gx=np.arange(x0,x1,unit); gy=np.arange(y0,y1,unit); gz=np.arange(-130,60,unit)        # 깊이 범위(정면 카메라 z · 카메라 쪽 +)
X,Y,Z=np.meshgrid(gx,gy,gz,indexing="ij"); Vc=np.c_[X.ravel(),Y.ravel(),Z.ravel()]; Vw=(MF[:3,:3]@Vc.T).T+MF[:3,3]
pF=fF(Vw); inF=mF[np.clip(pF[:,1].round().astype(int),0,H-1),np.clip(pF[:,0].round().astype(int),0,W-1)]
k=W/sF; uc=np.nonzero(mS2.any(0))[0]; ucen=(uc.min()+uc.max())/2      # 옆 뷰 = 정면 카메라 좌표의 수식: 가로 u = 깊이 z(얼굴이 왼쪽 → z 클수록 u 작음) · 세로 v = 정면과 같은 높이
def side_px(Vc_): return np.c_[ucen - Vc_[:,2]*k*s_side + 0.0, (0.5 - Vc_[:,1]/(sF*H/W))*H*s_side + ty]
pS=side_px(Vc); u=pS[:,0]; v=pS[:,1]
inS=mS2[np.clip(v.round().astype(int),0,H-1),np.clip(u.round().astype(int),0,W-1)]
vol=(inF&inS).reshape(X.shape); print("hull 복셀",vol.sum(),vol.shape)
verts,faces,_,_=measure.marching_cubes(vol.astype(np.float32),0.5,spacing=(unit,unit,unit)); verts+=np.array([x0,y0,-130])
m=trimesh.Trimesh(verts,faces,process=True); m=max(m.split(only_watertight=False),key=lambda t:len(t.faces)); trimesh.smoothing.filter_laplacian(m,lamb=0.5,iterations=30)
m=trimesh.Trimesh(*trimesh.remesh.subdivide_to_size(m.vertices,m.faces,max_edge=0.45)); print("점",len(m.vertices),"면",len(m.faces))
# ── 먹선 거리장(3배 해상도) ──
def dist(key,top_rep=None):
    z=np.load(f"{K}/선화_{key}.npz"); 선=z["선"]; 검=z["검은면"]
    if top_rep is not None: 선[:top_rep*3]=False
    return distance_transform_edt(~선), distance_transform_edt(~검)
dF,kF=dist("정면"); dS,kS=dist("옆")
Vw2=(MF[:3,:3]@m.vertices.T).T+MF[:3,3]; N=m.vertex_normals; Nw=(MF[:3,:3]@N.T).T
w,depth,kdepth=9.0,1.2,3.0   # 반폭(3배 px) · 홈 깊이 · 검은면 깊이(단위)
def smooth(t): t=np.clip(t,0,1); return t*t*(3-2*t)
disp=np.zeros(len(m.vertices))
for f,dmap,kmap,camM,fit in ((fF,dF,kF,MF,None),(None,dS,kS,None,"side")):
    p=f(Vw2) if f is not None else side_px(m.vertices)
    cd=np.array([0,0,1.0]) if f is not None else np.array([0,0,-1.0]); facing=np.clip((N@cd-0.2)/0.4,0,1)   # 정면 카메라 좌표 법선: 정면은 +z · 옆은 -x? 옆 카메라는 얼굴 왼쪽 = +z 쪽에서 보지 않고 옆(x)에서 본다
    if f is None: facing=np.clip((np.abs(N[:,0])-0.2)/0.4,0,1)
    d=map_coordinates(dmap,[p[:,1]*3,p[:,0]*3],order=1,mode="nearest"); k=map_coordinates(kmap,[p[:,1]*3,p[:,0]*3],order=1,mode="nearest")
    g=depth*smooth(1-d/w)+(kdepth*smooth(1-k/9.0) if f is not None else 0); disp=np.maximum(disp,g*facing)   # 검은면은 정면만(옆 눈은 얼룩)
m.vertices=m.vertices-N*disp[:,None]; print("홈 점",int((disp>0.05).sum()))
m.export("cut/hull_groove.obj"); np.save("cut/hull_fit.npy",np.array([s_side,ty,ucen])); print("saved")
