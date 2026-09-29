# -*- coding: utf-8 -*-
"""캡처를 부위(판)로 나눈다 — 먹선 연결성분은 720p 에서 선이 끊겨 실패(분할_*_비교.png) → SAM(transformers · facebook/sam-vit-base)에 판마다 점 프롬프트.
    python 분할.py -> out/오메가몬2/지표/분할_<캡처>.png (부위 색 · 프롬프트 점 흰색) · 분할_<캡처>.npz(마스크)
프롬프트 점은 격자 그림에서 손으로 읽은 원본 px. 부위 이름 = 지식 위키 부위/머리 의 낱말.
"""
import os, sys, json
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
from transformers import SamModel, SamProcessor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
색 = {"투구": (120, 160, 255), "뿔": (200, 200, 220), "차양": (255, 120, 40), "눈": (230, 40, 40), "코": (255, 220, 0), "입": (0, 190, 90), "볼": (200, 90, 230), "안테나": (255, 190, 0), "턱": (0, 130, 160)}
캡처 = {
    "정면 yt_172": ("yt_172.0_얼굴_정면.jpg", (700, 150, 1060, 520), {"투구": [(870, 230), (800, 270)], "뿔": [(887, 150)], "차양L": [(815, 312)], "차양R": [(950, 318)], "눈L": [(822, 352)], "눈R": [(905, 370)], "코": [(880, 380)], "입": [(865, 440)], "턱": [(875, 475)], "볼L": [(760, 380)], "볼R": [(965, 360)], "안테나L": [(775, 190)], "안테나R": [(990, 210)]}),
    "옆 yt_235":  ("yt_235.0_머리_옆.jpg", (420, 0, 820, 320), {"투구": [(700, 60)], "뿔": [(540, 40)], "차양": [(540, 110)], "눈": [(630, 118)], "코": [(495, 170)], "입": [(520, 230)], "턱": [(590, 270)], "볼": [(700, 200)], "안테나": [(780, 118)]}),
}
if __name__ == "__main__":
    dev = "cuda" if torch.cuda.is_available() else "cpu"; model = SamModel.from_pretrained("facebook/sam-vit-base").to(dev); proc = SamProcessor.from_pretrained("facebook/sam-vit-base")
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 16)
    for 이름, (f, box, 점들) in 캡처.items():
        im = Image.open(J(장면, f)).convert("RGB").crop(box); s = 3; im = im.resize((im.width * s, im.height * s), Image.LANCZOS)
        마스크 = {}; ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
        for 부위, pts in 점들.items():
            P = [[[(x - box[0]) * s, (y - box[1]) * s] for x, y in pts]]
            inp = proc(im, input_points=P, return_tensors="pt").to(dev)
            with torch.no_grad(): out = model(**inp)
            m = proc.image_processor.post_process_masks(out.pred_masks.cpu(), inp["original_sizes"].cpu(), inp["reshaped_input_sizes"].cpu())[0][0]   # (3, H, W)
            sc = out.iou_scores[0, 0].cpu().numpy(); a = m.numpy().sum((1, 2))
            # 세 후보 중: 너무 큰 것(그림 1/3 넘음)은 빼고 점수 높은 것
            cand = [i for i in range(3) if a[i] < 0.33 * m.shape[1] * m.shape[2]] or [int(np.argmin(a))]; i = max(cand, key=lambda i: sc[i]); mk = m[i].numpy()
            마스크[부위] = mk; c = 색[부위.rstrip("LR")]; col = Image.new("RGBA", im.size, c + (110,)); ov.paste(col, (0, 0), Image.fromarray((mk * 255).astype(np.uint8)))
        vis = Image.alpha_composite(im.convert("RGBA"), ov); dr = ImageDraw.Draw(vis)
        for 부위, pts in 점들.items():
            for x, y in pts: X, Y = (x - box[0]) * s, (y - box[1]) * s; dr.ellipse((X - 5, Y - 5, X + 5, Y + 5), fill=(255, 255, 255), outline=(0, 0, 0), width=2); dr.text((X + 7, Y - 8), 부위, font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
        p = J(OUT, "분할_%s.png" % 이름.replace("/", "-").replace(" ", "_")); vis.convert("RGB").save(p); np.savez_compressed(p[:-4] + ".npz", **마스크); print(p, {k: int(v.sum()) for k, v in 마스크.items()})
