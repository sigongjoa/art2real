# -*- coding: utf-8 -*-
"""실물0 그림 — 사람 부품 · 디코더+다듬기 · 상자+다듬기 · (모서리 점수) · 사전0 은 점수만"""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path[:0] = [os.path.join(os.path.dirname(R), "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 220; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
A = json.load(open(os.path.join(H, "디코더", "결과.json"), encoding="utf-8")); B = json.load(open(os.path.join(H, "대조_상자", "결과.json"), encoding="utf-8")); V2 = json.load(open(os.path.join(H, "디코더v2", "결과.json"), encoding="utf-8"))
S = [r for i in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % i), encoding="utf-8"))]
ids = [int(a) for a in sys.argv[1:]] or [2, 6, 8, 11, 14, 27, 32, 35]
def 그림(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3)
    return render(np.asarray(m.vertices), np.asarray(m.faces), [1, 0.6, 0.8], img_size=C)
im = Image.new("RGB", (C * 4 + 80, 70 + len(ids) * (C + 40)), "white"); d = ImageDraw.Draw(im)
for k, t in enumerate(["사람 부품", "v1 (합성만)", "v2 (회전 + 실물)", "상자 대조"]): d.text((20 + k * (C + 20), 20), t, font=F(24), fill="black")
for r, i in enumerate(ids):
    y = 60 + r * (C + 40); im.paste(그림(trimesh.load(RR + A[i]["부품"], force="mesh")), (20, y))
    for k, (d_, E) in enumerate((("디코더", A), ("디코더v2", V2), ("대조_상자", B))):
        p = os.path.join(H, d_, "%02d_예측.stl" % i)
        if os.path.exists(p): im.paste(그림(trimesh.load(p)), (20 + (k + 1) * (C + 20), y))
        else: d.text((20 + (k + 1) * (C + 20) + 60, y + 100), "조각 없음", font=F(22), fill="red")
        d.text((20 + (k + 1) * (C + 20), y + C + 4), "모서리 %.2f" % E[i]["edge_f1"], font=F(20), fill=(40, 150, 60) if E[i]["edge_f1"] >= .42 else (200, 40, 40))
    d.text((20, y + C + 4), "#%d · 사전0(손) %.2f" % (i, S[i]["edge_f1"]), font=F(20), fill=(90, 90, 90))
im.save(os.path.join(H, "실물그림_v2.png")); print("ok")
