# 기능0 2 판 결과 — 사람 / 모 판 선 고리 / 기능 바탕만 / 기능 바탕 + 선 고리 · 10-11
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 220
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]; ids = (4, 21, 24, 8, 32, 22, 13, 10)
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, v, 색): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
열 = [("사람 부품", None, None), ("모 판 + 선 고리", os.path.join(R, "선고리", "결과_A_모", "%02d_선고리.stl"), os.path.join(R, "선고리", "결과_A_모", "%02d.json")),
      ("기능 바탕만 (손)", os.path.join(H, "결과", "%02d.stl"), os.path.join(H, "결과", "%02d.json")), ("기능 바탕 + 선 고리", os.path.join(R, "선고리", "결과_A_기능", "%02d_선고리.stl"), os.path.join(R, "선고리", "결과_A_기능", "%02d.json"))]
색 = [None, (0.45, 0.68, 0.98), (0.98, 0.62, 0.35), (0.55, 0.8, 0.5)]; V = ([1, .6, .8], [-1, -.6, -.8]); w = 2 * C + 20
im = Image.new("RGB", (100 + 4 * w, 100 + len(ids) * (C + 40)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 2 판: 손 기능 바탕 위에 선 고리를 얹으면", font=F(28), fill="black")
for j, (t, _, _) in enumerate(열): d.text((100 + j * w + C, 75), t, font=F(22), fill=(31, 95, 173), anchor="mm")
for r_, i in enumerate(ids):
    y = 95 + r_ * (C + 40); d.text((10, y + C // 2), "#%d" % i, font=F(28), fill="black")
    for j, (t, f, jf) in enumerate(열):
        m = trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh") if f is None else trimesh.load(f % i)
        for q, v in enumerate(V): im.paste(그(정(m), v, 색[j]), (100 + j * w + q * C, y))
        if jf: e = json.load(open(jf % i, encoding="utf-8")); d.text((100 + j * w + C, y + C + 14), "점수 %.2f · 조각 %d" % (e["edge_f1"], e.get("조각", 0)), font=F(19), fill="black", anchor="mm")
im.save(os.path.join(H, "결과2.png")); print("ok")
