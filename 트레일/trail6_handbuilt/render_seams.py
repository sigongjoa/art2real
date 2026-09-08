# -*- coding: utf-8 -*-
"""각도별 UV 를 한 장으로. 섬마다 색 하나 — 조각이 몇 개인지 눈으로 세게."""
import os, glob, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = "out"; A = 420
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)


def fan(ls, lt):
    """면(삼각형이든 쿼드든)을 부채꼴 삼각화해 루프 인덱스 삼각형 목록으로."""
    out = []
    for s, n in zip(ls, lt):
        out += [(s, s + k, s + k + 1) for k in range(1, n - 1)]
    return np.array(out, np.int64)


def islands(uv, tri_loops):
    """UV 정점을 좌표로 용접해 연결성분을 센다 (= 섬)."""
    q = np.round(uv * 20000).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    tri = inv[tri_loops]
    n = inv.max() + 1; par = np.arange(n)
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for t in tri:
        r = find(t[0])
        for v in t[1:]:
            s = find(v)
            if r != s: par[s] = r
    lab = np.array([find(i) for i in range(n)])
    _, lab = np.unique(lab, return_inverse=True)
    return lab[tri[:, 0]], lab.max() + 1


def bake(uv, tri_loops, col):
    sx = np.clip(uv[:, 0], 0, 1) * (A - 1); sy = (1 - np.clip(uv[:, 1], 0, 1)) * (A - 1)
    img = np.zeros((A, A, 3), np.float32); hit = np.zeros((A, A), bool)
    for t in range(len(tri_loops)):
        x, y = sx[tri_loops[t]], sy[tri_loops[t]]
        x0 = max(int(x.min()), 0); x1 = min(int(np.ceil(x.max())) + 1, A)
        y0 = max(int(y.min()), 0); y1 = min(int(np.ceil(y.max())) + 1, A)
        if x1 <= x0 or y1 <= y0: continue
        gy, gx = np.mgrid[y0:y1, x0:x1]; px = gx + .5; py = gy + .5
        det = (y[1]-y[2])*(x[0]-x[2]) + (x[2]-x[1])*(y[0]-y[2])
        if abs(det) < 1e-12: continue
        w0 = ((y[1]-y[2])*(px-x[2]) + (x[2]-x[1])*(py-y[2])) / det
        w1 = ((y[2]-y[0])*(px-x[2]) + (x[0]-x[2])*(py-y[2])) / det
        m = (w0 >= -.004) & (w1 >= -.004) & (w0 + w1 <= 1.004)
        if m.any(): img[gy[m], gx[m]] = col[t]; hit[gy[m], gx[m]] = True
    a = img.copy(); gy, gx = np.mgrid[0:A, 0:A]
    chk = (((gx//12)+(gy//12)) % 2).astype(float)*10 + 26
    a[~hit] = chk[~hit][:, None]
    return a, hit.mean()*100


# 인자로 다른 스윕도 같은 자로 잰다:  python render_seams.py retopo_q "..." _리토폴로지.png
PRE, TITLE, DST = (sys.argv + ["seam_",
    "능선을 이음선으로 못 박고 각도 스윕 — 섬마다 색 하나 (생성 견갑 71,842면)",
    "_능선각도.png"])[1:4]
files = sorted(glob.glob(os.path.join(OUT, PRE + "*.npz")),
               key=lambda p: int(re.findall(r'\d+', os.path.basename(p))[0]))
rs = np.random.RandomState(1)
cells = []
for f in files:
    ang = int(re.findall(r'\d+', os.path.basename(f))[0])
    d = np.load(f); uv = d["uv"]
    tl = fan(d["ls"], d["lt"])
    lab, n = islands(uv, tl)
    img, fill = bake(uv, tl, rs.uniform(60, 235, (n, 3))[lab])
    cells.append((img, "%s%d" % (PRE, ang), "섬 %d · 채움 %.1f%%" % (n, fill)))
    print("%2d도  섬 %5d  채움 %.1f%%" % (ang, n, fill))

C = 3; R = (len(cells)+C-1)//C; PAD, CAP, TOP = 14, 54, 48
W = C*A + (C+1)*PAD; H = TOP + R*(A+CAP) + (R+1)*PAD
sh = Image.new("RGB", (W, H), (24, 24, 28)); dr = ImageDraw.Draw(sh)
dr.text((PAD, 13), TITLE,
        font=F(22), fill=(235, 235, 240))
for i, (img, t, s) in enumerate(cells):
    r, c = divmod(i, C); x = PAD + c*(A+PAD); y = TOP + PAD + r*(A+CAP+PAD)
    sh.paste(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), (x, y))
    dr.rectangle([x, y, x+A-1, y+A-1], outline=(70, 70, 80))
    dr.text((x, y+A+5), t, font=F(18), fill=(250, 250, 255))
    dr.text((x, y+A+28), s, font=F(15), fill=(165, 165, 180))
p = os.path.join(OUT, DST); sh.save(p); print("\n"+p, sh.size)
