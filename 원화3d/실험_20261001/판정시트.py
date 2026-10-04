# -*- coding: utf-8 -*-
"""판정 시트 — 원형사 패널 조작 O1(검은 실루엣) + O6(전후 같은 카메라) 한 장으로 (10-04 자가개선 루프용).
python 판정시트.py <출력이름> "<제목1>=<ply1>" "<제목2>=<ply2>" ...
없는 렌더(<ply>_{정면,옆,34}.png · <ply>_검_*.png)는 헤드리스 블렌더 win3.py 로 만든다. 맨 위 줄 = 원화.
구멍 = 검은 실루엣 안에 갇힌 흰 화소 / 채운 실루엣(정면 · 옆 · 3/4)."""
import os, sys, subprocess, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
A = "G:/art2real/원화3d/out/오메가몬2/지표/각도데이터/"; B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"
BL = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"; W3 = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/7cb277a7-139e-42d2-8434-a71e5084b8ad/scratchpad/win3.py"
F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 24); S = 330; 칸 = ("정면", "옆", "34")
def 렌더(n):
    if not os.path.exists(B + f"{n}_34.png"): subprocess.run([BL, "-b", "-P", W3, "--", n], capture_output=True)
def 검(n):
    if not os.path.exists(B + f"{n}_검.ply"):
        m = trimesh.load(B + n + ".ply", process=False)
        trimesh.Trimesh(m.vertices, m.faces, vertex_colors=np.tile([0, 0, 0, 255], (len(m.vertices), 1)).astype(np.uint8), process=False).export(B + f"{n}_검.ply", encoding="ascii")
    렌더(n + "_검")
def fit(g):
    s = min(S / g.width, S / g.height); g = g.resize((int(g.width * s), int(g.height * s))); c = Image.new("RGB", (S, S), "white"); c.paste(g, ((S - g.width) // 2, (S - g.height) // 2)); return c
def ren(n, k):
    g = Image.open(B + f"{n}_{k}.png").convert("RGB"); a = np.array(g.convert("L")); ys, xs = np.nonzero(np.abs(a.astype(int) - int(a[2, 2])) > 6)
    return fit(g.crop((xs.min() - 8, ys.min() - 8, xs.max() + 8, ys.max() + 8)))
def black(n, k):
    g = np.array(Image.open(B + f"{n}_검_{k}.png").convert("L")); m = g < 60; ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; f = ndimage.binary_fill_holes(m)
    return fit(Image.fromarray(np.where(m, 0, 255).astype(np.uint8)).convert("RGB")), round(float((f & ~m).sum() / f.sum()), 3)
def art(i):
    box = [(20, 0, 240, 301), (0, 0, 499, 301), (0, 0, 330, 301)][i]
    return fit(Image.open(A + f"판_{i + 1}_원화.png").convert("RGB").crop(box)), fit(Image.fromarray(np.where(np.load(A + f"판_{i + 1}_Z.npz")["m"], 0, 255).astype(np.uint8)).convert("RGB"))
out = sys.argv[1]; rows = [("원화", None)] + [tuple(a.split("=", 1)) for a in sys.argv[2:]]
o = Image.new("RGB", (S * 6 + 20, len(rows) * (S + 40)), "white"); d = ImageDraw.Draw(o); 기록 = {}
for i, (t, n) in enumerate(rows):
    y = i * (S + 40)
    if n: 렌더(n); 검(n)
    for j, k in enumerate(칸):
        if n is None: a_, b_ = art(j); o.paste(a_, (j * S, y + 40)); o.paste(b_, (3 * S + 20 + j * S, y + 40))
        else: o.paste(ren(n, k), (j * S, y + 40)); b, h = black(n, k); o.paste(b, (3 * S + 20 + j * S, y + 40)); 기록.setdefault(t, []).append(h)
    d.text((8, y + 6), t + (f" · 구멍 {기록[t]}" if t in 기록 else ""), font=F, fill="black")
o.save(B + out + ".png"); print(기록)
