# -*- coding: utf-8 -*-
"""TripoSG(MIT) 로컬 실행. RTX 3050 8GB.

    D:\imggen\venv\Scripts\python.exe run_triposg.py in/turn_front.png out/turn_front.glb

`diso` 는 CUDA 컴파일이 필요해 못 깔았다(nvcc 없음). 그래서 flash 디코더 대신
`hierarchical_extract_geometry`(skimage marching_cubes) 경로를 강제한다 —
`use_flash_decoder=False`. 파이프라인 기본값이 어느 쪽인지 믿지 말고 명시한다.
"""
import argparse, os, sys, time

import torch
import trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path += [os.path.join(HERE, "TripoSG"), os.path.join(HERE, "TripoSG", "scripts")]
from triposg.pipelines.pipeline_triposg import TripoSGPipeline
from image_process import prepare_image
from briarmbg import BriaRMBG

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    # **여러 장을 한 프로세스에서 돌린다.** 모델 로드가 387초라 인물마다 새로 띄우면
    # 그것만으로 26명에 2시간 45분이다. 로드는 한 번, 생성은 장당 100초 안팎이다
    ap.add_argument("image", nargs="+", help="입력 이미지들 (--outdir 과 함께 쓴다)")
    ap.add_argument("out", nargs="?", help="한 장일 때의 출력 경로")
    ap.add_argument("--outdir", help="여러 장일 때 여기에 <입력이름>.glb 로 낸다")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=7.0)
    ap.add_argument("--octree", type=int, default=8, help="dense octree depth")
    ap.add_argument("--hier", type=int, default=9, help="hierarchical octree depth")
    ap.add_argument("--no-rmbg", action="store_true", help="배경제거 건너뜀(이미 흰 배경)")
    a = ap.parse_args()

    dev, dt = "cuda", torch.float16
    t0 = time.time()
    rmbg = None if a.no_rmbg else BriaRMBG.from_pretrained(
        os.path.join(HERE, "weights", "RMBG-1.4")).to(dev).eval()
    pipe = TripoSGPipeline.from_pretrained(
        os.path.join(HERE, "weights", "TripoSG")).to(dev, dt)
    print(f"로드 {time.time()-t0:.0f}s  VRAM {torch.cuda.memory_allocated()/2**30:.2f}GB")

    jobs = []
    for im in a.image:
        if a.outdir:
            os.makedirs(a.outdir, exist_ok=True)
            o = os.path.join(a.outdir, os.path.splitext(os.path.basename(im))[0] + ".glb")
        else:
            o = a.out
        jobs.append((im, o))

    for im, o in jobs:
        try:
            img = prepare_image(im, bg_color=np.array([1.0, 1.0, 1.0]), rmbg_net=rmbg)
            img.save(o.replace(".glb", "_prep.png"))
            t = time.time()
            with torch.no_grad():
                out = pipe(image=img,
                           generator=torch.Generator(device=pipe.device).manual_seed(a.seed),
                           num_inference_steps=a.steps, guidance_scale=a.cfg,
                           use_flash_decoder=False,
                           dense_octree_depth=a.octree,
                           hierarchical_octree_depth=a.hier).samples[0]
            m = trimesh.Trimesh(out[0].astype(np.float32), np.ascontiguousarray(out[1]))
            m.export(o)
            print(f"생성 {time.time()-t:.0f}s  정점 {len(m.vertices):,} 면 {len(m.faces):,}"
                  f"  피크VRAM {torch.cuda.max_memory_allocated()/2**30:.2f}GB  -> {o}",
                  flush=True)
        except Exception as e:                    # 한 명이 죽어도 나머지는 뽑는다
            print(f"실패 {im}: {type(e).__name__} {e}", flush=True)


if __name__ == "__main__":
    main()
