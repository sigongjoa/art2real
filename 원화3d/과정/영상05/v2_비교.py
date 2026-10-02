# -*- coding: utf-8 -*-
"""교재 원본(v1) | 새로 그린 그림(v2) 나란히 — python v2_비교.py <편 번호> → out/영상05/v2그림/_비교_<편>.jpg"""
import sys, glob, os, re
from PIL import Image, ImageDraw, ImageFont
n = sys.argv[1]; A = r"G:\art2real\out\영상05\v1\그림"; B = r"G:\art2real\out\영상05\v2그림"
f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 26)
ids = sorted({os.path.basename(p)[:-4] for p in glob.glob(os.path.join(A, n + "-*.png"))}, key=lambda s: int(s.split("-")[1]))
W, H = 560, 315; s = Image.new("RGB", (W * 2 + 30, (H + 40) * len(ids)), (40, 40, 48)); d = ImageDraw.Draw(s)
for i, k in enumerate(ids):
    y = i * (H + 40); d.text((10, y + 4), k, fill=(255, 200, 110), font=f)
    for j, base in enumerate((A, B)):
        p = os.path.join(base, k + ".png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB"); im.thumbnail((W, H)); s.paste(im, (10 + j * (W + 10) + (W - im.width) // 2, y + 36))
        else: d.text((10 + j * (W + 10) + 200, y + 150), "없음", fill=(255, 90, 90), font=f)
out = os.path.join(B, "_비교_%s.jpg" % n); s.save(out, quality=82); print(out, len(ids))
