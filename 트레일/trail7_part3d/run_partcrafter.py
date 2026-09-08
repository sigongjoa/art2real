# -*- coding: utf-8 -*-
"""PartCrafter(MIT) 로컬 실행. RTX 3050 8GB · torch 2.5.1+cu124 · py3.11 전용 venv.

    venv/Scripts/python.exe run_partcrafter.py in/pauldron_front.png out/pc_front --parts 5

TripoSG 를 백본으로 파인튜닝한 모델이라 VAE·좌표가 같다 (research_part3d_20260829).
`use_flash_decoder=False` 를 명시한다 — nvcc 가 없어 diso 를 못 깐다. TripoSG 때와 같은 제약.
파트마다 별개 메시로 나오므로 GLB 씬으로 저장하고 파트별 OBJ 도 같이 뽑는다.
"""
import argparse, os, sys, time
import numpy as np
import torch
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PC = os.path.join(HERE, "PartCrafter")
sys.path.insert(0, PC)
os.chdir(PC)

from huggingface_hub import snapshot_download
from src.pipelines.pipeline_partcrafter import PartCrafterPipeline
from src.models.briarmbg import BriaRMBG
from src.utils.image_utils import prepare_image
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out")
    ap.add_argument("--parts", type=int, default=5)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--tokens", type=int, default=1024)
    ap.add_argument("--guidance", type=float, default=7.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--rmbg", action="store_true")
    a = ap.parse_args()
    img = os.path.abspath(os.path.join(HERE, a.image)) if not os.path.isabs(a.image) else a.image
    out = os.path.abspath(os.path.join(HERE, a.out)) if not os.path.isabs(a.out) else a.out
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    t0 = time.time()
    w = snapshot_download(repo_id="wgsxm/PartCrafter", local_dir=os.path.join(HERE, "weights", "PartCrafter"))
    print("가중치 %s  (%.0fs)" % (w, time.time()-t0))

    pipe = PartCrafterPipeline.from_pretrained(w).to("cuda", torch.float16)
    im = Image.open(img).convert("RGBA")
    if a.rmbg:
        rm = BriaRMBG.from_pretrained("briaai/RMBG-1.4").to("cuda")
        im = prepare_image(img, bg_color=np.array([1.0, 1.0, 1.0]), rmbg_net=rm)
    else:
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")

    torch.cuda.reset_peak_memory_stats()
    t1 = time.time()
    outs = pipe(image=[im] * a.parts, attention_kwargs={"num_parts": a.parts},
                num_tokens=a.tokens, generator=torch.Generator(device="cuda").manual_seed(a.seed),
                num_inference_steps=a.steps, guidance_scale=a.guidance,
                max_num_expanded_coords=int(1e9), use_flash_decoder=False).meshes
    dt = time.time() - t1
    peak = torch.cuda.max_memory_allocated()/1e9

    sc = trimesh.Scene()
    tot = 0
    for i, m in enumerate(outs):
        if m is None:
            print("  파트 %d: 빈 메시" % i); continue
        m.export("%s_p%d.obj" % (out, i))
        sc.add_geometry(m, node_name="part%d" % i)
        tot += len(m.faces)
        print("  파트 %d  면 %6d  bbox %s" % (i, len(m.faces), np.round(m.bounds[1]-m.bounds[0], 3)))
    sc.export(out + ".glb")
    print("파트 %d개 · 면 합 %d · %.0f초 · 최대 VRAM %.2fGB -> %s.glb" % (len(outs), tot, dt, peak, out))


main()
