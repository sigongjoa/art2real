# -*- coding: utf-8 -*-
"""보충격자 그림 — 개념도 · 빈 자리 · 판본 비교 · 장별 · 흩어진 점 (2026-09-18).

    python 보충격자그림.py 개념      -> out/보충_개념.png
    python 보충격자그림.py 빈자리 [케이스] -> out/보충_빈자리.png
    python 보충격자그림.py 점        -> out/보충_점.png
    python 보충격자그림.py 비교 [케이스...] -> out/보충_비교.png
    python 보충격자그림.py 타일 [n]  -> out/보충타일/<케이스>.png (한 장씩 · 끊겨도 이어서)
    python 보충격자그림.py 모으기     -> out/보충_장별.png
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)

TILE = os.path.join(HERE, "out", "보충타일")
S = 300


# ── ① 개념도 ────────────────────────────────────────────────────────────────

def 개념():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    plt.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    INK, GRAY, RED = "0.15", "0.80", "#c03"

    t = np.linspace(0, 2 * np.pi, 400)
    R = 1.0 + 0.22 * np.sin(3 * t + 0.6) + 0.10 * np.sin(5 * t)
    bx, by = R * np.cos(t), R * np.sin(t)
    gen = (bx > -0.35)                                   # 생성이 만든 쪽 (왼쪽을 통째로 못 만들었다 치자)

    fig, ax = plt.subplots(2, 2, figsize=(11.2, 9.0), dpi=170)

    a = ax[0, 0]
    a.fill(np.where(gen, bx, -0.35), by, color=GRAY, ec="none")
    a.plot(bx, by, ls="--", lw=1.4, color="0.55")
    a.plot([-0.35, -0.35], [-1.2, 1.2], lw=1.4, color=INK)
    a.fill_betweenx(np.linspace(-1.2, 1.2, 50), -1.35, -0.35, color=RED, alpha=0.13)
    a.text(-0.95, 1.28, "빈 자리", color=RED, fontsize=11, ha="center")
    a.text(0.35, -1.45, "생성 메시가 만든 쪽", fontsize=9, ha="center", color="0.3")
    a.set_title("① 빈 자리 — 원화 실루엣 중 생성이 못 덮은 곳\n(점선 = 원화 실루엣)", fontsize=10.5)

    b = ax[0, 1]
    h = 0.25
    edges = np.arange(-1.35, 1.36, h)
    for e in edges:
        b.plot([e, e], [-1.2, 1.2], lw=0.4, color="0.88", zorder=0)
        b.plot([-1.35, 1.35], [e, e], lw=0.4, color="0.88", zorder=0)
    b.fill(np.where(gen, bx, -0.35), by, color=GRAY, ec="none")
    from matplotlib.path import Path
    for i in range(len(edges) - 1):
        for j in range(len(edges) - 1):
            cx, cy = edges[i] + h / 2, edges[j] + h / 2
            if cx < -0.35 and Path(np.stack([bx, by], 1)).contains_point((cx, cy)):
                b.add_patch(Rectangle((edges[i], edges[j]), h, h, fc=RED, alpha=0.30, ec=RED, lw=0.8))
    b.plot(bx, by, ls="--", lw=1.2, color="0.55")
    b.set_title("② 지금 — 빈 자리를 복셀로 메운다\n패치만 격자에 눕는다 → 계단이 되돌아온다", fontsize=10.5)

    c = ax[1, 0]
    c.fill(np.where(gen, bx, -0.35), by, color=GRAY, ec="none")
    keep = bx < -0.35
    c.fill(np.r_[bx[keep], -0.35, -0.35], np.r_[by[keep], by[keep][-1], by[keep][0]], color=RED, alpha=0.30, ec=RED, lw=1.4)
    c.plot(bx, by, ls="--", lw=1.2, color="0.55")
    c.set_title("③ C — 빈 자리를 hull 메시로 메운다\n격자는 없지만 타원 깎기를 못 써 조금 뚱뚱하다", fontsize=10.5)

    d = ax[1, 1]
    d.fill(np.where(gen, bx, -0.35), by, color=GRAY, ec="none")
    zz = by[keep]
    xs = bx[keep]
    front = -0.35 + (xs + 0.35) * (0.55 + 0.35 * np.cos(zz * 2.2))   # hull 안쪽에 든 타원 깊이 높이장
    d.fill(np.r_[front, -0.35, -0.35], np.r_[zz, zz[-1], zz[0]], color=RED, alpha=0.30, ec=RED, lw=1.4)
    d.plot(bx, by, ls="--", lw=1.2, color="0.55")
    d.text(-0.95, -1.45, "높이장 y = f(x, z) · 실수라 계단이 없다", fontsize=9, ha="center", color=RED)
    d.set_title("④ D — 빈 자리를 타원 깊이 높이장으로 메운다\n격자도 없고 단면 가정도 지킨다", fontsize=10.5)

    for a_ in ax.ravel():
        a_.set_xlim(-1.45, 1.45); a_.set_ylim(-1.6, 1.45); a_.set_aspect("equal"); a_.axis("off")
    fig.tight_layout(pad=1.3)
    p = os.path.join(HERE, "out", "보충_개념.png")
    fig.savefig(p, facecolor="white")
    _논문(p, "개념.png")
    print("  ->", p)


# ── ② 빈 자리 (실제 마스크) ─────────────────────────────────────────────────

def 빈자리그림(cases=None):
    import cv2
    import hull as H
    import win as W
    from 계획 import _font
    from 보충격자 import prepare
    H.register_sheets()
    cases = cases or ["avatarsample_g", "hairsample_female"]
    S2 = 300
    im = Image.new("RGB", (30 + 3 * (S2 + 10), 130 + len(cases) * (S2 + 46)), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "빈 자리 — 원화 실루엣 중 불리언 메시가 못 덮은 곳", font=_font(28), fill=(20, 20, 20))
    d.text((24, 56), "회색 = 원화 실루엣 · 검정 = 불리언 메시의 투영 · 빨강 = 빈 자리 (보충이 채워야 하는 곳)",
           font=_font(16), fill=(90, 90, 90))
    for i, v in enumerate(W.VIEWS):
        d.text((30 + i * (S2 + 10) + 8, 96), v, font=_font(18), fill=(30, 30, 30))
    for r, case in enumerate(cases):
        ctx = prepare(case)
        y = 130 + r * (S2 + 46)
        for i, v in enumerate(W.VIEWS):
            m, g = ctx["masks"][v], ctx["gaps"][v]
            rgb = np.full((W.RES, W.RES, 3), 255, np.uint8)
            rgb[m] = (205, 205, 205)
            rgb[m & ~g] = (60, 60, 60)
            rgb[g] = (210, 40, 40)
            t = cv2.resize(rgb, (S2, S2), interpolation=cv2.INTER_AREA)
            im.paste(Image.fromarray(t), (30 + i * (S2 + 10), y))
        d.text((30, y + S2 + 4), "%s · 빈 자리 %s" % (case[:26], " · ".join(
            "%s %.1f%%" % (v, 100 * ctx["gaps"][v].sum() / max(ctx["masks"][v].sum(), 1)) for v in W.VIEWS)),
            font=_font(16), fill=(60, 60, 60))
        print("  빈자리 %s" % case, flush=True)
        del ctx
    p = os.path.join(HERE, "out", "보충_빈자리.png")
    im.save(p)
    _논문(p, "빈자리.png")
    print("  ->", p)


# ── ③ 흩어진 점 ─────────────────────────────────────────────────────────────

def 점():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
    from 보충격자 import rows, VARS
    rs = list(rows().values())
    A, B, C, D, V = VARS
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.6), dpi=170)
    g = lambda n, k: np.array([r[n][k] for r in rs])
    ax[0].scatter(g(A, "거칠기"), g(D, "거칠기"), s=34, color="#1f4e8c")
    lim = [0, max(g(A, "거칠기").max(), 0.45) * 1.05]
    ax[0].plot(lim, lim, ls="--", lw=1, color="0.6")
    ax[0].set_xlabel("A 복셀+보충 (지금)"); ax[0].set_ylabel("D 불리언+높이장보충")
    ax[0].set_title("거칠기 — 모든 장이 대각선 아래", fontsize=11)
    ax[1].scatter(g(A, "iou"), g(D, "iou"), s=34, color="#1f4e8c")
    lo = min(g(A, "iou").min(), g(D, "iou").min()) - 0.02
    ax[1].plot([lo, 0.95], [lo, 0.95], ls="--", lw=1, color="0.6")
    ax[1].set_xlabel("A"); ax[1].set_ylabel("D"); ax[1].set_title("속 채운 정답 IoU — 갈린다", fontsize=11)
    names = ["A", "B", "C", "D", "D→복셀"]
    vals = [np.median(g(n, "거칠기")) for n in VARS]
    ax[2].bar(names, vals, color=["0.6", "#5588bb", "#77aa88", "#1f4e8c", "#c03"])
    for i, v in enumerate(vals):
        ax[2].text(i, v + 0.008, "%.3f" % v, ha="center", fontsize=9)
    ax[2].set_title("거칠기 중앙값 — 대조군(빨강)은 되돌아온다", fontsize=11)
    for a_ in ax[:2]:
        a_.set_aspect("equal"); a_.grid(alpha=0.25)
    fig.tight_layout(pad=1.2)
    p = os.path.join(HERE, "out", "보충_점.png")
    fig.savefig(p, facecolor="white")
    _논문(p, "점.png")
    print("  ->", p)


# ── ④ 판본 비교 (명암) ──────────────────────────────────────────────────────

def 비교(cases=None):
    import 앨리어싱 as AL
    import hull as H
    from 계획 import _font
    from 폴리싱 import shaded
    from 보충격자 import prepare, make, VARS
    H.register_sheets()
    cases = cases or ["sendagaya_shino", "avatarsample_g"]
    cols = ("A 복셀+보충 (지금)", "B 불리언+복셀보충", "C 불리언+hull보충", "D 불리언+높이장보충", "D→복셀 (대조군)")
    S2 = 360
    im = Image.new("RGB", (30 + len(cols) * (S2 + 8), 140 + len(cases) * (S2 + 44)), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "보충까지 격자를 없애면 — 같은 장, 같은 틀, 면 법선 명암", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "A 는 ∩hull 도 보충도 복셀 · B 는 ∩hull 만 메시 · C · D 는 보충까지 메시 · D→복셀은 D 를 다시 구운 대조군",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "숫자 = 거칠기 (격자 한 칸 거리에서 법선이 30° 넘게 꺾인 이웃 쌍의 비율)", font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        d.text((30 + i * (S2 + 8) + 6, 110), n, font=_font(17), fill=(30, 30, 30))
    from 보충격자 import rows
    rs = rows()
    for r, case in enumerate(cases):
        ctx = prepare(case)
        y = 140 + r * (S2 + 44)
        dmesh, fr = None, None
        for i, n in enumerate(VARS):
            m = make(ctx, n, cache=dmesh)
            if fr is None:
                fr = AL.frame_of(m, 45)
            t = shaded(m, 45, fr, S2)
            im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t), (30 + i * (S2 + 8), y))
            v = rs.get(case, {}).get(n, {}).get("거칠기")
            d.text((30 + i * (S2 + 8) + 4, y + S2 + 4),
                   ("%s · %.3f" % (case[:16], v)) if v is not None else case[:16], font=_font(16), fill=(60, 60, 60))
            if n.startswith("D 불리언"):
                dmesh = m
            print("  비교 %s %s" % (case, n), flush=True)
        del ctx, dmesh
    p = os.path.join(HERE, "out", "보충_비교.png")
    im.save(p)
    _논문(p, "비교.png")
    print("  ->", p)


# ── ⑤ 장별 타일 ─────────────────────────────────────────────────────────────

def 타일(n=2):
    import 앨리어싱 as AL
    import hull as H
    from 폴리싱 import shaded
    from 보충격자 import prepare, make, rows
    os.makedirs(TILE, exist_ok=True)
    H.register_sheets()
    todo = [c for c in rows() if not os.path.exists(os.path.join(TILE, "%s.png" % c))][:n]
    for c in todo:
        ctx = prepare(c)
        a = make(ctx, "A 복셀+보충")
        dd = make(ctx, "D 불리언+높이장보충")
        fr = AL.frame_of(a, 45)
        im = Image.new("RGB", (2 * S + 6, S), "white")
        for j, m in enumerate((a, dd)):
            t = shaded(m, 45, fr, S)
            im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t), (j * (S + 6), 0))
        im.save(os.path.join(TILE, "%s.png" % c))
        print("  타일 %s" % c, flush=True)
        del ctx, a, dd


def 모으기():
    from 계획 import _font
    from 보충격자 import rows
    rs = rows()
    cs = [c for c in rs if os.path.exists(os.path.join(TILE, "%s.png" % c))]
    cs.sort(key=lambda c: -(rs[c]["A 복셀+보충"]["거칠기"] - rs[c]["D 불리언+높이장보충"]["거칠기"]))
    COLS, TOP = 3, 140
    im = Image.new("RGB", (30 + COLS * (2 * S + 6 + 16), TOP + ((len(cs) + COLS - 1) // COLS) * (S + 52) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "지금(왼) 대 보충까지 격자 없이(오른) — %d장" % len(cs), font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "왼쪽 A = ∩hull 도 보충도 복셀 · 오른쪽 D = 둘 다 메시 (기둥 불리언 + 타원 깊이 높이장)",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "숫자 = 거칠기 · IoU (속 채운 정답 · 격자 128) · 거칠기가 많이 준 장부터",
           font=_font(17), fill=(90, 90, 90))
    for i, c in enumerate(cs):
        r, q = divmod(i, COLS)
        x, y = 30 + q * (2 * S + 6 + 16), TOP + r * (S + 52)
        im.paste(Image.open(os.path.join(TILE, "%s.png" % c)), (x, y))
        d.text((x + 2, y + S + 2), c[:38], font=_font(15), fill=(40, 40, 40))
        d.text((x + 2, y + S + 22), "거칠기 %.3f → %.3f      IoU %.3f → %.3f"
               % (rs[c]["A 복셀+보충"]["거칠기"], rs[c]["D 불리언+높이장보충"]["거칠기"],
                  rs[c]["A 복셀+보충"]["iou"], rs[c]["D 불리언+높이장보충"]["iou"]), font=_font(15), fill=(110, 110, 110))
    p = os.path.join(HERE, "out", "보충_장별.png")
    im.save(p)
    _논문(p, "장별.png")
    print("  -> %s (%d장)" % (p, len(cs)))


def _논문(src, name):
    import shutil
    d = os.path.join(HERE, "논문", "보충격자", "그림")
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(src, os.path.join(d, name))


def main(args=None):
    a = (args or sys.argv[1:]) or ["개념"]
    cmd, rest = a[0], a[1:]
    {"개념": lambda: 개념(), "빈자리": lambda: 빈자리그림(rest or None), "점": lambda: 점(),
     "비교": lambda: 비교(rest or None), "타일": lambda: 타일(int(rest[0]) if rest else 2),
     "모으기": lambda: 모으기()}[cmd]()


if __name__ == "__main__":
    main()
