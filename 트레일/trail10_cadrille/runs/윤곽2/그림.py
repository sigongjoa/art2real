# -*- coding: utf-8 -*-
"""윤곽2 그림 — 사람 부품 · 바탕(윤곽 교차) · 깊이 깎기 · 점수"""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 210; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
ids = [int(a) for a in sys.argv[1:]] or [7, 19, 24, 12, 5, 17, 25, 35]
S = [r for i in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % i), encoding="utf-8"))]
def 그림(m, blue=False):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3)
    return render(np.asarray(m.vertices), np.asarray(m.faces), [1, 0.6, 0.8], img_size=C, cols=np.tile([0.45, 0.68, 0.98], (len(m.faces), 1)) if blue else None)
im = Image.new("RGB", (C * 3 + 60, 60 + len(ids) * (C + 34)), "white"); d = ImageDraw.Draw(im)
for k, t in enumerate(["사람 부품", "바탕: 윤곽 교차", "+ 깊이 깎기"]): d.text((20 + k * (C + 20), 15), t, font=F(22), fill="black")
for r_, i in enumerate(ids):
    y = 50 + r_ * (C + 34); res = json.load(open(os.path.join(H, "결과", "%02d.json" % i), encoding="utf-8"))
    im.paste(그림(trimesh.load(RR + S[i]["부품"], force="mesh")), (20, y))
    im.paste(그림(trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)), True), (40 + C, y))
    p = os.path.join(H, "결과", "%02d_깎음.stl" % i)
    if os.path.exists(p): im.paste(그림(trimesh.load(p), True), (60 + 2 * C, y))
    d.text((20, y + C + 4), "#%d · 손 %.2f" % (i, S[i]["edge_f1"]), font=F(19), fill=(90, 90, 90))
    for k, v in ((1, res["바탕"]), (2, res["edge_f1"])): d.text((20 + k * (C + 20), y + C + 4), "%.2f" % v, font=F(19), fill=(40, 150, 60) if v >= .42 else (200, 40, 40))
im.save(os.path.join(H, "깎기그림.png")); print("ok")
