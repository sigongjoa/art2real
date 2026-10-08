# -*- coding: utf-8 -*-
"""인코더0 — 합성 부품 그림 → 얼린 인코더 특징(npy) · 후보: cadrille / qwen원본 / dino / 픽셀(대조)
python runs/인코더0/특징.py <후보>  →  runs/인코더0/특징_<후보>.npy (행 = 정답.json 키 순서)"""
import os, sys, json, numpy as np, torch
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(os.path.dirname(H)); sys.path[:0] = [T, os.path.join(T, "s0", "stub")]
W = os.path.join(T, "weights"); 후보 = sys.argv[1]
키 = sorted(json.load(open(os.path.join(H, "정답.json"), encoding="utf-8"))); ims = [Image.open(os.path.join(H, "합성", k + ".png")).convert("RGB") for k in 키]

def qwen(ckpt):
    from transformers import AutoConfig, AutoProcessor
    from transformers.models.qwen2_vl.modeling_qwen2_vl import Qwen2VisionTransformerPretrainedModel
    from safetensors import safe_open
    from cadrille import collate
    cfg = AutoConfig.from_pretrained(os.path.join(W, "cadrille")).vision_config; cfg._attn_implementation = "sdpa"
    m = Qwen2VisionTransformerPretrainedModel(cfg)
    with safe_open(ckpt, "pt") as f: sd = {k[7:]: f.get_tensor(k) for k in f.keys() if k.startswith("visual.")}
    print(m.load_state_dict(sd, strict=True)); m = m.to("cuda", torch.bfloat16).eval()
    proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
    out = []
    with torch.no_grad():
        for g in ims:   # 학습 때와 같은 입력 경로(collate · video 한 장)
            x = collate([{"video": [g], "description": "Generate cadquery code"}], processor=proc, n_points=256, eval=True)
            t = m(x["pixel_values_videos"].to("cuda", torch.bfloat16), grid_thw=x["video_grid_thw"].to("cuda")).float()
            out.append(torch.cat([t.mean(0), t.max(0).values]).cpu().numpy())
    return np.stack(out)

def dino():
    from transformers import AutoModel, AutoImageProcessor
    m = AutoModel.from_pretrained(os.path.join(W, "dinov2_base")).to("cuda").eval()
    p = AutoImageProcessor.from_pretrained(os.path.join(W, "dinov2_base"), do_center_crop=False, size={"shortest_edge": 224})
    out = []
    with torch.no_grad():
        for i in range(0, len(ims), 32):
            h = m(**p(images=ims[i:i + 32], return_tensors="pt").to("cuda")).last_hidden_state
            out.append(torch.cat([h[:, 0], h[:, 1:].mean(1)], 1).cpu().numpy())
    return np.concatenate(out)

f = {"cadrille": lambda: qwen(os.path.join(W, "cadrille", "model.safetensors")),
     "qwen원본": lambda: qwen(os.path.join(W, "qwen2vl2b_원본", "model-00001-of-00002.safetensors")),
     "dino": dino,
     "픽셀": lambda: np.stack([np.asarray(g.convert("L").resize((64, 64)), np.float32).ravel() / 255 for g in ims])}[후보]()
np.save(os.path.join(H, "특징_%s.npy" % 후보), f); print(후보, f.shape)
