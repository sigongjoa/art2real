# -*- coding: utf-8 -*-
"""5-2 · 5-3 · 5-4 · 5-5 · 5-7 · 5-11: 5장_블렌더.py 렌더(_raw/5_*.png)를 흰 바탕 1920×1080 에 놓고 (a)(b) 이름표 · 화살표.
5-2 (b) 는 선 그림이라 여기서 shapely 로 직접 그린다. python 5장_합치기.py"""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon
from shapely import affinity
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "_raw"); OUT = os.path.dirname(HERE)
W, H = 1920, 1080; FONT = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 38)

def raw(n):
    im = Image.open(os.path.join(RAW, "5_%s.png" % n)).convert("RGBA"); return im.crop(im.getbbox())

def place(cv, im, cx, cy, bw, bh):
    s = min(bw / im.width, bh / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    cv.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im); return im.size

def label(dr, s, cx, cy):
    b = dr.textbbox((0, 0), s, font=FONT); dr.text((cx - (b[2] - b[0]) / 2, cy - (b[3] - b[1]) / 2 - b[1]), s, font=FONT, fill=(40, 40, 40))

def panels(name, keys, box_w, box_h, y=500, ly=None, same=False):
    cv = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(cv); n = len(keys)
    ims = [raw(k) for k in keys]; s0 = min(min(box_w / im.width, box_h / im.height) for im in ims)
    xs = [W / 2 + (i - (n - 1) / 2) * (1540 / n) for i in range(n)]
    for i, k in enumerate(keys):
        im = ims[i]
        if same: im = im.resize((int(im.width * s0), int(im.height * s0)), Image.LANCZOS)
        sz = place(cv, im, xs[i], y, box_w, box_h) if not same else (cv.paste(im, (int(xs[i] - im.width / 2), int(y - im.height / 2)), im) or im.size)
        if n > 1: label(dr, "(%s)" % "abc"[i], xs[i], ly or (y + box_h / 2 + 50))
    cv.save(os.path.join(OUT, name + ".png")); print("저장", name)

def arrow(dr, p, q, w=6, col=(0, 0, 0)):
    dr.line([p, q], fill=col, width=w); v = np.subtract(q, p); v = v / np.linalg.norm(v); n = np.array([-v[1], v[0]])
    a = np.array(q); dr.polygon([tuple(a), tuple(a - 30 * v + 13 * n), tuple(a - 30 * v - 13 * n)], fill=col)

# ---------- 5-2: (a) 원기둥 감은 덩어리 · (b) 다리 안쪽 선이 몸속으로 들어가 끝난다 ----------
cv = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(cv)
place(cv, raw("2a"), 640, 500, 640, 820); label(dr, "(a)", 640, 975)
# (b): 4 배 크게 그려 줄여 매끈하게
from shapely.geometry import LineString
S = 4; U = 120; big = Image.new("L", (760 * S, 1000 * S), 255); bd = ImageDraw.Draw(big)
T = lambda x, y: ((x + 3.15) * U * S, (4.1 - y) * U * S)
body = affinity.translate(affinity.scale(Point(0, 0).buffer(1, 128), 1.55, 1.5), 0, 1.0)
neck = Polygon([(-0.5, 2.0), (-0.35, 3.3), (0.15, 3.6), (0.4, 3.0), (0.6, 2.0)])
legL = Polygon([(-1.5, 0.6), (-0.15, 0.3), (-0.75, -3.3), (-1.05, -3.6), (-1.3, -2.6)])
legR = affinity.scale(legL, -1, 1, origin=(0, 0))
sil = unary_union([body, neck, legL, legR]).buffer(0.05).buffer(-0.05)
dr_line = lambda pts: bd.line([T(*p) for p in pts], fill=0, width=7 * S, joint="curve")
from shapely.geometry import box as sbox
crotch = [np.array(LineString([(sx * 0.75, -3.3), (sx * 0.15, 0.3)]).intersection(body.exterior).coords[0]) for sx in (-1, 1)]
edge = sil.exterior.difference(sbox(crotch[0][0] + 0.01, crotch[0][1] - 0.3, crotch[1][0] - 0.01, crotch[0][1] + 0.2))   # 다리 사이 몸 밑선은 지운다 → 안쪽 선이 몸속으로 이어진다
for g in getattr(edge, "geoms", [edge]): dr_line(list(g.coords))
tips = []
for sx in (-1, 1):   # 다리 안쪽 선을 몸속으로 늘이고 끝은 바깥으로 말린 갈고리
    lo, hi = np.array([sx * 0.75, -3.3]), np.array([sx * 0.15, 0.3]); d = (hi - lo) / np.linalg.norm(hi - lo)
    p0 = np.array(LineString([tuple(lo), tuple(hi)]).intersection(body.exterior).coords[0]); tips.append(p0)
    e = p0 + d * 0.75; c = e + np.array([sx * 0.22, 0.0])
    hook = [tuple(c + 0.22 * np.array([-sx * np.cos(t), np.sin(t)])) for t in np.linspace(0, 2.6, 12)]
    dr_line([tuple(p0 - d * 0.02), tuple(e)] + hook)
bim = big.resize((760, 1000), Image.LANCZOS).convert("RGB"); bb = Image.eval(bim, lambda v: 255 - v).getbbox(); bim = bim.crop(bb)
ox, oy = 1300 - bim.width / 2, 490 - bim.height / 2; cv.paste(bim, (int(ox), int(oy)))
for sx, p0 in zip((-1, 1), tips):   # 화살표: 다리 안쪽 선(늘이면 예각으로 만난다)
    q = np.array(T(*(p0 + np.array([sx * 0.05, -0.55])))) / S - np.array(bb[:2]) + (ox, oy)
    arrow(dr, tuple(q + (sx * 150, 80)), tuple(q + (sx * 16, 8)))
label(dr, "(b)", 1280, 975)
cv.save(os.path.join(OUT, "5-2.png")); print("저장 5-2")

panels("5-3", ["3"], 900, 940, y=530)
panels("5-4", ["4a", "4b", "4c"], 480, 620, y=480, ly=900)
panels("5-5", ["5a", "5b"], 720, 600, y=480, ly=900)
panels("5-7", ["7"], 1300, 900, y=530)
panels("5-11", ["11a", "11b"], 700, 600, y=480, ly=900, same=True)
