# -*- coding: utf-8 -*-
"""손으로 지은 것(형태) + 오늘의 3판 매핑(색) 대 생성 메시. 원화와 나란히."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); T4 = os.path.join(HERE, "..", "trail4_gen3d")
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)
S, PAD, TOP, BG = 236, 12, 44, (24, 24, 28)


def onbg(im):
    im = im.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", im.size, BG+(255,)), im).convert("RGB")


def sq(im):
    n = max(im.size); c = Image.new("RGB", (n, n), BG)
    c.paste(im, ((n-im.width)//2, (n-im.height)//2)); return c


art = np.load(os.path.join(T4, "rgb_front.npy"))
left = sq(onbg(Image.fromarray(art[98:277, 612:726].astype(np.uint8), "RGBA"))).resize((S, S), Image.LANCZOS)

ROWS = [("원화", [(left, "정면 원화"), (None, ""), (None, ""), (None, "")]),
        ("손으로 지은 286면 + 43판 색",
         [("pad_front.png", "정면"), ("pad_q.png", "3/4"), ("pad_back.png", "후면"), ("pad43_col.png", "UV (섬 5)")]),
        ("생성 71,842 -> 리토폴로지 723 + 43판 색",
         [("shot_front.png", "정면"), ("shot_q.png", "3/4"), ("shot_back.png", "후면"), ("panel_col.png", "UV (섬 98)")])]

W = 1024
sh = Image.new("RGB", (W, W), BG); dr = ImageDraw.Draw(sh)
dr.text((PAD, 12), "형태는 지어서 낸 것, 색은 오늘의 3판 매핑   ·   아래 줄이 생성 메시", font=F(17), fill=(235, 235, 240))
y = TOP
for title, cells in ROWS:
    dr.text((PAD, y), title, font=F(15), fill=(215, 215, 225)); y += 20
    for i, (src, cap) in enumerate(cells):
        if src is None: continue
        im = src if isinstance(src, Image.Image) else (
            Image.open(os.path.join(OUT, src)).convert("RGB").resize((S, S), Image.NEAREST)
            if "col" in str(src) else onbg(Image.open(os.path.join(OUT, src))).resize((S, S), Image.LANCZOS))
        x = PAD + i*(S+PAD)
        sh.paste(im, (x, y))
        dr.rectangle([x, y, x+S-1, y+S-1], outline=(70, 70, 80))
        dr.text((x, y+S+3), cap, font=F(13), fill=(200, 200, 210))
    y += S + 26

ty = y + 8
for line in ["                       실루엣 IoU   섬    순도    직접    밀도편차",
             "손으로 지은 286면        0.713      5      —     83.9%     1.3     <- 뿔이 이름 있는 부품이다",
             "리토폴로지 723 쿼드      0.642     98    100%    89.0%     1.57",
             "",
             "전개도를 언랩기에 안 맡기고 지을 때 같이 냈다 (build.py layout, 72번).",
             "뿔은 맞추는 게 아니라 지어 넣은 것 — 그래서 실루엣이 딴 물건으로 안 읽힌다.",
             "색은 오늘 만든 front 15 + side 12 + back 16 판이 둘 다에 그대로 얹힌다 (31.8% -> 83.9%)."]:
    dr.text((PAD, ty), line, font=F(14), fill=(180, 180, 190)); ty += 20

p = os.path.join(OUT, "final_sheet.png"); sh.save(p)
print(p, sh.size, os.path.getsize(p), "bytes")
