# 기능0 — 35 부품 썸네일 (사람 부품 두 방향 + 위 · 앞 · 옆 선 그림) · 기본 형태 나누기용 · 10-11
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 200
T = np.load(os.path.join(R, "깊이학습", "시험.npz")); 부 = T["부품"]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
형 = {i: k for k, v in json.load(open(os.path.join(H, "형태.json"), encoding="utf-8")).items() for i in v}; 색 = dict(zip(["휜 껍질", "속 빈 상자(셸)", "돌출(한 윤곽 밀기)", "회전체 + 블록(관절)", "다면 덩어리", "여러 덩어리"], [(200, 40, 40), (230, 120, 20), (40, 150, 60), (31, 95, 173), (120, 60, 160), (90, 90, 90)]))
ids = [i for i in range(len(부)) if i != 30]; cols = 3
im = Image.new("RGB", (cols * (2 * C + 3 * 110 + 40), ((len(ids) + cols - 1) // cols) * (C + 40) + 20), "white"); d = ImageDraw.Draw(im)
for n, i in enumerate(ids):
    x = (n % cols) * (2 * C + 3 * 110 + 40); y = 10 + (n // cols) * (C + 40)
    m = 정(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh"))
    for q, v in enumerate(([1, .6, .8], [-1, -.6, -.8])): im.paste(Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C))), (x + 30 + q * C, y))
    for q, k in enumerate((0, 2, 4)):
        s = (T["X"][i][0][k] > .5); a = np.where(s, 225, 255).astype(np.uint8); im.paste(Image.fromarray(cv2.resize(a, (100, 100), interpolation=cv2.INTER_NEAREST)), (x + 30 + 2 * C + q * 110, y + 50))
    d.text((x + 5, y + 5), "#%d" % i, font=F(26), fill="black"); d.text((x + 30 + 2 * C, y + 10), 형.get(i, "?"), font=F(22), fill=색.get(형.get(i), "black")); d.text((x + 30, y + C + 5), str(부[i])[:46], font=F(13), fill=(90, 90, 90))
im.save(os.path.join(H, "썸네일.png")); print(im.size)
