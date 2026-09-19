# -*- coding: utf-8 -*-
"""TripoSG 마칭큐브 등위값 손잡이 — 로짓 장을 한 번 만들고 level 만 바꿔 뽑는다. 드릴. 관찰."""
import os, sys, time, json, gc
import numpy as np, torch, trimesh
from PIL import Image
TG=r"G:\art2real\트레일\trail4_gen3d"; sys.path+= [os.path.join(TG,"TripoSG"), os.path.join(TG,"TripoSG","scripts")]
from triposg.pipelines import pipeline_triposg as PT
from triposg.pipelines.pipeline_triposg import TripoSGPipeline
from triposg import inference_utils as IU
from image_process import prepare_image
from skimage import measure

CASE="mech_Drill_8uBbH7Dvmb"
INP="C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/258d243a-5ef8-43a0-8cc2-a201109e5c04/scratchpad/drill_in_rgba.png"  # cv2 가 한글 경로를 못 읽어 ASCII 로 복사
OUT=r"G:\art2real\원화3d\out\등위"; os.makedirs(OUT,exist_ok=True)
LEVELS=(-0.3,-0.15,0.0,0.15,0.3,0.6)

# ── 1. 가로채기: 마칭큐브 직전의 geometric_func 를 잡는다 ─────────────────
cap={}
def hijack(geometric_func, device, bounds=(-1.005,)*3+(1.005,)*3, dense_octree_depth=8, hierarchical_octree_depth=9):
    cap.update(f=geometric_func, dev=device, bounds=list(bounds), d0=dense_octree_depth, d1=hierarchical_octree_depth)
    return [(np.zeros((3,3),np.float32), np.array([[0,1,2]]))]   # 파이프라인이 .astype 을 부르므로 가짜 삼각형 하나
PT.hierarchical_extract_geometry=hijack

img=prepare_image(INP,bg_color=np.array([1.0,1.0,1.0]),rmbg_net=None)
print("입력 준비 ok",img.size,flush=True)
t0=time.time()
pipe=TripoSGPipeline.from_pretrained(os.path.join(TG,"weights","TripoSG")).to("cuda",torch.float16)
print("로드 %.0fs"%(time.time()-t0),flush=True)
with torch.no_grad():
    pipe(image=img,generator=torch.Generator(device="cuda").manual_seed(42),num_inference_steps=50,guidance_scale=7.0,
         use_flash_decoder=False,dense_octree_depth=8,hierarchical_octree_depth=9)
print("생성 끝 %.0fs · 가로챔 %s"%(time.time()-t0, bool(cap)),flush=True)

# ── 2. 로짓 장을 한 번 만든다 (inference_utils.hierarchical_extract_geometry 와 같은 절차) ──
with torch.no_grad():
    f,dev,bounds=cap["f"],cap["dev"],cap["bounds"]
    bmin=torch.tensor(bounds[:3]).to(dev); bmax=torch.tensor(bounds[3:]).to(dev); bsize=bmax-bmin
    xyz,grid_size,_=IU.generate_dense_grid_points_gpu(bbox_min=bmin,bbox_max=bmax,octree_depth=cap["d0"],indexing="ij")
    G=f(xyz.unsqueeze(0)).to(torch.float16).view(grid_size[0],grid_size[1],grid_size[2])
    for i in range(cap["d1"]-cap["d0"]):
        gs=2**(cap["d0"]+i+1); off=gs/2
        hi=IU.parallel_zoom(G,2)
        edge=IU.find_candidates_band(G,1.0)
        exp=IU.expand_edge_region_fast(edge,grid_size=int(gs/2)).to(torch.float16)
        norm=(exp-off)*(abs(bounds[0])/off)
        lg=f(norm.unsqueeze(0)).to(torch.float16)
        idx=((norm*(off/abs(bounds[0])))+off).type(torch.IntTensor)
        hi[idx[:,0],idx[:,1],idx[:,2]]=lg[0][:,0]
        G=hi; torch.cuda.empty_cache()
    grid=G.float().cpu().numpy()
print("장 %s · 로짓 분포 %.2f ~ %.2f · 중앙 %.2f"%(grid.shape,grid.min(),grid.max(),np.median(grid)),flush=True)
np.save(os.path.join(OUT,CASE+"_logits.npy"),grid.astype(np.float16))
del pipe; gc.collect(); torch.cuda.empty_cache()

# ── 3. 등위값마다 마칭큐브 ────────────────────────────────────────────────
rows=[]
for L in LEVELS:
    V,F,_,_=measure.marching_cubes(grid,L,method="lewiner")
    V=V/(2**cap["d1"])*bsize.cpu().numpy()+bmin.cpu().numpy()
    m=trimesh.Trimesh(V.astype(np.float32),np.ascontiguousarray(F))
    p=os.path.join(OUT,"%s_L%+.2f.glb"%(CASE,L)); m.export(p)
    rows.append(dict(level=L,faces=int(len(m.faces)),volume=float(abs(m.volume)),path=p))
    print("  level %+.2f  면 %8d  부피 %.5f"%(L,len(m.faces),abs(m.volume)),flush=True)
ref=trimesh.load(r"G:\art2real\원화3d\out\생성3D\triposg\%s.glb"%CASE,force="mesh")
print("배관 — 캐시된 글b: 면 %d 부피 %.5f  (level 0 이 이것과 같아야 씨앗·레시피가 맞다)"%(len(ref.faces),abs(ref.volume)),flush=True)
json.dump(dict(case=CASE,levels=rows,cached=dict(faces=int(len(ref.faces)),volume=float(abs(ref.volume)))),
          open(os.path.join(OUT,CASE+"_levels.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("saved",flush=True)
