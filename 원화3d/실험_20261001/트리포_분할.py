# -*- coding: utf-8 -*-
"""머리 전용 TripoSG 를 부품별로 분할 (10-02 사용자 「tripoSG 에서 각 부분별로 분할 먼저」 · 깎기 테스트 앞 단계).
  1) 특징: G:\art2real\트레일\trail7_part3d\venv\Scripts\python.exe 트리포_분할.py 특징
           h_units.obj(머리 단위 · 자세 맞춘 머리 전용 TripoSG) → 줄임(12만 면) → PartField 면 특징 448 차
  2) 가르기: python 트리포_분할.py [n…] → 면 인접 계층 군집(ward) · n = 6 · 12 · 20 부품 → 라벨 npz + 렌더용 obj"""
import os, sys, numpy as np
S=r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\7cb277a7-139e-42d2-8434-a71e5084b8ad\scratchpad"
O=r"G:\art2real\원화3d\out\오메가몬2\지표\트리포분할"; os.makedirs(O,exist_ok=True)
PF=r"G:\art2real\트레일\trail9_partfield"
IN=os.environ.get("IN",""); TAG=os.environ.get("TAG","")   # 10-05: 입력 ply · 출력 이름 앞붙이
def 특징():
    import types, torch, trimesh
    sys.path[:0]=[os.path.join(PF,"shim"),os.path.join(PF,"PartField")]
    for m in ("boto3","mesh2sdf","tetgen","vtk","pymeshlab"): sys.modules[m]=types.ModuleType(m)
    L=types.ModuleType("lightning"); Lp=types.ModuleType("lightning.pytorch")
    Lp.LightningModule=type("LightningModule",(torch.nn.Module,),{"save_hyperparameters":lambda self,*a,**k:None}); L.pytorch=Lp; sys.modules["lightning"]=L; sys.modules["lightning.pytorch"]=Lp
    from partfield.config import setup
    from partfield.model_trainer_pvcnn_only_demo import Model
    from partfield.model.PVCNN.encoder_pc import sample_triplane_feat
    cfg=setup(types.SimpleNamespace(config_file=os.path.join(PF,"PartField","configs","final","demo.yaml"),opts=[]),freeze=False); net=Model(cfg)
    sd=torch.load(os.path.join(PF,"model","model_objaverse.ckpt"),map_location="cpu",weights_only=False)["state_dict"]; print("가중치",net.load_state_dict(sd,strict=False)); net=net.cuda().eval()
    if IN:   # 10-05: 우리 틀(z 위 · 앞 −y) ply 를 그대로 — PartField 는 y 위 · z 앞
        m=trimesh.load(IN,process=True); V=np.asarray(m.vertices,np.float64); V=np.c_[V[:,0],V[:,2],-V[:,1]]
    else:
        m=trimesh.load(os.path.join(S,"cut","h_units.obj"),process=True)
        try: m=m.simplify_quadric_decimation(face_count=120000)
        except Exception as e: print("줄임 실패",e)
        m.export(os.path.join(O,"머리_줄임.obj")); V=np.asarray(m.vertices,np.float64); V=np.c_[V[:,0],-V[:,1],V[:,2]]          # (x, y아래, z앞) → y 위
    print("면",len(m.faces))
    c=(V.min(0)+V.max(0))/2; V=(V-c)*(2*0.9/(V.max(0)-V.min(0)).max())
    torch.manual_seed(0); np.random.seed(0); m2=trimesh.Trimesh(V,m.faces,process=False)
    pc,_=trimesh.sample.sample_surface(m2,100000,seed=0); pc=torch.tensor(pc,dtype=torch.float32,device="cuda")[None]
    with torch.no_grad():
        part=net.triplane_transformer(net.pvcnn(pc,pc))[:,:,64:]; k=32; Vt=torch.tensor(V,dtype=torch.float32,device="cuda"); Ft=torch.tensor(m.faces,device="cuda"); out=[]
        for s in range(0,len(Ft),4000):
            f=Ft[s:s+4000]; u=torch.rand(len(f),k,1,device="cuda").sqrt(); v=torch.rand(len(f),k,1,device="cuda")
            p=(1-u)*Vt[f[:,0]][:,None]+u*(1-v)*Vt[f[:,1]][:,None]+u*v*Vt[f[:,2]][:,None]
            out.append(sample_triplane_feat(part,p.reshape(1,-1,3)).reshape(len(f),k,-1).mean(1).float().cpu())
    F=torch.cat(out).numpy(); np.save(os.path.join(O,TAG+"면특징.npy"),F.astype(np.float32)); print("면 특징",F.shape)
def 가르기(ns):
    """147만 면 → (특징 + 위치) MiniBatchKMeans 400 조각 → 조각 인접 그래프 위 ward 군집 n 부품."""
    import trimesh, scipy.sparse as sp, json
    from sklearn.cluster import AgglomerativeClustering, MiniBatchKMeans
    m=trimesh.load(os.path.join(S,"cut","h_units.obj"),process=True); F=np.load(os.path.join(O,"면특징.npy")); F=F/np.linalg.norm(F,axis=1,keepdims=True)
    assert len(F)==len(m.faces), (len(F),len(m.faces))
    P=m.triangles_center; Pn=(P-P.mean(0))/P.std()
    X=np.c_[F, 0.15*Pn]                                    # 위치는 조각을 이어 붙게만 약하게
    km=MiniBatchKMeans(n_clusters=400,random_state=0,batch_size=20000,n_init=3).fit(X); sp_lab=km.labels_
    adj=m.face_adjacency; a_,b_=sp_lab[adj[:,0]],sp_lab[adj[:,1]]; k=a_!=b_
    A=sp.coo_matrix((np.ones(k.sum()),(a_[k],b_[k])),shape=(400,400)).tocsr(); A=((A+A.T)>0).astype(float)
    C=np.vstack([F[sp_lab==i].mean(0) if (sp_lab==i).any() else np.zeros(F.shape[1]) for i in range(400)])
    res={}
    for n in ns:
        L=AgglomerativeClustering(n_clusters=n,linkage="ward",connectivity=A).fit_predict(C); lab=L[sp_lab]
        np.save(os.path.join(O,f"라벨_{n}.npy"),lab.astype(np.int16)); sizes=np.bincount(lab); res[n]=sizes.tolist(); print(n,"부품 · 큰 순 면 수",sorted(sizes.tolist(),reverse=True)[:6])
    json.dump(res,open(os.path.join(O,"가르기.json"),"w"))
if __name__=="__main__":
    if sys.argv[1:2]==["특징"]: 특징()
    else: 가르기([int(x) for x in sys.argv[1:]] or [6,12,20])
