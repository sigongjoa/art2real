"""시험판 배경 — imggen venv 의 SDXL(animagine) 로 하늘 · 먼 언덕 한 장. 블렌더 뒤 판으로 쓴다.
    D:/imggen/venv/Scripts/python.exe 시험판_배경.py <출력.png>"""
import sys, torch
from diffusers import StableDiffusionXLPipeline
pipe = StableDiffusionXLPipeline.from_single_file(r"D:\imggen\models\animagine-xl-4.0-opt.safetensors", torch_dtype=torch.float16, use_safetensors=True)
pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
im = pipe("no humans, scenery, wide blue sky, fluffy white clouds, distant soft green hills, a few round trees, pastel colors, soft light, clean simple background, masterpiece, best quality",
          negative_prompt="people, character, text, watermark, buildings, dark, lowres, blurry",
          width=832, height=1216, num_inference_steps=28, guidance_scale=6, generator=torch.Generator("cpu").manual_seed(7)).images[0]
im.save(sys.argv[1])
