# -*- coding: utf-8 -*-
"""TripoSG 가 「점마다 안/밖」을 정해 가는 과정을 단계별로 꺼낸다 (쇼츠 원리 장면용).

    D:\imggen\venv\Scripts\python.exe 단계보기.py out/knights/omega_front_clean_prep.png out/steps

50 단계 중 STEPS 에서 잠재(latents)를 복사해 두고, 끝난 뒤 단계마다
  slice_front_XX.npy : 정면 평면(z=0) 256² 점의 안/밖 값(양수 = 안)
  slice_side_XX.npy  : 옆 평면(x=0) 256² — 그림에 없는 깊이를 어떻게 지어내나
  mesh_XX.glb        : 거친 메시(옥트리 7/8 — 모양만 보려고)
를 낸다. 잠재는 그 단계의 x_t(잡음이 섞인 현재 상태) 그대로 — 예측 x0 이 아니다.
"""
import os, sys, time
import numpy as np, torch, trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path += [os.path.join(HERE, "TripoSG"), os.path.join(HERE, "TripoSG", "scripts")]
from triposg.pipelines.pipeline_triposg import TripoSGPipeline
from triposg.inference_utils import hierarchical_extract_geometry

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
STEPS = [0, 1, 3, 6, 10, 15, 25, 35, 49]
N, B = 256, 1.0

t0 = time.time()
pipe = TripoSGPipeline.from_pretrained(os.path.join(HERE, "weights", "TripoSG")).to("cuda", torch.float16)
print(f"로드 {time.time()-t0:.0f}s", flush=True)

saved = {}
def grab(p, i, t, kw):
    if i in STEPS: saved[i] = kw["latents"].detach().clone()
    return kw

img = Image.open(src).convert("RGB")
with torch.no_grad():
    pipe(image=img, generator=torch.Generator(device="cuda").manual_seed(42), num_inference_steps=50,
         guidance_scale=7.0, use_flash_decoder=False, dense_octree_depth=6, hierarchical_octree_depth=6,
         callback_on_step_end=grab)
print("단계", sorted(saved), flush=True)

u = torch.linspace(-B, B, N, device="cuda")
gy, gx = torch.meshgrid(-u, u, indexing="ij")            # 행 = 위→아래(y 큰 쪽이 위)
zero = torch.zeros_like(gx)
planes = {"front": torch.stack([gx, gy, zero], -1), "side": torch.stack([zero, gy, gx], -1)}  # side 의 가로 = z(깊이)
with torch.no_grad():
    for i, lat in sorted(saved.items()):
        for name, P in planes.items():
            v = pipe.vae.decode(lat, sampled_points=P.reshape(1, -1, 3).to(lat.dtype)).sample
            np.save(os.path.join(out, f"slice_{name}_{i:02d}.npy"), v.float().reshape(N, N).cpu().numpy())
        try:
            g = lambda x, lat=lat: pipe.vae.decode(lat, sampled_points=x).sample
            o = hierarchical_extract_geometry(g, "cuda", bounds=(-1.005, -1.005, -1.005, 1.005, 1.005, 1.005),
                                              dense_octree_depth=7, hierarchical_octree_depth=8)
            trimesh.Trimesh(o[0][0].astype(np.float32), np.ascontiguousarray(o[0][1])).export(os.path.join(out, f"mesh_{i:02d}.glb"))
        except Exception as e:                      # 아주 이른 단계는 면이 안 생길 수 있다
            print(f"메시 실패 {i}: {type(e).__name__} {e}", flush=True)
        print(f"단계 {i} 끝 {time.time()-t0:.0f}s", flush=True)
