# -*- coding: utf-8 -*-
"""**점수판을 모양으로** — 옛 기본(파이프 lam0.20) 대 새 기본(타원 lam1.00), 속 채운 정답과 겹쳐 반 자른 3D (2026-09-15).

    python 점수판그림.py [케이스...]   -> out/점수판그림.png  (기본: 가장 오른 셋 · 가장 떨어진 셋)

칸마다 회색 = 원형과 정답이 겹침 · 빨강 = 원형이 넘침 · 보라 = 원형이 모자람. `속채움그림.py` 와 같은 각도 · 같은 색.
"""
import json
import os
import sys

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import 대조 as C
import 오라클 as O
import 정답 as J
from 겉면채점 import fill_slices
from 속채움그림 import OVER, MISS, OVERLAP, S, basis, paint
from 계획 import _font

PROG = os.path.join(HERE, "out", "기록", "점수판_진행.jsonl")


def picks(rows, k=3):
    d = sorted(rows.values(), key=lambda r: r["새"][1] - r["옛"][1])
    return [r["case"] for r in d[::-1][:k]] + [r["case"] for r in d[:k]]


def tiles(c):
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    T, ot = J.grid(truth)
    _, old, axes, _ = O.build(c, truth, H.LAM, "파이프")
    _, new, axes2, _ = C.build(c)
    Go, oo = J.grid(O.C.to_mesh(old, axes))
    Gn, on = J.grid(O.C.to_mesh(new, axes2))
    lo = np.minimum.reduce([ot, oo, on])
    hi = np.maximum.reduce([ot + T.shape, oo + Go.shape, on + Gn.shape])

    def put(g, o):
        a = np.zeros(hi - lo + 2, bool)
        a[tuple(slice(o[i] - lo[i] + 1, o[i] - lo[i] + 1 + g.shape[i]) for i in range(3))] = g
        return a
    F = fill_slices(put(T, ot))
    Bo, Bn = put(Go, oo), put(Gn, on)
    xs = np.nonzero(F.any((1, 2)))[0]
    mid = (xs.min() + xs.max()) // 2
    for m in (F, Bo, Bn):
        m[mid + 1:] = False
    r, u, _ = basis()
    pts = np.argwhere(F | Bo | Bn)
    X, Y = pts @ r, pts @ u
    span = max(X.max() - X.min(), Y.max() - Y.min()) * 1.08
    frame = (((X.max() + X.min()) / 2 - span / 2, (Y.max() + Y.min()) / 2 - span / 2), span)
    draw = lambda B: paint([(B & F, OVERLAP), (B & ~F, OVER), (F & ~B, MISS)], frame)
    return draw(Bo), draw(Bn)


def main(cases):
    rows = {r["case"]: r for r in map(json.loads, open(PROG, encoding="utf-8"))}
    cases = cases or picks(rows)
    G, TOP, LW = 18, 170, 250
    im = Image.new("RGB", (LW + 2 * (S + G) + 30, TOP + len(cases) * (S + G) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 16), "기본값을 바꿨다 — 옛 기본(파이프 lam 0.20) 대 새 기본(타원 lam 1.00)", font=_font(30), fill=(20, 20, 20))
    d.text((24, 62), "속 채운 정답과 겹쳐 반 잘라 비스듬히 밑에서 · 위 셋 = 가장 오른 장 · 아래 셋 = 가장 떨어진 장", font=_font(19), fill=(90, 90, 90))
    x = 24
    for col, name in (((185, 185, 185), "겹침"), ((215, 60, 60), "원형이 넘친 곳"), ((160, 85, 175), "원형이 모자란 곳")):
        d.rectangle([x, 100, x + 18, 118], fill=col)
        d.text((x + 26, 96), name, font=_font(19), fill=(40, 40, 40))
        x += 200
    d.text((LW + S // 2 - 40, TOP - 34), "옛 기본", font=_font(22), fill=(30, 30, 30))
    d.text((LW + S + G + S // 2 - 40, TOP - 34), "새 기본", font=_font(22), fill=(30, 30, 30))
    for i, c in enumerate(cases):
        y = TOP + i * (S + G)
        a, b = tiles(c)
        im.paste(Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB)), (LW, y))
        im.paste(Image.fromarray(cv2.cvtColor(b, cv2.COLOR_BGR2RGB)), (LW + S + G, y))
        r = rows[c]
        dv = r["새"][1] - r["옛"][1]
        d.text((24, y + S // 2 - 40), c[:24], font=_font(18), fill=(30, 30, 30))
        d.text((24, y + S // 2 - 12), "%.3f → %.3f" % (r["옛"][1], r["새"][1]), font=_font(22), fill=(30, 30, 30))
        d.text((24, y + S // 2 + 20), "%+.3f" % dv, font=_font(26), fill=(40, 120, 60) if dv > 0 else (200, 50, 50))
        print("  %s" % c, flush=True)
    p = os.path.join(HERE, "out", "점수판그림.png")
    im.save(p)
    print("  -> %s" % p)


if __name__ == "__main__":
    main(sys.argv[1:])
