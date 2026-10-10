# 곡면 바닥 비교 GIF — 부품마다 줄 · 칸: 사람 / 바탕 / 지금 기본(기울기) / 곡면 바닥 · 한 바퀴 돌림
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 200; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
ids = [int(a) for a in sys.argv[1:]]; S = [r for i in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % i), encoding="utf-8"))]
열 = [("사람 부품", None), ("바탕", "바탕"), ("지금 기본", "결과_기울기02g"), ("곡면 바닥", "결과_곡면")]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
M = []
for i in ids:
    row = []
    for _, k in 열:
        p = RR + S[i]["부품"] if k is None else (os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i) if k == "바탕" else os.path.join(H, k, "%02d_깎음.stl" % i))
        row.append(정(trimesh.load(p, force="mesh")))
    sc = [None, json.load(open(os.path.join(H, "결과_기울기02g", "%02d.json" % i), encoding="utf-8"))["바탕"], json.load(open(os.path.join(H, "결과_기울기02g", "%02d.json" % i), encoding="utf-8"))["edge_f1"], json.load(open(os.path.join(H, "결과_곡면", "%02d.json" % i), encoding="utf-8"))["edge_f1"]]
    M.append((i, row, sc))
fr = []
for t in range(24):
    a = 2 * np.pi * t / 24; v = [np.cos(a), np.sin(a), 0.7]
    im = Image.new("RGB", (C * 4 + 50, 50 + len(M) * (C + 30)), "white"); d = ImageDraw.Draw(im)
    for j, (n, _) in enumerate(열): d.text((10 + j * (C + 10) + C // 2, 25), n, font=F(22), fill="black", anchor="mm")
    for r, (i, row, sc) in enumerate(M):
        y = 50 + r * (C + 30)
        for j, m in enumerate(row):
            im.paste(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C, cols=None if j == 0 else np.tile([0.45, 0.68, 0.98], (len(m.faces), 1))), (10 + j * (C + 10), y))
            if sc[j] is not None: d.text((10 + j * (C + 10) + C // 2, y + C + 12), "%.2f" % sc[j], font=F(20), fill=(40, 150, 60) if sc[j] >= .42 else (200, 40, 40), anchor="mm")
        d.text((14, y + 4), "#%d" % i, font=F(20), fill=(90, 90, 90))
    fr.append(im)
out = os.environ.get("OUTF", "곡면비교.gif"); fr[0].save(os.path.join(H, out), save_all=True, append_images=fr[1:], duration=120, loop=0); print("ok", out)
