# -*- coding: utf-8 -*-
"""**왼쪽 원화 알베도 분할 · 오른쪽 UV.** 번호와 색이 같은 판이다.

    python panel_order.py          # blender 안 쓴다

왼쪽은 정면 원화(rgb_front) 위에 panels.json 의 판 18개를 얹고 번호를 찍은 것.
오른쪽은 그 번호를 그대로 쓴 UV 아틀라스.
라벨 18 은 `side/lav` 라 정면 원화에 없다 — 아틀라스 면적의 55.8% 인데 정면엔 안 뜬다.
"""
import os, json, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
T4 = os.path.join(HERE, "..", "trail4_gen3d")
import sys; sys.path.insert(0, HERE)
import mask2d

S, W = 460, 1024
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)

META = json.load(open(os.path.join(OUT, "tri_meta.json"), encoding="utf-8"))
PN = {p["id"]: p for p in json.load(open(os.path.join(HERE, "parts", "panels.json"), encoding="utf-8"))["panels"]}
d = np.load(os.path.join(OUT, "panel_dump.npz"))
uv, ls, lt, lab, area = d["uv"], d["ls"], d["lt"], d["lab"], d["area"]
nf = len(ls)
IDS = sorted(int(x) for x in np.unique(lab))
rs = np.random.RandomState(7)
PC = {L: tuple(rs.uniform(75, 235, 3)) for L in IDS}

# ── 왼쪽: 원화 + 판 ──────────────────────────────────────────────────────────
art = np.load(os.path.join(T4, "rgb_front.npy")).astype(float)
base = art[..., :3].copy()
base[art[..., 3] < 128] = 32
lm = {}
for L in IDS:
    if L < 0 or L >= len(META) or not META[L].startswith("front/"):
        continue
    pid = int(re.findall(r"\d+", META[L].split("/")[1])[0])
    if pid not in PN:
        continue
    m = mask2d.raster([np.array(PN[pid]["poly"], float)])
    if m.any():
        lm[L] = m
        base[m] = base[m] * 0.35 + np.array(PC[L]) * 0.65
allm = np.any(list(lm.values()), 0)
ys, xs = np.where(allm)
y0, y1 = max(ys.min()-24, 0), min(ys.max()+24, 1024)
x0, x1 = max(xs.min()-24, 0), min(xs.max()+24, 1024)
n = max(y1-y0, x1-x0)
y0 = max(min(y0, 1024-n), 0); x0 = max(min(x0, 1024-n), 0)
left = Image.fromarray(np.clip(base[y0:y0+n, x0:x0+n], 0, 255).astype(np.uint8)).resize((S, S), Image.NEAREST)
CL = {L: (((np.where(m)[1].mean()-x0)/n)*S, ((np.where(m)[0].mean()-y0)/n)*S) for L, m in lm.items()}

# ── 오른쪽: UV ───────────────────────────────────────────────────────────────
img = np.zeros((S, S, 3), np.float32); hit = np.zeros((S, S), bool)
sx = np.clip(uv[:, 0], 0, 1)*(S-1); sy = (1-np.clip(uv[:, 1], 0, 1))*(S-1)
for i in range(nf):
    c = PC[int(lab[i])]
    for a, b, cc in [(ls[i], ls[i]+k, ls[i]+k+1) for k in range(1, lt[i]-1)]:
        x = sx[[a, b, cc]]; y = sy[[a, b, cc]]
        xa = max(int(x.min()), 0); xb = min(int(np.ceil(x.max()))+1, S)
        ya = max(int(y.min()), 0); yb = min(int(np.ceil(y.max()))+1, S)
        if xb <= xa or yb <= ya: continue
        gy, gx = np.mgrid[ya:yb, xa:xb]; px = gx+.5; py = gy+.5
        det = (y[1]-y[2])*(x[0]-x[2]) + (x[2]-x[1])*(y[0]-y[2])
        if abs(det) < 1e-12: continue
        w0 = ((y[1]-y[2])*(px-x[2]) + (x[2]-x[1])*(py-y[2]))/det
        w1 = ((y[2]-y[0])*(px-x[2]) + (x[0]-x[2])*(py-y[2]))/det
        mm = (w0 >= -.004) & (w1 >= -.004) & (w0+w1 <= 1.004)
        if mm.any(): img[gy[mm], gx[mm]] = c; hit[gy[mm], gx[mm]] = True
a = img.copy(); gy, gx = np.mgrid[0:S, 0:S]
a[~hit] = ((((gx//12)+(gy//12)) % 2).astype(float)*10+26)[~hit][:, None]
right = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
CR = {}
for L in IDS:
    k = lab == L
    pts = np.concatenate([uv[ls[i]:ls[i]+lt[i]] for i in np.where(k)[0]])
    CR[L] = (pts[:, 0].mean()*S, (1-pts[:, 1].mean())*S)

# ── 시트 (1024 정사각) ───────────────────────────────────────────────────────
sh = Image.new("RGB", (W, W), (24, 24, 28)); dr = ImageDraw.Draw(sh)
dr.text((16, 12), "왼쪽 = 원화 알베도 분할 (panels.json)   ·   오른쪽 = 같은 번호의 UV 아틀라스",
        font=F(19), fill=(235, 235, 240))
for k, (im, cen, t) in enumerate([(left, CL, "정면 원화 — 판 라벨"), (right, CR, "아틀라스 — 같은 판 라벨")]):
    x = 16 + k*(S+16); y = 46
    sh.paste(im, (x, y))
    for L, (cu, cv) in cen.items():
        dr.text((x+cu-8, y+cv-9), str(L), font=F(17), fill=(12, 12, 12),
                stroke_width=2, stroke_fill=(255, 255, 255))
    dr.rectangle([x, y, x+S-1, y+S-1], outline=(70, 70, 80))
    dr.text((x, y+S+6), t, font=F(17), fill=(250, 250, 255))

# 범례
ty = 46 + S + 34
dr.text((16, ty), "판   색   원화 이름        아틀라스 면적%   섬", font=F(15), fill=(200, 200, 210))
ty += 22
tot = area.sum()
for i, L in enumerate(IDS):
    col = 16 + (i % 2)*(S+16); row = ty + (i//2)*21
    dr.rectangle([col, row+3, col+13, row+15], fill=tuple(int(v) for v in PC[L]))
    nm = META[L] if 0 <= L < len(META) else "라벨없음"
    k = lab == L
    isls = len(set(tuple(np.round(uv[ls[i2]]*20000).astype(int)) for i2 in np.where(k)[0]))
    dr.text((col+20, row), "%-4d %-16s %5.1f%%   %d면" % (L, nm, area[k].sum()/tot*100, k.sum()),
            font=F(14), fill=(180, 180, 190))
p = os.path.join(OUT, "panel_order.png"); sh.save(p); print(p, sh.size)
