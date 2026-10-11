# 기능0 결과 — 사람 / 모 판 선 고리 / 기능 짓기 · 세 방향 렌더 · 10-11
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 260
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, v, 색): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
V = ([1, .6, .8], [-1, -.6, -.8], [.3, -.9, .4]); 열 = ["사람 부품", "모 판 선 고리 (지금까지 최선)", "기능 짓기 (손)"]
im = Image.new("RGB", (130 + 9 * C + 40, 110 + 2 * (C + 50)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 짓기 천장 시험: CAD 설계 순서로 손으로 지은 #4 #21", font=F(28), fill="black")
for j, t in enumerate(열): d.text((130 + j * (3 * C + 20) + 3 * C // 2, 80), t, font=F(22), fill=(31, 95, 173), anchor="mm")
for r_, i in enumerate((4, 21)):
    y = 100 + r_ * (C + 50); d.text((15, y + C // 2), "#%d" % i, font=F(32), fill="black")
    ms = [trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh"), trimesh.load(os.path.join(R, "선고리", "결과_A_모", "%02d_선고리.stl" % i)), trimesh.load(os.path.join(H, "결과", "%02d.stl" % i))]
    es = [None, json.load(open(os.path.join(R, "선고리", "결과_A_모", "%02d.json" % i), encoding="utf-8"))["edge_f1"], json.load(open(os.path.join(H, "결과", "%02d.json" % i), encoding="utf-8"))["edge_f1"]]
    for j, (m, e) in enumerate(zip(ms, es)):
        for q, v in enumerate(V): im.paste(그(정(m), v, None if j == 0 else ((0.45, 0.68, 0.98) if j == 1 else (0.98, 0.62, 0.35))), (130 + j * (3 * C + 20) + q * C, y))
        if e is not None: d.text((130 + j * (3 * C + 20) + 3 * C // 2, y + C + 18), "점수 %.2f" % e, font=F(22), fill="black", anchor="mm")
im.save(os.path.join(H, "결과.png")); print("ok")
