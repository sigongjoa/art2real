# -*- coding: utf-8 -*-
"""음영민감도 의 SDXL 한 장 — imggen venv 에서 돈다 (`음영민감도.py 입력` 이 부른다). 점토 렌더의 **큰 명암만** 쓴다."""
import os
import sys

os.environ["HF_HOME"] = r"D:\imggen\hf"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
import torch
from PIL import Image
from diffusers import StableDiffusionXLImg2ImgPipeline

src, dst = sys.argv[1], sys.argv[2]
STRENGTH = float(sys.argv[4]) if len(sys.argv) > 4 else 0.50
init = Image.open(src).convert("RGB")
w, h = init.size
init = init.resize((w // 8 * 8, h // 8 * 8), Image.LANCZOS)
P = ("full body collectible figure of a tall thin pale man standing straight, arms slightly spread, long black coat, "
     "3d render, grey clay statue, soft studio lighting from upper left, strong ambient occlusion, clear folds, "
     "clear rounded volume, plain white background, centered")
if len(sys.argv) > 3 and sys.argv[3]:
    P = sys.argv[3]
N = "text, watermark, multiple characters, cropped, blurry, extra limbs, dark background, flat colors, lineart"
pipe = StableDiffusionXLImg2ImgPipeline.from_single_file(r"D:\imggen\models\animagine-xl-4.0-opt.safetensors", torch_dtype=torch.float16, use_safetensors=True)
pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling(); pipe.enable_attention_slicing()
im = pipe(prompt=P, negative_prompt=N, image=init, strength=STRENGTH, guidance_scale=7.0, num_inference_steps=34,
          generator=torch.Generator("cuda").manual_seed(5)).images[0]
im.resize((w, h), Image.LANCZOS).save(dst)
print("->", dst)
