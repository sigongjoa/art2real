# 정답 부품 소개 — 사람 부품 75(개발 35 · 검증 40) 썸네일 + 이름 · 모델 · 규칙 라벨 · 우리 결과는 안 넣음 · 10-11
# python runs/기능0/부품소개.py  →  부품소개.png
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 150
L = json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"]
색 = {"상자형": (60, 120, 220), "곡면": (220, 110, 40), "섞임": (150, 110, 190), "얇은 판·껍질": (40, 150, 140), "속 빔·오목": (120, 120, 60), "막대": (200, 60, 120),
      "관통 구멍": (90, 90, 90), "여러 덩이": (180, 80, 60), "디테일 많음": (60, 150, 60), "열린 메시": (220, 50, 50)}
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
cols, cw, ch = 5, 380, C + 70; 키 = list(L)
im = Image.new("RGB", (cols * cw + 20, 120 + 2 * 60 + ((len(키) + cols) // cols + 1) * ch), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "정답 부품 소개 — 사람이 만든 부품 %d 개 (개발 35 · 검증 40) · 라벨은 사람 부품만 보고 규칙으로" % len(키), font=F(28), fill="black")
x0 = 20
for t, c in 색.items(): d.rounded_rectangle((x0, 62, x0 + 14 * len(t) + 24, 92), 8, fill=c); d.text((x0 + 12, 77), t, font=F(16), fill="white", anchor="lm"); x0 += 14 * len(t) + 34
y = 110
for 세트 in ("시험", "검증"):
    ks = [k for k in 키 if k.startswith(세트)]; d.text((20, y + 10), "개발 세트 (지으면서 본 부품)" if 세트 == "시험" else "검증 세트 (처음 보는 부품 · 학습에서 모델째 뺌)", font=F(26), fill=(31, 95, 173)); y += 55
    for q, k in enumerate(ks):
        x, yy = 10 + (q % cols) * cw, y + (q // cols) * ch; v = L[k]
        g = Image.fromarray(np.asarray(render(*(lambda m: (np.asarray(m.vertices), np.asarray(m.faces)))(정(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + v["부품"], force="mesh"))), [1, .6, .8], img_size=C, cols=None)))
        im.paste(g, (x, yy)); d.text((x + C + 8, yy + 4), "#" + k.split("/")[1], font=F(22), fill="black")
        d.text((x + C + 8, yy + 34), v["이름"][:16], font=F(15), fill=(40, 40, 50)); d.text((x + C + 8, yy + 54), v["모델"].split("_", 1)[-1][:18], font=F(13), fill=(110, 110, 110))
        for j, t in enumerate(v["라벨"][:5]): d.rounded_rectangle((x + C + 8, yy + 76 + j * 22, x + C + 18 + 13 * len(t), yy + 96 + j * 22), 6, fill=색.get(t, (0, 0, 0))); d.text((x + C + 13, yy + 86 + j * 22), t, font=F(13), fill="white", anchor="lm")
    y += ((len(ks) + cols - 1) // cols) * ch + 20
im = im.crop((0, 0, im.width, y)); im.save(os.path.join(H, "부품소개.png")); print("ok", im.size)
