# 5 판 결과 — 셸이 걸린 부품: 사람 / 가(셸 없음) / 셸6 · 두 방향 렌더 · 10-11
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [H, os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 230
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]
줄 = [(1, "A"), (4, "A"), (21, "A"), (24, "A"), (23, "B")]
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, v, 색): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
열 = ["사람 부품", "가 (셸 없음)", "5 판 (셸)"]; V = ([1, .6, .8], [-1, -.6, -.8])
im = Image.new("RGB", (150 + 6 * C + 40, 110 + len(줄) * (C + 40)), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "5 판 결과: 벽 ≤ 6 일 때만 속 비움 — 걸린 부품을 앞 · 뒤 두 방향에서", font=F(26), fill="black")
for j, t in enumerate(열): d.text((150 + j * (2 * C + 10) + C, 80), t, font=F(22), fill=(31, 95, 173), anchor="mm")
for r_, (i, 판) in enumerate(줄):
    y = 100 + r_ * (C + 40); d.text((15, y + C // 2 - 15), "#%d" % i, font=F(30), fill="black"); d.text((15, y + C // 2 + 20), "%s 깊이" % ("정답" if 판 == "A" else "AI"), font=F(18), fill=(90, 90, 90))
    ms = [trimesh.load("G:/art2real/원화3d/out/레퍼런스/사람분할/" + str(부[i]), force="mesh")] + [trimesh.load(os.path.join(H, "결과_%s_%s" % (판, s), "%02d_선고리.stl" % i)) for s in ("가", "셸6")]
    es = [None] + [json.load(open(os.path.join(H, "결과_%s_%s" % (판, s), "%02d.json" % i), encoding="utf-8"))["edge_f1"] for s in ("가", "셸6")]
    for j, (m, e) in enumerate(zip(ms, es)):
        for q, v in enumerate(V): im.paste(그(정(m), v, None if j == 0 else (0.45, 0.68, 0.98)), (150 + j * (2 * C + 10) + q * C, y))
        if e is not None: d.text((150 + j * (2 * C + 10) + C, y + C + 12), "점수 %.2f" % e, font=F(20), fill=(40, 150, 60) if e >= .42 else (200, 40, 40), anchor="mm")
im.save(os.path.join(H, "셸6결과.png")); print("ok")
