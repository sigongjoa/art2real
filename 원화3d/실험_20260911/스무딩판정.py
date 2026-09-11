# -*- coding: utf-8 -*-
"""벤치smooth.jsonl -> 판정표 + 그림 (out/스무딩판정.png).

    python 스무딩판정.py <벤치smooth.jsonl> [<벤치lam4.jsonl>]

통과 = 격자 128·192 둘 다 「같은 σ 제 부피 대조군」을 평균으로 이기고 과반 승 (돌리기 전 기준).
옆 칸: 찢김(위아래 >3칸) · 조각(50칸↑) · 실루엣 손실 — 중앙값. lam4 를 주면 σ0 이 재현되나 본다."""
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
rows.sort(key=lambda r: order.index(r["case"]))
n = len(rows)
KS = ["파이프0.20", "파이프0.50", "타원0.50", "오라클0.50"]
SIG = (0, 2)
own = lambda r, g, k, s: r[g]["%sσ%d" % (k, s)] - r[g]["균일@%sσ%d" % (k, s)]

# σ0 재현 점검
if len(sys.argv) > 2:
    L = {json.loads(l)["case"]: json.loads(l) for l in open(sys.argv[2], encoding="utf-8")}
    dv = [abs(r[g]["%sσ0" % k] - L[r["case"]][g][k]) for r in rows for g in ("128", "192") for k in KS]
    dc = [abs(r[g]["균일@%sσ0" % k] - L[r["case"]][g]["균일@" + k]) for r in rows for g in ("128", "192") for k in KS]
    print("  σ0 재현 (lam4 대비)  판본 최대차 %.5f · 대조군 최대차 %.5f" % (max(dv), max(dc)))

med = lambda key, name: float(np.median([r[key][name] for r in rows]))
lines = []
for k in KS:
    for s in SIG:
        a = [np.array([own(r, g, k, s) for r in rows]) for g in ("128", "192")]
        ok = all(v.mean() > 0 and (v > 0).sum() > n / 2 for v in a)
        name = "%sσ%d" % (k, s)
        lines.append((name, a, ok, med("찢김", name), med("조각", name), med("실루엣", name),
                      med("찢김", "균일@" + name), med("조각", "균일@" + name)))
for s in SIG:
    lines.append(("이진σ%d" % s, None, None, med("찢김", "이진σ%d" % s), med("조각", "이진σ%d" % s),
                  med("실루엣", "이진σ%d" % s), None, None))
print("  %d 장" % n)
for name, a, ok, t, p, sl, tc, pc in lines:
    if a is None:
        print("  %-14s %34s  찢김 %4.1f%% · 조각 %.0f · 실루엣 손실 %.2f%%" % (name, "", 100 * t, p, 100 * sl))
        continue
    print("  %-14s %+.4f (%2d/%d)  %+.4f (%2d/%d)  %-4s  찢김 %4.1f%% · 조각 %.0f · 실루엣 손실 %.2f%%  | 대조 찢김 %.1f%% 조각 %.0f"
          % (name, a[0].mean(), (a[0] > 0).sum(), n, a[1].mean(), (a[1] > 0).sum(), n, "통과" if ok else "",
             100 * t, p, 100 * sl, 100 * tc, pc))

# 그림 — 위 표, 아래 케이스별 점 (σ0 옅게 · σ2 진하게)
SHOW = [("파이프0.20", (150, 185, 235), (40, 90, 190)), ("타원0.50", (205, 180, 235), (130, 80, 200)),
        ("오라클0.50", (160, 220, 180), (30, 140, 70))]
W_, LW, RH, X0, X1 = 1320, 330, 24, -0.10, 0.10
TOPT = 110 + 30 * len(lines) + 70
PW = W_ - LW - 60
im = Image.new("RGB", (W_, TOPT + n * RH + 60), "white")
d = ImageDraw.Draw(im)
f1, f2, f3 = _font(26), _font(14), _font(13)
d.text((24, 16), "스무딩 σ0 vs σ2 — 실물 %d장 · 대조군도 같은 σ" % n, fill=(20, 20, 20), font=f1)
d.text((24, 54), "통과 = 격자 128·192 둘 다 같은 σ · 제 부피 대조군을 평균으로 이기고 과반 승. "
                 "찢김 = 위아래 >3칸 · 조각 = 50칸↑ · 실루엣 손실 = hull 정면·측면 중 잃은 몫 (중앙값)", fill=(90, 90, 90), font=f3)
xs = [24, 190, 360, 530, 610, 760, 880, 1040]
for x, t in zip(xs, ["판본", "격자128", "격자192", "판정", "찢김", "조각", "실루엣 손실", "대조군 찢김·조각"]):
    d.text((x, 84), t, fill=(20, 20, 20), font=f2)
for i, (name, a, ok, t, p, sl, tc, pc) in enumerate(lines):
    y = 110 + i * 30
    col = (40, 40, 40) if a is None else (30, 130, 70) if ok else (190, 60, 40)
    cells = [name] + (["", "", ""] if a is None else ["%+.4f (%2d/%d)" % (v.mean(), (v > 0).sum(), n) for v in a]
                      + ["통과" if ok else "짐"]) + ["%.1f%%" % (100 * t), "%.0f" % p, "%.2f%%" % (100 * sl),
                      "" if tc is None else "%.1f%% · %.0f" % (100 * tc, pc)]
    for x, c in zip(xs, cells):
        d.text((x, y), c, fill=col if x in (24, 530) else (40, 40, 40), font=f2)
xp = lambda v: LW + (min(max(v, X0), X1) - X0) / (X1 - X0) * PW
for j, (k, c0, c2) in enumerate(SHOW):
    x = 24 + j * 330
    d.ellipse([x, TOPT - 44, x + 11, TOPT - 33], fill=c0)
    d.ellipse([x + 16, TOPT - 44, x + 27, TOPT - 33], fill=c2)
    d.text((x + 34, TOPT - 47), "%s  σ0 → σ2" % k, fill=(40, 40, 40), font=f2)
for t in np.arange(-0.10, 0.101, 0.02):
    x = xp(t)
    d.line([x, TOPT - 8, x, TOPT + n * RH], fill=(160, 160, 160) if abs(t) < 1e-9 else (234, 234, 234),
           width=2 if abs(t) < 1e-9 else 1)
    d.text((x - 16, TOPT + n * RH + 6), "%+.2f" % t, fill=(120, 120, 120), font=f3)
for i, r in enumerate(rows):
    y = TOPT + i * RH + RH // 2
    d.text((24, y - 9), r["case"][:40], fill=(30, 30, 30), font=f3)
    for k, c0, c2 in SHOW:
        a0, a2 = xp(own(r, "128", k, 0)), xp(own(r, "128", k, 2))
        d.line([a0, y, a2, y], fill=c0, width=2)
        d.ellipse([a0 - 4, y - 4, a0 + 4, y + 4], fill=c0)
        d.ellipse([a2 - 5, y - 5, a2 + 5, y + 5], fill=c2)
p = os.path.join(HERE, "out", "스무딩판정.png")
im.save(p)
print("  ->", p)
