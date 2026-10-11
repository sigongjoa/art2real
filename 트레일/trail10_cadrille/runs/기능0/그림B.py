# 기능0 학습 결과 — 사람 / 통과된 한 벌(정답 깊이) / 옛 학생 깊이 / 새 학생 깊이 · 한 방향 · 35 부품 · 10-11
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 170
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]; ids = [i for i in range(36) if i != 30]
열 = [("사람", None, None), ("통과된 한 벌", "디테일", (0.98, 0.62, 0.35)), ("옛 학생 깊이", "B_모델", (0.45, 0.68, 0.98)), ("새 학생 깊이", "B_모델T", (0.55, 0.8, 0.5))]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, 색): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [1, .6, .8], img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
cols = 3; w = 4 * C + 60
im = Image.new("RGB", (cols * w + 20, 110 + ((len(ids) + cols - 1) // cols) * (C + 10)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "학습 결과: 사람 · 통과된 한 벌 · 옛 학생 깊이 · 새 학생 깊이 (선 그림만 보고 지음)", font=F(28), fill="black")
for c in range(cols):
    for j, (t, _, _) in enumerate(열): d.text((10 + c * w + 50 + j * C + C // 2, 80), t, font=F(18), fill=(31, 95, 173), anchor="mm")
for q, i in enumerate(ids):
    x = 10 + (q % cols) * w; y = 100 + (q // cols) * (C + 10); d.text((x, y + 5), "#%d" % i, font=F(22), fill="black")
    for j, (t, f, 색) in enumerate(열):
        m = trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh") if f is None else trimesh.load(os.path.join(H, f, "%02d.stl" % i))
        im.paste(그(정(m), 색), (x + 50 + j * C, y))
im.save(os.path.join(H, "결과B.png")); print("ok")
