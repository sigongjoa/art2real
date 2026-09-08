# -*- coding: utf-8 -*-
"""왼쪽 원화 · 가운데 텍스처 입힌 3D · 오른쪽 UV. 1024² 팔레트 PNG."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); T4 = os.path.join(HERE, "..", "trail4_gen3d")
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)
S, PAD, TOP = 320, 14, 44
BG = (24, 24, 28)


def onbg(im):
    im = im.convert("RGBA")
    b = Image.new("RGBA", im.size, BG + (255,))
    return Image.alpha_composite(b, im).convert("RGB")


# 왼쪽 — 정면 원화, 견갑 창으로 자른다
x0, x1, y0, y1 = 612, 726, 98, 277
art = np.load(os.path.join(T4, "rgb_front.npy"))
C = art[y0:y1, x0:x1].astype(np.uint8)
left = onbg(Image.fromarray(C, "RGBA"))
n = max(left.size); sq = Image.new("RGB", (n, n), BG)
sq.paste(left, ((n-left.width)//2, (n-left.height)//2))
left = sq.resize((S, S), Image.LANCZOS)

mid = onbg(Image.open(os.path.join(OUT, "shot_front.png"))).resize((S, S), Image.LANCZOS)
right = Image.open(os.path.join(OUT, "panel_col.png")).convert("RGB").resize((S, S), Image.NEAREST)

W = 1024
sh = Image.new("RGB", (W, W), BG); dr = ImageDraw.Draw(sh)
dr.text((PAD, 12), "왼쪽 원화  ·  가운데 UV 텍스처를 도로 입힌 3D  ·  오른쪽 UV 아틀라스",
        font=F(19), fill=(235, 235, 240))
for i, (im, t) in enumerate([(left, "정면 원화"), (mid, "3D (평면 알베도)"), (right, "UV 아틀라스 47판")]):
    x = PAD + i*(S+PAD)
    sh.paste(im, (x, TOP))
    dr.rectangle([x, TOP, x+S-1, TOP+S-1], outline=(70, 70, 80))
    dr.text((x, TOP+S+6), t, font=F(16), fill=(250, 250, 255))

# 아래 줄 — 3/4 와 후면
y2 = TOP + S + 46
for i, (fn, t) in enumerate([("shot_q.png", "3/4"), ("shot_back.png", "후면"), (None, "")]):
    if not fn: continue
    im = onbg(Image.open(os.path.join(OUT, fn))).resize((S, S), Image.LANCZOS)
    x = PAD + i*(S+PAD)
    sh.paste(im, (x, y2))
    dr.rectangle([x, y2, x+S-1, y2+S-1], outline=(70, 70, 80))
    dr.text((x, y2+S+6), t, font=F(16), fill=(250, 250, 255))

ty = y2 + S + 40
for line in ["판 43개 (front 15 + side 12 + back 16)   섬 98   순도 100%   채움 64.9%",
             "직접 89.0% · 전파 11.0% · 미배정 0        밀도편차 1.57 (손으로 지은 것 1.3)",
             "팔레트 게이트로 적갈색 오염 20면 -> 4면 (0.6%), 하이라이트 판 2개도 같이 빠졌다"]:
    dr.text((PAD, ty), line, font=F(15), fill=(180, 180, 190)); ty += 23

sh = sh.convert("P", palette=Image.ADAPTIVE, colors=64)
p = os.path.join(OUT, "check3.png"); sh.save(p, optimize=True)
print(p, sh.size, os.path.getsize(p), "bytes")
