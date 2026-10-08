# 교사2 LoRA 가 학습 예제(교사 vs 수확)를 얼마나 맞히나 — 예제별 손실 + 탐욕 생성 첫 줄
import os, sys, glob, torch, numpy as np
from PIL import Image
sys.path[:0] = [".", "s0", "s0/stub"]
from transformers import AutoProcessor
from peft import PeftModel
from cadrille import Cadrille, collate
W = "weights"; d = "runs/교사1/data/train"
model = Cadrille.from_pretrained(W + "/cadrille", torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
model = PeftModel.from_pretrained(model, sys.argv[1] if len(sys.argv) > 1 else "runs/교사2/lora/lora"); model.eval()
proc = AutoProcessor.from_pretrained(W + "/qwen2vl2b", min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
fs = sorted(glob.glob(d + "/*.py")); teach = fs[396::3][:6]; harv = fs[:396:66]
for nm, grp in (("교사", teach), ("수확", harv)):
    L = []
    for p in grp:
        code = open(p, encoding="utf-8").read(); img = Image.open(p[:-3] + ".png").convert("RGB")
        b = collate([{"video": [img], "description": "Generate cadquery code", "answer": code}], processor=proc, n_points=256, eval=False)
        b = {k: (v.cuda() if torch.is_tensor(v) else v) for k, v in b.items()}
        with torch.no_grad(): L.append(model(**b).loss.item())
    print(nm, "손실", [round(x, 3) for x in L])
    p = grp[0]; img = Image.open(p[:-3] + ".png").convert("RGB")
    b = collate([{"video": [img], "description": "Generate cadquery code", "file_name": "x"}], processor=proc, n_points=256, eval=True)
    with torch.no_grad():
        o = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(), pixel_values_videos=b["pixel_values_videos"].cuda(), video_grid_thw=b["video_grid_thw"].cuda(), max_new_tokens=120, do_sample=False)
    print(nm, "정답 앞:", open(p, encoding="utf-8").read()[:120].replace("\n", " | "))
    print(nm, "생성 앞:", proc.batch_decode(o[:, b["input_ids"].shape[1]:], skip_special_tokens=True)[0][:120].replace("\n", " | "))
