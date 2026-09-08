# -*- coding: utf-8 -*-
"""복셀 구조가 납작한 게 **그림 탓인지** 잰다. 이 단계는 마스크를 안 본다 — 입력은 그림뿐이다.

    venv/Scripts/python.exe probe_coords.py in/pauldron_front.png in/pauldron_clean.png

깊이축 폭이 64칸 중 몇 칸인지 찍는다. op_front 는 7칸이었다(= 판때기).
"""
import os, sys, time
os.environ.setdefault("ATTN_BACKEND", "flash_attn")
os.environ.setdefault("SPCONV_ALGO", "native")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "shim")); sys.path.insert(0, os.path.join(HERE, "OmniPart"))
imgs = [os.path.abspath(os.path.join(HERE, p)) for p in sys.argv[1:]]
mask = os.path.abspath(os.path.join(HERE, "in/pauldron_front_mask.exr"))
os.chdir(os.path.join(HERE, "OmniPart"))
from modules.inference_utils import load_img_mask
from modules.part_synthesis.pipelines import OmniPartImageTo3DPipeline

pipe = OmniPartImageTo3DPipeline.from_pretrained("omnipart/OmniPart")
for k in ("slat_decoder_gs", "slat_decoder_rf", "slat_decoder_mesh", "slat_flow_model"):
    pipe.models.pop(k, None)
pipe.to("cuda")
SWEEP = [(25,12.0,1),(25,12.0,2),(25,12.0,3),(25,7.5,7),(25,10.0,7),(25,12.0,11),(25,12.0,23)]   # (스텝, cfg[, 시드])
for p in imgs:
    _, img_black, _, _ = load_img_mask(p, mask)
    for cfgs in SWEEP:
        st, cf = cfgs[0], cfgs[1]
        sd = cfgs[2] if len(cfgs) > 2 else 42
        t = time.time()
        c = pipe.get_coords(img_black, num_samples=1, seed=sd,
                            sparse_structure_sampler_params={"steps": st, "cfg_strength": cf}).cpu().numpy()
        w = c[:, 1:].max(0) - c[:, 1:].min(0)
        print("%-22s 스텝%3d cfg%5.1f 시드%2d  복셀 %5d  축폭 x%2d y%2d z%2d  (%.0fs)"
              % (os.path.basename(p), st, cf, sd, len(c), w[0], w[1], w[2], time.time()-t))
