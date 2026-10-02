# -*- coding: utf-8 -*-
"""겹깊이시험 DA3 단계 — 깊이DA3_돌리기.py(09-22) 를 겹깊이 폴더로 돌린다.
    D:\ComfyUI\venv\Scripts\python.exe 깊이DA3_돌리기.py   -> out/깊이DA3/<케이스>/<판>_da3.npy (창 해상도 · 모델 raw depth)"""
import os, sys, glob
sys.path.insert(0, r"D:\ComfyUI")
os.chdir(r"D:\ComfyUI")
import numpy as np, torch
from PIL import Image
import folder_paths, comfy.sd
from comfy_extras.nodes_depth_anything_3 import _run_da3

D = r"G:\art2real\원화3d\out\오메가몬2\지표\겹깊이"
RES = int(os.environ.get("DA3_RES", "1008"))
m = comfy.sd.load_diffusion_model(folder_paths.get_full_path_or_raise("geometry_estimation", "depth_anything_3_mono_large.safetensors"))
for f in sorted(glob.glob(os.path.join(D, "*_평면.png")) + glob.glob(os.path.join(D, "*_음영.png"))):
    if os.path.basename(f).startswith("_"): continue
    im = torch.from_numpy(np.asarray(Image.open(f).convert("RGB"), np.float32) / 255)[None]
    depth, conf, sky = _run_da3(m, im, RES)
    np.save(f[:-4] + "_da3.npy", depth[0].numpy().astype(np.float32))
    print(os.path.relpath(f, D), tuple(depth.shape), float(depth.min()), float(depth.max()), flush=True)
