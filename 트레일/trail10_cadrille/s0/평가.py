# -*- coding: utf-8 -*-
"""첫 학습 판정(돌리기 전 고정 · business_panel_첫학습_20261005): 시험 20 의 ① 모따기+홈 함께 비율 ② 실행 성공률 · ③ DeepCAD 대조 3 개 IoU(그림 모드)
python s0/평가.py <시험 폴더> <출력 json> [LoRA 폴더]"""
import os, sys, glob, json, numpy as np, torch, trimesh
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
from transformers import AutoProcessor
from cadrille import Cadrille, collate
import s0 as S
from lora import 읽기, 실행, 새연산
W = os.path.join(os.path.dirname(H), "weights")
te_dir, out = sys.argv[1], sys.argv[2]; lp = sys.argv[3] if len(sys.argv) > 3 else None
model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
if lp:
    from peft import PeftModel; model = PeftModel.from_pretrained(model, lp)
model.eval()
proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
def gen(img, name):
    b = collate([{"video": [img], "description": "Generate cadquery code", "file_name": name}], processor=proc, n_points=256, eval=True)
    with torch.no_grad():
        o = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                           pixel_values_videos=b["pixel_values_videos"].cuda(), video_grid_thw=b["video_grid_thw"].cuda(), max_new_tokens=768, do_sample=False)
    return proc.batch_decode([o[0][len(b["input_ids"][0]):]], skip_special_tokens=True)[0]
R = {"시험": [], "대조": {}}
for t in 읽기(te_dir):
    code = gen(t["img"], t["name"]); ch, cu = 새연산(code); ok = True; iou = None
    try:
        pm = 실행(code); gm = 실행(t["code"]); a = gm.copy(); a.apply_translation([-0.5] * 3); a.apply_scale(2); b = pm.copy(); b.apply_translation([-0.5] * 3); b.apply_scale(2); iou = S.iou(a, b)
    except Exception: ok = False
    R["시험"].append({"이름": t["name"], "실행": ok, "모따기": ch, "홈": cu, "IoU": iou, "코드": code})
for f in sorted(glob.glob(os.path.join(H, "in", "0000*.stl"))):
    gt = S.unit(trimesh.load(f)); it, g = S.item_img(gt); code = gen(g, "d")
    try:
        pm = S.run_code(code); pm.apply_scale(1 / 100.0); g2 = gt.copy(); g2.apply_translation([-0.5] * 3); g2.apply_scale(2.0); R["대조"][os.path.basename(f)] = S.iou(g2, pm)
    except Exception: R["대조"][os.path.basename(f)] = 0.0
n = len(R["시험"]); ious = [r["IoU"] for r in R["시험"] if r["IoU"] is not None]
R["요약"] = {"모따기+홈": sum(r["모따기"] and r["홈"] for r in R["시험"]) / n, "실행": sum(r["실행"] for r in R["시험"]) / n, "IoU중앙": float(np.median(ious)) if ious else 0.0, "대조": R["대조"]}
json.dump(R, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(R["요약"])
