# -*- coding: utf-8 -*-
"""겹깊이시험 깊이 단계 — DA3(09-22 ComfyUI)가 사라져 Depth Anything V2 Large(transformers · HF depth-anything/Depth-Anything-V2-Large-hf · CPU)로 대신.
출력 <모델>_<그림>_da3.npy (이름은 채점 스크립트와 맞춤 · 값 = 상대 깊이 · 클수록 멂으로 뒤집어 저장)."""
import os, glob, numpy as np, torch
from PIL import Image
from transformers import pipeline
D = r"G:\art2real\원화3d\out\오메가몬2\지표\겹깊이"
pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Large-hf", device=-1)
for f in sorted(glob.glob(os.path.join(D, "*_평면.png")) + glob.glob(os.path.join(D, "*_음영.png")) + glob.glob(os.path.join(D, "*_원화식.png")) + glob.glob(os.path.join(D, "*_강조.png"))):
    if os.path.exists(f[:-4] + "_da3.npy"): continue
    out = pipe(Image.open(f).convert("RGB")); d = out["predicted_depth"].squeeze().numpy().astype(np.float32)   # DA V2 = 역깊이(클수록 가까움)
    np.save(f[:-4] + "_da3.npy", -d); print(os.path.basename(f), d.shape, float(d.min()), float(d.max()), flush=True)
