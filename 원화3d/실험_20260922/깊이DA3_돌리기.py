# -*- coding: utf-8 -*-
"""깊이 DA3 2 단계 — D:\ComfyUI 의 venv 로 돌린다(ComfyUI 내장 노드 코드를 그대로 부른다).
    D:\ComfyUI\venv\Scripts\python.exe 깊이DA3_돌리기.py   -> out/깊이DA3/<케이스>/<판>_da3.npy (창 해상도 · 모델 raw depth)"""
import os, sys, glob
sys.path.insert(0, r"D:\ComfyUI")
os.chdir(r"D:\ComfyUI")
import numpy as np, torch
from PIL import Image
import folder_paths, comfy.sd
from comfy_extras.nodes_depth_anything_3 import _run_da3

D = r"G:\art2real\원화3d\out\깊이DA3"
RES = int(os.environ.get("DA3_RES", "1008"))
m = comfy.sd.load_diffusion_model(folder_paths.get_full_path_or_raise("geometry_estimation", "depth_anything_3_mono_large.safetensors"))
for f in sorted(glob.glob(os.path.join(D, "*", "*.png"))):
    if os.path.basename(f).startswith("_"): continue
    im = torch.from_numpy(np.asarray(Image.open(f).convert("RGB"), np.float32) / 255)[None]
    depth, conf, sky = _run_da3(m, im, RES)
    np.save(f[:-4] + "_da3.npy", depth[0].numpy().astype(np.float32))
    print(os.path.relpath(f, D), tuple(depth.shape), float(depth.min()), float(depth.max()), flush=True)
