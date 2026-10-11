# 기능0 최종 — 35 부품 사람(노랑) / 기능 짓기(주황) 한 장 · 10-11
import os, sys, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 200
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]; ids = [i for i in range(36) if i != 30]; cols = 5; w = 2 * C + 30
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, 색): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [1, .6, .8], img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
im = Image.new("RGB", (cols * w + 20, 80 + ((len(ids) + cols - 1) // cols) * (C + 30)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 짓기 35 부품: 사람 부품(노랑) · 기능 짓기(주황) — 같은 방향", font=F(30), fill="black")
for q, i in enumerate(ids):
    x = 10 + (q % cols) * w; y = 70 + (q // cols) * (C + 30)
    im.paste(그(정(trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh")), None), (x, y))
    im.paste(그(정(trimesh.load(os.path.join(H, os.environ.get("FIN", "최종"), "%02d.stl" % i))), (0.98, 0.62, 0.35)), (x + C, y))
    d.text((x + 5, y + 2), "#%d" % i, font=F(24), fill="black")
im.save(os.path.join(H, os.environ.get("OUT", "최종.png"))); print("ok")
