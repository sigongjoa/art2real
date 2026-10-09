# -*- coding: utf-8 -*-
"""조각3 샘플 — 시험 부품마다: 입력 그림 · 정답 · 다듬기 전(조각2 디코더) · 다듬은 뒤 (같은 두 방향 렌더 · 점수)"""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(os.path.dirname(R), "s0")]
from 평가 import 메시
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
E2, E3 = [json.load(open(os.path.join(R, d, "평가.json"), encoding="utf-8")) for d in ("조각2", "조각3")]
ids = [int(a) for a in sys.argv[1:]] or [0, 1, 4, 5, 37, 120, 200, 333]; C = 200
cols = ["입력", "정답", "다듬기 전 (디코더)", "다듬은 뒤"]
im = Image.new("RGB", (C * 2 + C * 6 + 120, 70 + len(ids) * (C + 34)), "white"); d = ImageDraw.Draw(im)
for k, t in enumerate(cols): d.text((20 + (0 if k == 0 else C * 2 + 40 + (k - 1) * (C * 2 + 20)), 20), t, font=F(26), fill="black")
for r, i in enumerate(ids):
    y = 60 + r * (C + 34); im.paste(Image.open(os.path.join(R, "조각0", "합성", "%04d.png" % (3600 + i))).resize((C, C)), (20, y))
    Q = json.load(open(os.path.join(R, "조각0", "정답", "%04d.json" % (3600 + i)), encoding="utf-8"))
    for k, (P, e) in enumerate(((Q, None), (E2["예측"][i], E2["디코더"][i]), (E3["예측"][i], E3["디코더"][i]))):
        x0 = C * 2 + 40 + k * (C * 2 + 20)
        try:
            m = 메시(P); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(1 / max(m.extents)); m.apply_translation([.5] * 3)
            for j, f in enumerate(([1, 1, 1], [-1, 0.3, 0.2])): im.paste(render(np.asarray(m.vertices), np.asarray(m.faces), f, img_size=C), (x0 + j * C, y))
        except Exception as ex: d.text((x0, y + 80), "못 지음", font=F(22), fill="red")
        if e: d.text((x0, y + C + 2), "모서리 %.2f · IoU %.2f" % (e["edge_f1"], e["iou"]), font=F(20), fill=(40, 150, 60) if e["edge_f1"] >= .42 else (200, 40, 40))
im.save(os.path.join(H, "샘플.png")); print("ok")
