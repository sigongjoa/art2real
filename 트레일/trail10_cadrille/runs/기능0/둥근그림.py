# 둥근 찾기 눈 검사 — 부품마다 사람 렌더 + 가장 많이 찾은 두 방향 깊이 그림에 칠(빨강 공 · 주황 소켓 · 파랑 볼록 원기둥 · 하늘 오목 원기둥) · 10-11
import os, sys, numpy as np, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont
from 도구 import *
import 둥근찾기 as G
sys.path.insert(0, os.path.join(os.path.dirname(R), "s0"))
from render import render
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 210
색 = {("구", False): (220, 50, 50), ("구", True): (240, 150, 40), ("원기둥", False): (50, 110, 220), ("원기둥", True): (90, 200, 230)}
ids = [int(a) for a in sys.argv[2:]]; 이름 = sys.argv[1]; cols = 3; w = 3 * C + 40
im = Image.new("RGB", (cols * w + 20, 120 + ((len(ids) + cols - 1) // cols) * (C + 50)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "둥근 찾기: 빨강 공 · 주황 소켓(오목 구) · 파랑 볼록 원기둥 · 하늘 오목 원기둥", font=F(28), fill="black")
for q, i in enumerate(ids):
    x0, y0 = 10 + (q % cols) * w, 70 + (q // cols) * (C + 50)
    합, 낱 = G.찾기(i); X = 입력(i); D = X[3]
    m = trimesh.load(W.RR + str(부[i]), force="mesh"); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(.9 / max(m.extents)); m.apply_translation([.5] * 3)
    im.paste(Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [1, .6, .8], img_size=C))), (x0, y0))
    쪽순 = sorted(range(6), key=lambda k: -sum(f["넓이"] for f in 낱 if f["쪽"] == k))[:2]
    for j, k in enumerate(쪽순):
        s = X[0][k] > .5; v = np.where(s, D[k], np.nan); lo, hi = np.nanmin(v), np.nanmax(v)
        g = np.where(s, 60 + 170 * (1 - (D[k] - lo) / max(hi - lo, 1e-6)), 255).astype(np.uint8); a = np.stack([g] * 3, -1)
        for f in 낱:
            if f["쪽"] == k: a[f["_m"]] = (.45 * a[f["_m"]] + .55 * np.array(색[(f["종류"], f["오목"])])).astype(np.uint8)
        im.paste(Image.fromarray(cv2.resize(a, (C, C), interpolation=cv2.INTER_NEAREST)), (x0 + (j + 1) * C + 10, y0))
    d.text((x0 + 5, y0 + 2), "#%d" % i, font=F(26), fill="black")
    d.text((x0 + 5, y0 + C + 8), " · ".join("%s%s R%.0f" % ("소켓" if f["종류"] == "구" and f["오목"] else "공" if f["종류"] == "구" else "원기둥", "(오목)" if f["종류"] == "원기둥" and f["오목"] else "", f["R"]) for f in 합[:4]), font=F(17), fill=(60, 60, 70))
im.save(os.path.join(H, 이름)); print("ok")
