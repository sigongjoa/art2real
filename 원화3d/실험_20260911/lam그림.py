# -*- coding: utf-8 -*-
"""벤치lam.jsonl -> out/lam비교.png + 표.

    python lam그림.py <벤치lam.jsonl>

점 = 판본 IoU - **제 부피의 균일 침식** (격자128). 오른쪽이 이긴 것. 맨 아래 표는 두 격자,
그리고 옛 규약(모두 파이프0.20 부피의 대조군 하나)으로 쟀으면 얼마였나를 나란히."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
from 계획 import _font

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
order = [c["name"] for c in json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]]
rows.sort(key=lambda r: order.index(r["case"]) if r["case"] in order else 999)
n = len(rows)
SHOW = [("파이프0.20", (150, 185, 235)), ("파이프0.50", (40, 90, 190)),
        ("타원0.50", (150, 100, 210)), ("오라클0.20", (150, 215, 170)), ("오라클0.50", (30, 140, 70))]
ALL = ["파이프0.20", "파이프0.50", "타원0.20", "타원0.50", "오라클0.20", "오라클0.50"]
own = lambda r, g, k: r[g][k] - r[g]["균일@" + k]
old = lambda r, g, k: r[g][k] - r[g]["균일층@파이프0.20"]      # 저장소가 써 온 대조군 (한 겹씩 · 파이프0.20 부피)

W_, LW, TOP, RH, X0, X1 = 1300, 330, 150, 26, -0.09, 0.09
PW = W_ - LW - 60
im = Image.new("RGB", (W_, TOP + n * RH + 60 + 30 * (len(ALL) + 3)), "white")
d = ImageDraw.Draw(im)
f1, f2, f3 = _font(26), _font(14), _font(13)
d.text((24, 18), "lam 0.20 vs 0.50 — 실물 %d장 · 대조군은 판본마다 제 부피로" % n, fill=(20, 20, 20), font=f1)
d.text((24, 56), "점 = 그 판본 IoU − 같은 부피의 균일 침식 IoU (hull 을 판본 부피까지 매끈하게 안으로 민 것 · 격자128). "
                 "오른쪽 = 정보를 안 쓰고 같은 양을 깎은 것보다 낫다.", fill=(90, 90, 90), font=f3)
xp = lambda v: LW + (min(max(v, X0), X1) - X0) / (X1 - X0) * PW
for j, (k, c) in enumerate(SHOW):
    x = 24 + j * 240
    d.ellipse([x, 96, x + 12, 108], fill=c)
    d.text((x + 18, 93), k, fill=(40, 40, 40), font=f2)
for t in np.arange(-0.08, 0.081, 0.02):
    x = xp(t)
    d.line([x, TOP - 8, x, TOP + n * RH], fill=(170, 170, 170) if abs(t) < 1e-9 else (232, 232, 232), width=2 if abs(t) < 1e-9 else 1)
    d.text((x - 16, TOP + n * RH + 6), "%+.2f" % t, fill=(120, 120, 120), font=f3)
for i, r in enumerate(rows):
    y = TOP + i * RH + RH // 2
    d.text((24, y - 9), r["case"][:40], fill=(30, 30, 30), font=f3)
    for k, c in SHOW:
        x = xp(own(r, "128", k))
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=c)
y = TOP + n * RH + 40
d.text((24, y), "판본            제 대조군 · 격자128      격자192           옛 규약(파이프0.20 부피 하나) · 128", fill=(20, 20, 20), font=f2)
lines = []
for k in ALL:
    a = [np.array([f(r, g, k) for r in rows]) for f, g in ((own, "128"), (own, "192"), (old, "128"))]
    both = all(v.mean() > 0 and (v > 0).sum() > n / 2 for v in a[:2])
    s = "%-12s  %+.4f (%2d/%d)     %+.4f (%2d/%d)     %+.4f (%2d/%d)   %s" % (
        k, a[0].mean(), (a[0] > 0).sum(), n, a[1].mean(), (a[1] > 0).sum(), n,
        a[2].mean(), (a[2] > 0).sum(), n, "통과" if both else "")
    lines.append(s)
    y += 28
    d.text((24, y), s, fill=(30, 130, 70) if both else (40, 40, 40), font=f2)
vol = {k: np.median([r["부피"][k] for r in rows]) for k in ALL}
y += 34
d.text((24, y), "남은 부피 / hull (중앙)  " + " · ".join("%s %.3f" % (k, vol[k]) for k in ALL), fill=(90, 90, 90), font=f3)
p = os.path.join(HERE, "out", "lam비교.png")
im.save(p)
print("\n".join(lines))
print("부피 " + " · ".join("%s %.3f" % (k, vol[k]) for k in ALL))
print("->", p)
