# -*- coding: utf-8 -*-
"""층 분해 그림 — 판본을 같은 각도 · 같은 틀로 나란히, 그리고 층 색칠 한 장 (2026-09-18).

    python 층분해.py 그림      -> out/층분해.png · out/층분해_층.png
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
for d in ("실험_20260913", "실험_20260915", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import 대조 as C
import 정답 as J
import 속채움그림 as SC
from 계획 import _font
from 점수판그림 import FRONT_VIEW, SHAPE
from 층분해 import LAYERS, build, rows, truth_layers

ROWS = ["avatarsample_d_darkness", "avatarsample_g", "sendagaya_shino", "base_male"]
COLS = ("정답 (속 채움)", "지금 기본", "층기본", "균일기본@층기본", "층기본보임", "무작위층기본")
COLOR = {"인체": (150, 175, 205), "천": (205, 165, 150), "머리": (150, 200, 165)}


def _full(grids):
    lo = np.minimum.reduce([o for _, o in grids])
    hi = np.maximum.reduce([o + np.asarray(g.shape) for g, o in grids])
    out = []
    for g, o in grids:
        a = np.zeros(hi - lo + 2, g.dtype)
        a[tuple(slice(o[i] - lo[i] + 1, o[i] - lo[i] + 1 + g.shape[i]) for i in range(3))] = g
        out.append(a)
    return out


def _frame(arrs):
    r_, u_, _ = SC.basis()
    pts = np.argwhere(np.logical_or.reduce([a > 0 for a in arrs]))
    X, Y = pts @ r_, pts @ u_
    span = max(np.ptp(X), np.ptp(Y)) * 1.06
    return (((X.max() + X.min()) / 2 - span / 2, (Y.max() + Y.min()) / 2 - span / 2), span)


def main():
    SC.VIEW = FRONT_VIEW
    rs = rows()
    S, Gp, TOP, LW = SC.S, 14, 150, 230
    im = Image.new("RGB", (LW + len(COLS) * (S + Gp) + 20, TOP + len(ROWS) * (S + Gp) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "층을 갈라 따로 세워도, 기본을 같은 부피로 민 것을 못 이긴다", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "층기본 = 인체 · 천 · 머리 층마다 따로 hull 을 세워 깎고 합친 것 (층 마스크는 정답 재질에서 뽑은 오라클)",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "균일기본@층기본 = 지금 기본을 층기본과 같은 부피까지 매끈하게 민 대조군 (검토가 짚은 대조군) · 층기본보임 = 가린 자리를 안 메운 경우 · 무작위층기본 = 의미 없이 셋으로 가른 것",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 106), "같은 각도 · 같은 틀 · 자르지 않음 · 숫자 = 속 채운 정답 IoU (격자 128)", font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(COLS):
        d.text((LW + i * (S + Gp) + 10, TOP - 30), n, font=_font(19), fill=(30, 30, 30))

    for rr, case in enumerate(ROWS):
        y = TOP + rr * (S + Gp)
        vox, axes, _ = build(case)
        Fl, _, ot, _ = truth_layers(case, J.PITCH)
        import hull as H
        keys = ("기본", "층기본")
        meshes = [C.to_mesh(vox[k], axes) for k in keys]
        ev = H.even_control(vox["기본"], axes, abs(C.to_mesh(vox["층기본"], axes).volume))[0]
        grids = ([(Fl, ot)] + [J.grid(m) for m in meshes] + [J.grid(ev)]
                 + [J.grid(C.to_mesh(vox[k], axes)) for k in ("층기본보임", "무작위층기본#0")])
        full = _full(grids)
        fr = _frame(full)
        d.text((24, y + S // 2 - 20), case[:22], font=_font(17), fill=(30, 30, 30))
        r = rs.get(case, {}).get("iou", {})
        lab = [""] + ["%.3f" % r[k]["128"] if k in r else "" for k in ("기본", "층기본", "균일기본@층기본", "층기본보임", "무작위층기본")]
        for i, a in enumerate(full):
            t = SC.paint([(a > 0, SHAPE)], fr)
            x = LW + i * (S + Gp)
            im.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (x, y))
            if lab[i]:
                d.text((x + 8, y + S - 26), lab[i], font=_font(18), fill=(40, 40, 40))
        print("  %s 그림" % case, flush=True)
    p = os.path.join(HERE, "out", "층분해.png")
    im.save(p)
    print("  -> %s" % p)

    # 층 색칠 — 층이 무엇인지 한 장
    im2 = Image.new("RGB", (20 + len(ROWS) * (S + Gp), 120 + S + 20), "white")
    d2 = ImageDraw.Draw(im2)
    d2.text((20, 14), "층 라벨 (정답 재질) — 인체 · 천 · 머리", font=_font(28), fill=(20, 20, 20))
    d2.text((20, 56), "  ".join("■ %s" % L for L in LAYERS), font=_font(20), fill=(70, 70, 70))
    for i, L in enumerate(LAYERS):
        d2.rectangle([20 + i * 150, 84, 40 + i * 150, 104], fill=COLOR[L])
        d2.text((46 + i * 150, 84), L, font=_font(18), fill=(40, 40, 40))
    for rr, case in enumerate(ROWS):
        Fl, lab, ot, _ = truth_layers(case, J.PITCH)
        gs = _full([((lab * Fl).astype(np.int8), ot)])
        a = gs[0]
        fr = _frame([a])
        t = SC.paint([((a == i + 1), COLOR[L]) for i, L in enumerate(LAYERS)], fr)
        im2.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (20 + rr * (S + Gp), 120))
    p2 = os.path.join(HERE, "out", "층분해_층.png")
    im2.save(p2)
    print("  -> %s" % p2)


if __name__ == "__main__":
    main()
