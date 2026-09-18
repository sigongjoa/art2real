# -*- coding: utf-8 -*-
"""방법 그림 — 복셀 길과 불리언 길, 그리고 두 척도를 단면 한 장으로 (2026-09-18).

    python 방법그림.py   -> out/방법.png · 논문/표면계단/그림/방법.png

논문에 말만 있고 그림이 없어 안 읽힌다는 지적(사용자 09-18)에 따라 만든다. 실제 데이터가 아니라 **개념 단면**이다.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

HERE = r"G:\art2real\원화3d"
OUT = os.path.join(HERE, "out", "방법.png")
plt.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
GRAY, INK, CUT = "0.78", "0.15", "0.35"


def blob(n=400):
    """부드러운 닫힌 곡선 하나 — 「생성 메시의 단면」."""
    t = np.linspace(0, 2 * np.pi, n)
    r = 1.0 + 0.22 * np.sin(3 * t + 0.6) + 0.10 * np.sin(5 * t)
    return r * np.cos(t), r * np.sin(t)


def inside(px, py, bx, by):
    from matplotlib.path import Path
    return Path(np.stack([bx, by], 1)).contains_points(np.stack([px, py], 1))


def panel_voxel(ax):
    bx, by = blob()
    h, lim = 0.25, 1.5
    edges = np.arange(-lim, lim + h, h)
    cx = edges[:-1] + h / 2
    X, Y = np.meshgrid(cx, cx)
    on = inside(X.ravel(), Y.ravel(), bx, by).reshape(X.shape)
    for i in range(len(cx)):
        for j in range(len(cx)):
            if on[j, i]:
                ax.add_patch(Rectangle((edges[i], edges[j]), h, h, fc=GRAY, ec="none"))
    for e in edges:
        ax.plot([e, e], [-lim, lim], lw=0.4, color="0.85", zorder=0)
        ax.plot([-lim, lim], [e, e], lw=0.4, color="0.85", zorder=0)
    # 계단 경계 — 켜진 칸의 테두리
    for i in range(len(cx)):
        for j in range(len(cx)):
            if not on[j, i]:
                continue
            for di, dj, seg in ((1, 0, "v"), (-1, 0, "v"), (0, 1, "h"), (0, -1, "h")):
                ii, jj = i + di, j + dj
                if 0 <= ii < len(cx) and 0 <= jj < len(cx) and on[jj, ii]:
                    continue
                x0, y0 = edges[i], edges[j]
                if seg == "v":
                    x = x0 + (h if di > 0 else 0)
                    ax.plot([x, x], [y0, y0 + h], lw=2.4, color=INK, solid_capstyle="butt")
                else:
                    y = y0 + (h if dj > 0 else 0)
                    ax.plot([x0, x0 + h], [y, y], lw=2.4, color=INK, solid_capstyle="butt")
    ax.plot(bx, by, ls="--", lw=1.6, color="0.45")
    ax.set_title("① 복셀 길 (지금)\n생성 메시를 격자에 다시 굽는다 → 경계가 격자에 눕는다", fontsize=10.5)
    ax.text(0, -1.42, "굵은 선 = 우리가 내보내는 면 · 점선 = 원래 생성 메시",
            ha="center", fontsize=8.6, color="0.35")
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal"); ax.axis("off")


def panel_bool(ax):
    bx, by = blob()
    lim = 1.5
    x0, x1 = -0.95, 1.02                      # 정면 실루엣이 주는 좌우 자름
    y0, y1 = -0.90, 0.98                      # 측면 실루엣이 주는 앞뒤 자름
    keep = (bx > x0) & (bx < x1) & (by > y0) & (by < y1)
    ax.fill(np.clip(bx, x0, x1), np.clip(by, y0, y1), color=GRAY, ec="none")
    for v in (x0, x1):
        ax.plot([v, v], [-lim, lim], lw=1.2, color=CUT, ls="-")
    for v in (y0, y1):
        ax.plot([-lim, lim], [v, v], lw=1.2, color=CUT, ls="-")
    b = np.stack([np.clip(bx, x0, x1), np.clip(by, y0, y1)], 1)
    ax.plot(np.r_[b[:, 0], b[0, 0]], np.r_[b[:, 1], b[0, 1]], lw=2.4, color=INK)
    ax.plot(bx, by, ls="--", lw=1.2, color="0.6")
    for xx, yy, s in ((x1, 1.3, "정면 실루엣"), (-1.42, y1, "측면 실루엣")):
        ax.text(xx + 0.04, yy, s, fontsize=8.4, color=CUT, va="bottom")
    ax.set_title("② 불리언 길 (제안)\n실루엣을 밀어 세운 기둥과 바로 교집합 → 격자를 안 거친다", fontsize=10.5)
    ax.text(0, -1.42, "잘린 자리만 평면이고 나머지는 생성 메시의 면 그대로",
            ha="center", fontsize=8.6, color="0.35")
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal"); ax.axis("off")


def _profile(stair, n=9, h=0.34):
    """계단 단면 또는 같은 자리를 지나는 매끈한 단면 -> 꺾인 점들."""
    if stair:
        pts = []
        for i in range(n):
            pts += [(i * h, i * h * 0.55), ((i + 1) * h, i * h * 0.55)]
        return np.array(pts)
    t = np.linspace(0, n * h, 120)
    return np.stack([t, t * 0.55], 1)


def panel_rough(ax):
    r = 0.30
    for k, (stair, lbl, dx) in enumerate(((True, "계단 면", 0.0), (False, "매끈한 면", 3.4))):
        p = _profile(stair)
        ax.plot(p[:, 0] + dx, p[:, 1], lw=2.2, color=INK)
        # 표본점과 법선
        idx = np.linspace(0, len(p) - 2, 14).astype(int)
        for i in idx:
            a, b = p[i], p[i + 1]
            m = (a + b) / 2
            d = b - a
            nn = np.array([-d[1], d[0]])
            L = np.linalg.norm(nn)
            if L < 1e-9:
                continue
            nn = nn / L * 0.22
            ax.plot([m[0] + dx], [m[1]], "o", ms=2.6, color="0.25")
            ax.arrow(m[0] + dx, m[1], nn[0], nn[1], head_width=0.055, color="0.45", lw=0.8)
        c = p[len(p) // 2] + np.array([dx, 0])
        ax.add_patch(Circle(c, r, fc="none", ec="#c03", lw=1.4, ls="--"))
        ax.text(c[0] + 0.05, c[1] + 0.62, "반지름 r", fontsize=8.6, color="#c03", ha="center")
        ax.text(p[:, 0].mean() + dx, p[:, 1].max() + 0.55, lbl, fontsize=9.6, ha="center")
    ax.text(1.5, -0.75, "거칠기 큼", fontsize=9.6, ha="center", color="#c03")
    ax.text(4.9, -0.75, "거칠기 ≈ 0", fontsize=9.6, ha="center", color="#c03")
    ax.text(3.2, -1.25, "r(= 격자 한 칸) 안의 이웃 쌍 중 법선이 30° 넘게 꺾인 비율 = 거칠기",
            fontsize=9, ha="center")
    ax.set_title("③ 거칠기 — 삼각형 개수와 무관한 자", fontsize=10.5)
    ax.set_xlim(-0.5, 6.9); ax.set_ylim(-1.6, 2.6); ax.set_aspect("equal"); ax.axis("off")


def panel_bad(ax):
    p = _profile(True, n=6, h=0.45)
    for k, (dx, sub, lbl, val) in enumerate(((0.0, 1, "삼각형이 성길 때", "계단 몫 0.236"),
                                             (3.6, 4, "잘게 쪼갠 뒤 (모양은 그대로)", "계단 몫 0.059"))):
        ax.plot(p[:, 0] + dx, p[:, 1], lw=2.2, color=INK)
        for i in range(len(p) - 1):
            a, b = p[i] + np.array([dx, 0]), p[i + 1] + np.array([dx, 0])
            for t in np.linspace(0, 1, sub + 1):
                q = a + (b - a) * t
                ax.plot([q[0]], [q[1]], "|", ms=9, color="0.45", mew=1.0)
        ax.text(p[:, 0].mean() + dx, p[:, 1].max() + 0.45, lbl, fontsize=9.4, ha="center")
        ax.text(p[:, 0].mean() + dx, -0.75, val, fontsize=9.6, ha="center", color="#c03")
    ax.text(3.0, -1.35, "같은 기하인데 값이 4배 달라진다 — 이웃각 분포는 판본 비교에 쓸 수 없다",
            fontsize=9, ha="center")
    ax.set_title("④ 왜 첫 자를 버렸나", fontsize=10.5)
    ax.set_xlim(-0.4, 6.6); ax.set_ylim(-1.7, 2.4); ax.set_aspect("equal"); ax.axis("off")


def main():
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 9.4), dpi=170)
    panel_voxel(axes[0, 0]); panel_bool(axes[0, 1])
    panel_rough(axes[1, 0]); panel_bad(axes[1, 1])
    fig.tight_layout(pad=1.4)
    fig.savefig(OUT, facecolor="white")
    d = os.path.join(HERE, "논문", "표면계단", "그림")
    os.makedirs(d, exist_ok=True)
    fig.savefig(os.path.join(d, "방법.png"), facecolor="white")
    print("  -> %s" % OUT)


if __name__ == "__main__":
    main()
