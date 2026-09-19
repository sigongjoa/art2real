# -*- coding: utf-8 -*-
"""보충경계 그림 — **반 칸이 눈에 보이는 한 장** · 장별 막대.

    python 보충경계그림.py 반칸 [케이스]   -> out/보충경계_반칸.png
    python 보충경계그림.py 장별            -> out/보충경계_장별.png
"""
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918", "실험_20260919"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 보충격자 as BG
import 보충경계 as BD
from 불리언 import gen_manifold, to_trimesh

for f in ("Malgun Gothic", "맑은 고딕", "NanumGothic"):
    if any(f == x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.join(HERE, "out")


def 투영(man):
    t = to_trimesh(man)
    return np.asarray(W.silhouette(np.asarray(t.vertices), np.asarray(t.faces), "front")).astype(bool), t


def 반칸(case="knight_Warrior_Z6ZUtm6kc1"):
    import manifold3d as m3
    H.register_sheets()
    ctx = BG.prepare(case)
    masks, bs, gaps = ctx["masks"], ctx["bs"], ctx["gaps"]
    gp, hull = ctx["gp"], ctx["hull"]
    patD = m3.Manifold.batch_boolean([ctx["hf"], gp], m3.OpType.Intersect)
    hf2, _ = BD.기본_높이장2(masks, bs)
    patD2 = m3.Manifold.batch_boolean([gen_manifold(hf2), hull, gp], m3.OpType.Intersect)
    sD, mD = 투영(patD)
    sD2, mD2 = 투영(patD2)
    sil, gapf = masks["front"], gaps["front"]

    # 빈 자리가 제일 몰린 자리를 잘라 본다
    ker = np.ones((64, 64), np.float32) / (64 * 64)
    heat = cv2.filter2D(gapf.astype(np.float32), -1, ker)
    cy, cx = np.unravel_index(int(np.argmax(heat)), heat.shape)
    r = 96
    y0, x0 = max(cy - r, 0), max(cx - r, 0)
    sl = (slice(y0, y0 + 2 * r), slice(x0, x0 + 2 * r))

    fig, axs = plt.subplots(1, 3, figsize=(13.6, 5.4), gridspec_kw={"width_ratios": (1, 1, 1.15)})
    for ax, (t, m) in zip(axs[:2], (("D 높이장 보충 — 반 칸 안쪽", sD), ("D′ 보충경계 — 1024 윤곽까지", sD2))):
        img = np.zeros((2 * r, 2 * r, 3), np.float32) + 1.0
        s, g, p = sil[sl], gapf[sl], m[sl]
        img[s] = (0.86, 0.86, 0.88)                       # 원화 실루엣
        img[g] = (0.95, 0.45, 0.42)                       # 빈 자리 (생성이 못 덮은 곳)
        img[g & p] = (0.30, 0.55, 0.85)                   # 보충이 덮은 빈 자리
        ax.imshow(img, interpolation="nearest")
        c = float((g & p).sum() / max(g.sum(), 1))
        ax.set_title("%s\n이 자리 빈 자리 덮음 %.3f" % (t, c), fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
    # 격자 한 칸(4 화소) 눈금 — 반 칸이 무엇인지 눈으로
    for x in range(0, 2 * r, 4 * 8):
        axs[0].axvline(x, color="k", lw=0.25, alpha=0.25)
        axs[0].axhline(x, color="k", lw=0.25, alpha=0.25)

    # 가로 단면 (z 고정) — y 방향 반 칸까지 보인다
    z = W.Z1 - (cy + 0.5) * (W.Z1 - W.Z0) / W.RES
    ax = axs[2]
    xs = []
    # hull 을 굵게 **뒤에** 깐다 — 가는 선 위에 굵은 선을 얹으면 선폭만큼 밖으로 삐져나와 보인다
    for t, mm, col, lw in (("hull (1024 윤곽)", to_trimesh(hull), "0.78", 3.2),
                           ("D 높이장 패치", mD, "#2f6fb5", 1.3),
                           ("D′ 보충경계 패치", mD2, "#d4553f", 1.3)):
        try:
            sec = mm.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        except Exception:
            sec = None
        if sec is None:
            continue
        # **`entities` 를 그대로 이으면 안 된다** — 고리가 안 닫혀 직선 현이 생기고, 그림에서 패치가
        # hull 밖으로 나간 것처럼 보인다. 실제 포함은 불리언으로 확인했다 (D′ 패치 − hull 부피 = 0).
        for q in sec.discrete:
            q = np.vstack([q, q[:1]])
            ax.plot(q[:, 0], q[:, 1], color=col, lw=lw, label=t)
            xs.extend(q[:, 0].tolist())
            t = "_"
    ax.set_aspect("equal")
    if xs:                                                        # 실제로 그린 단면만 보고 확대한다
        x0 = min(xs)
        ax.set_xlim(x0 - 0.008, x0 + 0.075)
    ax.set_title("z = %.3f 가로 단면 확대 (x 가로 · y 깊이) · 격자 한 칸 %.4f\nhull 밖으로 샌 패치 부피: D 1.7%% · D′ 0%%"
                 % (z, (W.U1 - W.U0) / H.N), fontsize=10)
    ax.legend(fontsize=7.5, loc="best")
    ax.tick_params(labelsize=7)
    fig.suptitle("%s — 보충 패치의 반 칸. 높이장은 256² 칸 중심에서, 빈 자리 기둥은 1024² 윤곽에서 온다" % case,
                 fontsize=11, y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    p = os.path.join(OUT, "보충경계_반칸.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    print("  ->", p)


def 장별():
    rs, y = BD.rows(), BD.어제()
    cs = [c for c in BD.경계집합() if c in rs]
    cs.sort(key=lambda c: y[c]["D 불리언+높이장보충"]["못덮음"] - rs[c]["D′ 보충경계"]["못덮음"], reverse=True)
    x = np.arange(len(cs))
    fig, axs = plt.subplots(2, 1, figsize=(12.5, 7.6))
    w = 0.27
    for i, (n, lab, col) in enumerate((("A 복셀+보충", "A 현행", "0.62"),
                                       ("D 불리언+높이장보충", "D 09-18", "#2f6fb5"))):
        axs[0].bar(x + (i - 1) * w, [y[c][n]["못덮음"] for c in cs], w, label=lab, color=col)
    axs[0].bar(x + w, [rs[c]["D′ 보충경계"]["못덮음"] for c in cs], w, label="D′ 보충경계", color="#d4553f")
    axs[0].set_ylabel("못덮음 (낮을수록 좋다)")
    axs[0].set_title("반 칸을 없애면 못덮음이 A 아래로 돌아온다 (%d장 · 개선 큰 순)" % len(cs))
    for i, (n, lab, col) in enumerate((("B 불리언+복셀보충", "B 09-18", "0.62"),)):
        axs[1].bar(x - w / 2, [y[c][n]["거칠기"] for c in cs], w, label=lab, color=col)
    axs[1].bar(x + w / 2, [rs[c]["D′ 보충경계"]["거칠기"] for c in cs], w, label="D′ 보충경계", color="#d4553f")
    axs[1].plot(x, [rs[c]["D′→복셀"]["거칠기"] for c in cs], "k.", ms=5, label="D′→복셀 (해상도 대조군)")
    axs[1].set_ylabel("거칠기 (낮을수록 매끄럽다)")
    axs[1].set_title("거칠기는 B 아래를 지킨다 · 같은 결과를 256 격자에 다시 구우면 복귀한다")
    for ax in axs:
        ax.set_xticks(x)
        ax.set_xticklabels([c[:22] for c in cs], rotation=38, ha="right", fontsize=7)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    p = os.path.join(OUT, "보충경계_장별.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    print("  ->", p)


def main(args=None):
    a = args or sys.argv[1:] or ["반칸"]
    if a[0] == "반칸":
        반칸(*(a[1:2] or []))
    elif a[0] == "장별":
        장별()
    else:
        반칸()
        장별()


if __name__ == "__main__":
    main()
