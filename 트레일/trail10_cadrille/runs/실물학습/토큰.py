# -*- coding: utf-8 -*-
"""그림 폴더 → 얼린 cadrille 비전 인코더 토큰 (N, 100, 1536) fp16 · python 토큰.py <그림 폴더> <출력.npy> [이름 목록 json(키 순서)]"""
import os, sys, glob, json, numpy as np, torch
from PIL import Image
T0 = "G:/art2real/트레일/trail10_cadrille"; sys.path[:0] = [T0, os.path.join(T0, "s0", "stub")]
from transformers import AutoConfig, AutoProcessor
from transformers.models.qwen2_vl.modeling_qwen2_vl import Qwen2VisionTransformerPretrainedModel
from safetensors import safe_open
from cadrille import collate
W = os.path.join(T0, "weights"); cfg = AutoConfig.from_pretrained(os.path.join(W, "cadrille")).vision_config; cfg._attn_implementation = "sdpa"
m = Qwen2VisionTransformerPretrainedModel(cfg)
with safe_open(os.path.join(W, "cadrille", "model.safetensors"), "pt") as f: m.load_state_dict({k[7:]: f.get_tensor(k) for k in f.keys() if k.startswith("visual.")}, strict=True)
m = m.to("cuda", torch.bfloat16).eval()
proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
fs = [os.path.join(sys.argv[1], k + ".png") for k in sorted(json.load(open(sys.argv[3], encoding="utf-8")))] if len(sys.argv) > 3 else sorted(glob.glob(os.path.join(sys.argv[1], "*.png")))
out = []
with torch.no_grad():
    for p in fs:
        x = collate([{"video": [Image.open(p).convert("RGB")], "description": "Generate cadquery code", "file_name": ""}], processor=proc, n_points=256, eval=True)
        out.append(m(x["pixel_values_videos"].to("cuda", torch.bfloat16), grid_thw=x["video_grid_thw"].to("cuda")).half().cpu().numpy())
np.save(sys.argv[2], np.stack(out)); print("ok", len(out))
