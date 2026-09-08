# -*- coding: utf-8 -*-
"""판 이음선 UV 를 **한 장**으로. 섬 그림에는 섬 번호를 찍는다 (대응표와 맞춰 보라고)."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
S, PAD, CAP, TOP = 420, 16, 66, 54
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)

PANELS = [
    ("panel_island.png", "UV 섬 47개 (번호)", "판 경계 = 이음선 · 순도 100% · 섞인섬 0"),
    ("panel_col.png",    "구운 색",           "채움 59.8% · 밀도편차 2.44 · 판마다 평면색 하나"),
    ("panel_prov.png",   "출처",              "초록 직접 / 노랑 전파 / 파랑 뿔계급 · 후면 보정 49면"),
]

# 섬 번호를 찍을 자리 = UV 공간의 섬 무게중심
d = np.load(os.path.join(OUT, "panel_q800.npz"))
uv, ls, lt = d["uv"], d["ls"], d["lt"]
_, inv = np.unique(np.round(uv * 20000).astype(np.int64), axis=0, return_inverse=True)
par = np.arange(inv.max() + 1)
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for i in range(len(ls)):
    r = find(inv[ls[i]])
    for k in range(1, lt[i]):
        t = find(inv[ls[i] + k])
        if r != t: par[t] = r
root = np.array([find(inv[ls[i]]) for i in range(len(ls))])
_, isl = np.unique(root, return_inverse=True)
cent, wt = {}, {}
for i in range(len(ls)):
    P = uv[ls[i]:ls[i] + lt[i]]
    cent[isl[i]] = cent.get(isl[i], np.zeros(2)) + P.mean(0) * lt[i]
    wt[isl[i]] = wt.get(isl[i], 0) + lt[i]
CENT = {k: cent[k] / wt[k] for k in cent}
BIG = sorted(wt, key=lambda k: -wt[k])[:18]        # 작은 섬에 번호 찍으면 글자만 보인다

COLS = 3
ROWS = (len(PANELS) + COLS - 1) // COLS
W = COLS * S + (COLS + 1) * PAD
H = TOP + ROWS * (S + CAP) + (ROWS + 1) * PAD
sheet = Image.new("RGB", (W, H), (24, 24, 28))
dr = ImageDraw.Draw(sheet)
dr.text((PAD, 16), "어깨 갑주 UV   ·   723 쿼드 · 판 15개 -> 섬 47개 (일대다) · 후면 보정 포함",
        font=F(19), fill=(235, 235, 240))

for i, (fn, title, sub) in enumerate(PANELS):
    p = os.path.join(OUT, fn)
    if not os.path.exists(p):
        continue
    r, c = divmod(i, COLS)
    x = PAD + c * (S + PAD)
    y = TOP + PAD + r * (S + CAP + PAD)
    sheet.paste(Image.open(p).convert("RGB").resize((S, S), Image.NEAREST), (x, y))
    if i == 0:                                      # 섬 번호
        for k in BIG:
            u, v = CENT[k]
            tx = x + u * (S - 1); ty = y + (1 - v) * (S - 1)
            dr.text((tx - 7, ty - 8), str(k), font=F(15), fill=(15, 15, 15),
                    stroke_width=2, stroke_fill=(255, 255, 255))
    dr.rectangle([x, y, x + S - 1, y + S - 1], outline=(70, 70, 80))
    dr.text((x, y + S + 6), title, font=F(18), fill=(250, 250, 255))
    dr.text((x, y + S + 30), sub, font=F(14), fill=(165, 165, 180))

out = os.path.join(OUT, "_UV비교.png")
sheet.save(out)
print(out, sheet.size)
