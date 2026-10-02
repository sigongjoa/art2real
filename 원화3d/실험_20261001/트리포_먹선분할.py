# -*- coding: utf-8 -*-
"""3D 먹선(꺾인 모서리)으로 TripoSG 머리를 분할 (10-02 사용자 「이 정보를 바탕으로 분할해야지」).
원화 선파츠와 같은 생각을 표면에서: 꺾인 각 ≥ 문턱인 변의 양쪽 면 = 벽 → 벽을 k 고리 두껍게(끊긴 선 잇기) → 벽 아닌 면의 연결 성분 = 부품
→ 벽 면은 이웃 부품으로 번져 돌려줌 → 작은 부품(머리 면적 0.4 % 미만)은 가장 길게 맞닿은 이웃에.
메시: h_remesh.obj(복셀 0.5 · 22만 면) — ink3d.py 가 선을 뽑은 그 메시."""
import os, numpy as np, trimesh, scipy.sparse as sp, json
from scipy.sparse.csgraph import connected_components
S=r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\7cb277a7-139e-42d2-8434-a71e5084b8ad\scratchpad"; O=r"G:\art2real\원화3d\out\오메가몬2\지표\트리포먹선분할"; os.makedirs(O,exist_ok=True)
c=trimesh.load(os.path.join(S,"cut","h_remesh.obj"),process=True); adj=c.face_adjacency; ang=np.degrees(c.face_adjacency_angles); nF=len(c.faces); area=c.area_faces; tot=area.sum()
FA=sp.coo_matrix((np.ones(len(adj)),(adj[:,0],adj[:,1])),shape=(nF,nF)).tocsr(); FA=FA+FA.T
def 나누기(문턱,k):
    wall=np.zeros(nF,bool); e=ang>=문턱; wall[adj[e,0]]=True; wall[adj[e,1]]=True
    for _ in range(k): wall=wall|(FA@wall.astype(float)>0)
    keep=~wall[adj[:,0]]&~wall[adj[:,1]]; G=sp.coo_matrix((np.ones(keep.sum()),(adj[keep,0],adj[keep,1])),shape=(nF,nF)); _,lab=connected_components(G,directed=False); lab=lab.astype(np.int64); lab[wall]=-1
    for _ in range(400):
        if not (lab<0).any(): break
        la,lb=lab[adj[:,0]],lab[adj[:,1]]; s1=(la<0)&(lb>=0); lab[adj[s1,0]]=lb[s1]; s2=(lb<0)&(la>=0); lab[adj[s2,1]]=la[s2]
    lab[lab<0]=0; _,lab=np.unique(lab,return_inverse=True)
    for _ in range(10):
        pa=np.bincount(lab,weights=area); small=pa<0.004*tot
        if not small[lab].any(): break
        a,b=lab[adj[:,0]],lab[adj[:,1]]; cr=a!=b; w=sp.coo_matrix((np.ones(cr.sum()),(a[cr],b[cr])),shape=(lab.max()+1,)*2).tocsr(); w=w+w.T; tgt=np.arange(lab.max()+1)
        for s_ in np.nonzero(small)[0]:
            row=w.getrow(s_)
            if row.nnz: tgt[s_]=row.indices[np.argmax(row.data)]
        for _ in range(6): tgt=tgt[tgt]
        _,lab=np.unique(tgt[lab],return_inverse=True)
    return lab, wall
결과={}
for 문턱 in (20,26,35):
    for k in (1,2,3):
        lab,wall=나누기(문턱,k); pa=np.bincount(lab,weights=area)/tot*100; 결과[f"{문턱}_{k}"]={"부품":int(lab.max()+1),"벽%":round(float(area[wall].sum()/tot*100),1),"큰순%":[round(float(x),1) for x in sorted(pa,reverse=True)[:6]]}
        print(문턱,k,결과[f"{문턱}_{k}"])
json.dump(결과,open(os.path.join(O,"훑기.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
