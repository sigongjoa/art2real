# -*- coding: utf-8 -*-
"""머리 전용 TripoSG 를 곡률 · 법선으로 분할 (10-02 사용자 「곡률이랑 법선을 바탕으로 분할하면?」).
1차(이웃 면 꺾인 각)는 한 덩어리 — 촘촘한 메시는 골짜기에서도 이웃끼리 몇 도만 꺾인다. 그래서 「넓게 잰」 값으로:
 A 골 자르기: 꼭짓점마다 반지름 r 공 안의 평균 곡률(오목 = 음수) → 오목이 문턱보다 깊은 면을 벽으로 → 벽 아닌 면의 연결 성분 = 부품 → 벽 면은 가까운 부품에.
 B 법선 묶기: 면 법선(반지름 r 로 평균) + 곡률로 600 조각(KMeans) → 맞닿은 조각끼리만 ward, 거리 문턱으로 멈춤(부품 수는 안 정함).
속도: 복셀 0.6 로 다시 짠 메시(약 20만 면)에서 재고, 라벨은 원본 면에 가까운 면으로 옮긴다."""
import os, numpy as np, trimesh, scipy.sparse as sp, json
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
S=r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\7cb277a7-139e-42d2-8434-a71e5084b8ad\scratchpad"; O=r"G:\art2real\원화3d\out\오메가몬2\지표\트리포곡률"; os.makedirs(O,exist_ok=True)
m=trimesh.load(os.path.join(S,"cut","h_units.obj"),process=True)
from skimage import measure
vg=m.voxelized(0.6).fill(); M=vg.matrix.astype(np.float32); v,f,_,_=measure.marching_cubes(np.pad(M,1),0.5); v=(v-1)*0.6; v=trimesh.transform_points(v,vg.transform) if False else v*1.0
c=trimesh.Trimesh(v,f,process=True); c.apply_translation(m.bounds[0]-c.bounds[0]); trimesh.smoothing.filter_taubin(c,iterations=15); print("다시 짠 면",len(c.faces))
r=1.6
H=trimesh.curvature.discrete_mean_curvature_measure(c,c.vertices,r)/(np.pi*r*r)          # 꼭짓점 평균 곡률(볼록 +)
Hf=H[c.faces].mean(1)
# 법선 넓게: 꼭짓점 법선을 이웃 평균 3 번
vn=c.vertex_normals.copy(); Ad=c.vertex_adjacency_graph
import networkx as nx
Ls=sp.csr_matrix(nx.to_scipy_sparse_array(Ad,nodelist=range(len(c.vertices)))); Ls=sp.diags(1/np.maximum(Ls.sum(1).A1,1))@Ls
for _ in range(6): vn=Ls@vn; vn/=np.linalg.norm(vn,axis=1,keepdims=True)+1e-9
Nf=vn[c.faces].mean(1); Nf/=np.linalg.norm(Nf,axis=1,keepdims=True)+1e-9
adj=c.face_adjacency; nF=len(c.faces); area=c.area_faces; tot=area.sum()
tree=cKDTree(c.triangles_center); _,near=tree.query(m.triangles_center)
결과={}
def 저장(이름,lab):
    _,lab=np.unique(lab,return_inverse=True); L=lab[near]; np.save(os.path.join(O,f"라벨_{이름}.npy"),L.astype(np.int32))
    pa=np.bincount(lab,weights=area); 결과[이름]={"부품":int(lab.max()+1),"큰 순 면적%":[round(float(x),1) for x in sorted(pa/tot*100,reverse=True)[:8]]}; print(이름,결과[이름])
    d=os.path.join(O,이름); os.makedirs(d,exist_ok=True); [os.remove(os.path.join(d,q)) for q in os.listdir(d)]
    for i in range(L.max()+1):
        idx=np.nonzero(L==i)[0]
        if len(idx): m.submesh([idx],append=True).export(os.path.join(d,f"p{i}.obj"))
def 작은것합치기(lab,최소=0.004):
    el=np.ones(len(adj))
    for _ in range(10):
        pa=np.bincount(lab,weights=area,minlength=lab.max()+1); small=(pa<최소*tot)&(pa>0)
        if not small[lab].any(): break
        a,b=lab[adj[:,0]],lab[adj[:,1]]; cr=a!=b; w=sp.coo_matrix((el[cr],(a[cr],b[cr])),shape=(lab.max()+1,)*2).tocsr(); w=w+w.T; tgt=np.arange(lab.max()+1)
        for s_ in np.nonzero(small)[0]:
            row=w.getrow(s_)
            if row.nnz: tgt[s_]=row.indices[np.argmax(row.data)]
        for _ in range(6): tgt=tgt[tgt]
        lab=tgt[lab]
    return lab
# A 골 자르기 — 문턱 = 오목 곡률 백분위
for 이름,q in (("A골_깊은골",3),("A골_보통",7),("A골_얕은골",12)):
    t=np.percentile(Hf,q); wall=Hf<t; keep=~wall[adj[:,0]]&~wall[adj[:,1]]
    G=sp.coo_matrix((np.ones(keep.sum()),(adj[keep,0],adj[keep,1])),shape=(nF,nF)); _,lab=connected_components(G,directed=False)
    lab[wall]=-1
    # 벽 면 → 가까운 비벽 성분으로 번지기
    for _ in range(200):
        if (lab<0).sum()==0: break
        a,b=adj[:,0],adj[:,1]; la,lb=lab[a],lab[b]; s1=(la<0)&(lb>=0); lab[a[s1]]=lb[s1]; s2=(lb<0)&(la>=0); lab[b[s2]]=la[s2]
    lab[lab<0]=0; 저장(이름,작은것합치기(lab))
# B 법선 묶기
from sklearn.cluster import MiniBatchKMeans, AgglomerativeClustering
P=c.triangles_center; X=np.c_[Nf*1.0,np.clip(Hf/np.std(Hf),-3,3)*0.25,(P-P.mean(0))/P.std()*0.25]
spl=MiniBatchKMeans(600,random_state=0,batch_size=20000,n_init=3).fit_predict(X)
a,b=spl[adj[:,0]],spl[adj[:,1]]; k=a!=b; A=sp.coo_matrix((np.ones(k.sum()),(a[k],b[k])),shape=(600,600)).tocsr(); A=((A+A.T)>0).astype(float)
C=np.vstack([np.r_[Nf[spl==i].mean(0),Hf[spl==i].mean()/np.std(Hf)*0.25] for i in range(600)])
for 이름,th in (("B법선_굵게",4.0),("B법선_보통",2.5),("B법선_잘게",1.5)):
    L=AgglomerativeClustering(n_clusters=None,distance_threshold=th,linkage="ward",connectivity=A).fit_predict(C); 저장(이름,작은것합치기(L[spl]))
json.dump(결과,open(os.path.join(O,"곡률분할.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
