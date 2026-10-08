# -*- coding: utf-8 -*-
"""조각0 — 합성 그림 → cadrille 비전 인코더(얼림) 토큰 열 · 한 번만 뽑아 저장 (N, 토큰, 1536) fp16
python runs/조각0/특징.py  →  runs/조각0/특징.npy"""
import os, sys, glob, numpy as np, torch
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(os.path.dirname(H)); sys.path[:0] = [T, os.path.join(T, "s0", "stub")]
W = os.path.join(T, "weights")
from transformers import AutoConfig, AutoProcessor
from transformers.models.qwen2_vl.modeling_qwen2_vl import Qwen2VisionTransformerPretrainedModel
from safetensors import safe_open
from cadrille import collate
cfg = AutoConfig.from_pretrained(os.path.join(W, "cadrille")).vision_config; cfg._attn_implementation = "sdpa"
m = Qwen2VisionTransformerPretrainedModel(cfg)
with safe_open(os.path.join(W, "cadrille", "model.safetensors"), "pt") as f: m.load_state_dict({k[7:]: f.get_tensor(k) for k in f.keys() if k.startswith("visual.")}, strict=True)
m = m.to("cuda", torch.bfloat16).eval()
proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
fs = sorted(glob.glob(os.path.join(H, "합성", "*.png")))[:int(sys.argv[1]) if len(sys.argv) > 1 else None]; out = []
with torch.no_grad():
    for i, p in enumerate(fs):
        x = collate([{"video": [Image.open(p).convert("RGB")], "description": "Generate cadquery code", "file_name": ""}], processor=proc, n_points=256, eval=True)
        out.append(m(x["pixel_values_videos"].to("cuda", torch.bfloat16), grid_thw=x["video_grid_thw"].to("cuda")).half().cpu().numpy())
        if i == 0: print("토큰", out[0].shape, flush=True)
np.save(os.path.join(H, "특징.npy"), np.stack(out)); print("ok", len(out))
