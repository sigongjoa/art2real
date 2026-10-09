# -*- coding: utf-8 -*-
"""윤곽0 그림 — 사람 부품 · 3 방향 윤곽 교차(학습 없음) · 손으로 쓴 사전0 · 점수 · 두 방향"""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 200; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
ids = [int(a) for a in sys.argv[1:]] or [2, 8, 11, 17, 7, 19, 21, 35]
S = [r for i in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % i), encoding="utf-8"))]
def 그림(m, f, blue=False):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3)
    return render(np.asarray(m.vertices), np.asarray(m.faces), f, img_size=C, cols=np.tile([0.45, 0.68, 0.98], (len(m.faces), 1)) if blue else None)
VS = ([1, 0.6, 0.8], [-1, 0.3, -0.6])
im = Image.new("RGB", (C * 4 + 60, 60 + len(ids) * (C + 34)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "사람 부품 (두 방향)", font=F(22), fill="black"); d.text((C * 2 + 40, 15), "3 방향 윤곽 교차 · 학습 없음", font=F(22), fill=(60, 110, 220))
for r, i in enumerate(ids):
    y = 50 + r * (C + 34); g = trimesh.load(RR + S[i]["부품"], force="mesh"); res = json.load(open(os.path.join(H, "결과", "%02d.json" % i), encoding="utf-8"))
    for k, f in enumerate(VS): im.paste(그림(g, f), (20 + k * C, y))
    p = os.path.join(H, "결과", "%02d_교차.stl" % i)
    if os.path.exists(p):
        b = trimesh.load(p)
        for k, f in enumerate(VS): im.paste(그림(b, f, True), (C * 2 + 40 + k * C, y))
    d.text((20, y + C + 4), "#%d · 손(사전0) %.2f" % (i, S[i]["edge_f1"]), font=F(19), fill=(90, 90, 90))
    d.text((C * 2 + 40, y + C + 4), "윤곽 교차 %.2f" % res["B"], font=F(19), fill=(40, 150, 60) if res["B"] >= .42 else (200, 40, 40))
im.save(os.path.join(H, "윤곽그림.png")); print("ok")
