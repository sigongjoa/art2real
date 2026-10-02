# -*- coding: utf-8 -*-
"""4-1 · 4-7 다시(10-02): 손전등 선 렌더(3D/g5_손전등_선.png) 위에 같은 회색 가림 조각 여섯 — 4-1 은 이음매(꼭짓점)에, 4-7 은 선 중간에.
같은 조각 · 같은 크기 · 자리만 다르다."""
import json, math, random
from PIL import Image, ImageDraw
R = r"G:\art2real\out\영상05"
line = Image.open(R + r"\3D\g5_손전등_선.png").convert("RGB")
J = json.load(open(R + r"\3D\g5_오목부.json", encoding="utf-8"))
joints = list(J.values()) + [(960, 330), (960, 520), (230, 350)]   # 렌즈 테 이음 · 끝마개 이음까지
# 선 중간 자리: 몸통 위 · 아래 선, 머리 원뿔 두 옆선, 렌즈 테 둥근 선, 끝마개 옆 몸통
mids = [(520, 300), (520, 452), (870, 323), (870, 470), (1040, 400), (420, 286), (650, 330), (400, 432)]
def blob(d, cx, cy, r, seed):
    random.seed(seed); pts = []
    for k in range(14):
        a = 2 * math.pi * k / 14; rr = r * random.uniform(0.7, 1.15); pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=(105, 105, 115), outline=(255, 255, 255), width=3)
def make(spots, out):
    im = line.copy(); d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate(spots): blob(d, x, y, 56, i)
    c = Image.new("RGB", (1920, 1080), (255, 255, 255)); s = 1.45; im2 = im.resize((int(im.width * s), int(im.height * s)))
    c.paste(im2, ((1920 - im2.width) // 2, (1080 - im2.height) // 2)); c.save(out)
make(joints, R + r"\v2그림\4-1.png"); make(mids, R + r"\v2그림\4-7.png")
