# -*- coding: utf-8 -*-
"""정면·측면·후면 알베도 분할을 한 장으로. 640² 팔레트 PNG (그래야 뜬다)."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); T4 = os.path.join(HERE, "..", "trail4_gen3d")
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)
MINPX = 40
VW = json.load(open(os.path.join(HERE, "parts", "views.json"), encoding="utf-8"))
SRC = [("front", "_L_alb.npy", [612, 726, 98, 277]),
       ("side",  "_L_alb_side.npy", VW["side"]["win"]),
       ("back",  "_L_alb_back.npy", VW["back"]["win"])]

H = 300
cells = []
for v, lf, (x0, x1, y0, y1) in SRC:
    L = np.load(os.path.join(OUT, lf))
    art = np.load(os.path.join(T4, "rgb_%s.npy" % v))
    C = art[y0:y1, x0:x1, :3].astype(float)
    A = art[y0:y1, x0:x1, 3]
    ids = [int(x) for x in np.unique(L) if x > 1 and (L == x).sum() >= MINPX]
    rs = np.random.RandomState(11)
    img = C.copy(); img[A < 128] = 30
    for i in ids:
        m = L == i
        img[m] = img[m] * 0.35 + rs.uniform(70, 235, 3) * 0.65
    h, w = img.shape[:2]
    sc = H / h
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((max(int(w*sc), 8), H), Image.NEAREST)
    cells.append((im, v, len(ids)))

PAD, TOP = 14, 46
W = sum(c[0].width for c in cells) + PAD*(len(cells)+1)
CAN = max(W, 640)
sh = Image.new("RGB", (CAN, 640), (24, 24, 28)); dr = ImageDraw.Draw(sh)
dr.text((PAD, 12), "알베도 분할 — 세 판 전부. 측면·후면은 오늘 처음 나눴다", font=F(18), fill=(235, 235, 240))
x = PAD
for im, v, n in cells:
    sh.paste(im, (x, TOP))
    dr.rectangle([x, TOP, x+im.width-1, TOP+im.height-1], outline=(70, 70, 80))
    dr.text((x, TOP+im.height+6), "%s — 판 %d개" % (v, n), font=F(16), fill=(250, 250, 255))
    x += im.width + PAD

ty = TOP + H + 40
for line in ["front  18판  (커밋된 원본 panels.json)          아틀라스 라벨 0~17",
             "side   67판  <- 지금까지 라벨 하나였다 (side/lav, 아틀라스 면적 55.8%)",
             "back   32판  (금 17 · 어두움 9 · 라벤더 6)      <- 아예 안 쓰던 판",
             "",
             "측면 크롭에 남의 부품이 섞여 있다 (white 16개) — 견갑 마스크를 아직 안 씌웠다.",
             "다음: 판별 마스크로 거르고 -> 면마다 어느 판/어느 판넬인지 다시 배정 -> UV 재구성"]:
    dr.text((PAD, ty), line, font=F(15), fill=(180, 180, 190)); ty += 24

sh = sh.resize((640, int(640*640/CAN)) if CAN > 640 else (640, 640), Image.LANCZOS)
sh = sh.convert("P", palette=Image.ADAPTIVE, colors=48)
p = os.path.join(OUT, "views_sheet.png"); sh.save(p, optimize=True)
print(p, sh.size, os.path.getsize(p), "bytes")
