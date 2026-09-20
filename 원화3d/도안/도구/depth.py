"""분할 결과에서 **깊이 맵과 법선 맵**을 만든다 (crease 팽창, Ink-and-Ray 계열).

음영에서 법선을 역산하는 길은 닫혀 있다(셀 채색에 단일 광원 최소제곱 R²=0.12).
대신 **선화를 접힘으로 읽고 부풀린다.** 하드서피스는 판이 평평하므로,
전체 팽창에 **판마다 평면을 최소제곱으로 맞춰 갈아끼우고** 경계에만 좁은 골을 판다.

    py -3.11 depth.py <art3d출력폴더> [--depth-over-width 1.0] [--bevel 3] [--groove 0.03]

내보내는 것: depth.png · normal.png · shade.png · depth.npy · depth.json
지표: **판 안쪽 법선 각도 표준편차** (10도 이하 평면 / 30도 이상 물집).
"""
import argparse
import json
import pathlib
from collections import deque

import numpy as np
from PIL import Image, ImageFilter


def edt(mask):
    d = np.where(mask, 1e9, 0.0)
    H, W = d.shape
    for i in range(H):
        up = d[i - 1] if i else None
        for j in range(W):
            if d[i, j] == 0:
                continue
            v = d[i, j]
            if j: v = min(v, d[i, j - 1] + 1)
            if up is not None:
                v = min(v, up[j] + 1)
                if j: v = min(v, up[j - 1] + 1.41421)
                if j + 1 < W: v = min(v, up[j + 1] + 1.41421)
            d[i, j] = v
    for i in range(H - 1, -1, -1):
        dn = d[i + 1] if i + 1 < H else None
        for j in range(W - 1, -1, -1):
            if d[i, j] == 0:
                continue
            v = d[i, j]
            if j + 1 < W: v = min(v, d[i, j + 1] + 1)
            if dn is not None:
                v = min(v, dn[j] + 1)
                if j + 1 < W: v = min(v, dn[j + 1] + 1.41421)
                if j: v = min(v, dn[j - 1] + 1.41421)
            d[i, j] = v
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--depth-over-width", type=float, default=1.0,
                    help="깊이/폭. **측면 참조에서 재라** — 지어내면 1.4배 깊어진다")
    ap.add_argument("--bevel", type=int, default=3,
                    help="판 경계 골의 폭(px). 판보다 넓으면 판이 통째로 경사면이 된다")
    ap.add_argument("--groove", type=float, default=0.030)
    ap.add_argument("--cut-bottom", type=float, default=0.78,
                    help="이 비율 아래는 어깨로 보고 자른다")
    a = ap.parse_args()
    d = pathlib.Path(a.dir).resolve()
    lab = np.load(d / "labels.npy")
    head = np.load(d / "mask.npy").copy()
    H, W = head.shape
    head[int(H * a.cut_bottom):] = False
    lab = np.where(head, lab, 0)

    dg = edt(head)
    Rg = dg.max()
    t = np.clip(dg / max(Rg, 1e-6), 0, 1)
    hg = np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1))       # 전체 팽창(돔)

    # **판은 평면.** 돔으로 부풀리면 표면이 물집이 된다 (실측: 법선 표준편차 54도)
    Y, X = np.mgrid[0:H, 0:W]
    hp = hg.copy()
    groove = np.zeros_like(hg)
    used = 0
    for k in [v for v in np.unique(lab) if v > 0]:
        m = lab == k
        if m.sum() < 80:
            continue
        yy, xx, vv = Y[m], X[m], hg[m]
        A = np.stack([xx, yy, np.ones_like(xx)], 1).astype(float)
        coef, *_ = np.linalg.lstsq(A, vv, rcond=None)
        hp[m] = A @ coef
        sub = np.zeros_like(head); sub[m] = True
        groove[m] = np.clip(edt(sub)[m] / a.bevel, 0, 1) ** 0.6
        used += 1

    h = hp + a.groove * (groove - 1.0) * Rg * 0.35
    h[~head] = 0
    mx = h.max() + 1e-9
    h = (np.asarray(Image.fromarray((h / mx * 255).astype(np.uint8), "L")
                    .filter(ImageFilter.MedianFilter(5))).astype(float) / 255.0 * mx)
    h[~head] = 0
    ys, xs = np.where(head)
    width = xs.max() - xs.min()
    h *= a.depth_over_width * width / (h.max() + 1e-9)

    gy, gx = np.gradient(h)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9

    # 판 안쪽 평평도 (bevel 띠 제외)
    devs = []
    for k in [v for v in np.unique(lab) if v > 0]:
        m = lab == k
        if m.sum() < 200:
            continue
        mi = np.asarray(Image.fromarray((m * 255).astype(np.uint8), "L")
                        .filter(ImageFilter.MinFilter(13))) > 127
        mi &= m
        if mi.sum() < 60:
            continue
        nn = n[mi]; mu = nn.mean(0); mu /= np.linalg.norm(mu) + 1e-9
        devs.append((mi.sum(), np.degrees(np.arccos(np.clip(nn @ mu, -1, 1))).mean()))
    flat = float(np.average([x[1] for x in devs],
                            weights=[x[0] for x in devs])) if devs else float("nan")

    d0 = h / (h.max() + 1e-9)
    Image.fromarray(np.where(head[..., None], (d0[..., None] * 255) * np.ones(3), 255)
                    .astype(np.uint8)).save(d / "depth.png")
    Image.fromarray(np.where(head[..., None], (n * 0.5 + 0.5) * 255, 255)
                    .astype(np.uint8)).save(d / "normal.png")
    L = np.array([-0.4, -0.6, 0.7]); L /= np.linalg.norm(L)
    sh = np.clip((n * L).sum(-1), 0, 1) ** 0.8
    Image.fromarray(np.where(head[..., None], (sh[..., None] * 235 + 20) * np.ones(3), 255)
                    .astype(np.uint8)).save(d / "shade.png")
    np.save(d / "depth.npy", h)
    json.dump({"panels": used, "depth_over_width": a.depth_over_width,
               "bevel_px": a.bevel, "flatness_deg": round(flat, 1),
               "flatness_note": "판 안쪽 법선 각도 표준편차. 10도 이하 평면 / 30도 이상 물집"},
              open(d / "depth.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"판 {used}개 · 깊이/폭 {a.depth_over_width} · 판 안쪽 평평도 {flat:.1f}도")
    print(d / "depth.png")


if __name__ == "__main__":
    main()
