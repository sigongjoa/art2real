# -*- coding: utf-8 -*-
"""**원화와 내 판이 어디서 갈리는지 숫자로 잰다.**  python formfit.py <원화.png> <내판.png>

눈으로 「안 맞는다」를 열두 번 고쳤다. 스킬(`art-to-3d-maps`)이 시키는 대로
**형태를 재서** 비교한다. 재는 것 셋 —

    금/검정/하늘 면적    화면을 무엇이 채우고 있나
    선 방향 히스토그램   수직·수평이냐 방사냐. **이게 「건물이냐 부채냐」를 가른다**
    소실점 수렴도        선을 늘였을 때 한 점에 모이나 (방사 구조의 정의)

세 번째가 핵심이다. 원화는 밑에서 올려본 **방사**고 상자로 지으면 **수직·수평**이다.
같은 금색, 같은 남색이어도 이게 다르면 절대 안 닮는다.
"""
import sys

import numpy as np
from PIL import Image

N_BIN = 12                       # 선 방향을 15도씩 열둘로


def load(p, w=512):
    im = Image.open(p).convert("RGB")
    im = im.resize((w, int(round(w * im.size[1] / im.size[0]))), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def masses(a):
    """금 · 검정 · 하늘이 각각 화면의 몇 할인가."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    v = a.max(axis=2)
    gold = (r > 0.35) & (g > 0.28) & (b < r * 0.75) & (v > 0.35)
    dark = v < 0.22
    sky = (b >= r) & ~dark
    n = float(a.shape[0] * a.shape[1])
    return {"금": gold.sum() / n, "검정": dark.sum() / n, "하늘": sky.sum() / n}


def edges(a):
    """소벨. 세기와 방향(선의 방향, 기울기가 아니라)을 돌려준다."""
    y = a.mean(axis=2)
    gx = np.zeros_like(y)
    gy = np.zeros_like(y)
    gx[:, 1:-1] = y[:, 2:] - y[:, :-2]
    gy[1:-1, :] = y[2:, :] - y[:-2, :]
    mag = np.hypot(gx, gy)
    ang = (np.arctan2(gx, -gy)) % np.pi          # 선 방향 = 기울기에 수직
    return mag, ang, gx, gy


def orient(mag, ang, thr):
    m = mag > thr
    h, _ = np.histogram(ang[m], bins=N_BIN, range=(0, np.pi), weights=mag[m])
    return h / max(h.sum(), 1e-9)


def converge(mag, ang, gx, gy, thr):
    """**소실점 수렴도.** 선마다 그 선을 지나는 직선을 세우고 최소제곱 교점을 푼다.

    돌려주는 건 (교점 x, y — 화면 비율) 과 **잔차**(화면 대각선 대비).
    잔차가 작을수록 방사 구조다. 상자로 지은 것은 교점이 안 모여 잔차가 크다."""
    H, W = mag.shape
    m = mag > thr
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        return None
    step = max(1, len(xs) // 4000)
    xs, ys = xs[::step], ys[::step]
    # 선의 법선 (nx, ny) = 기울기 방향. 직선: nx*(x-x0) + ny*(y-y0) = 0
    nx, ny = gx[ys, xs], gy[ys, xs]
    L = np.hypot(nx, ny)
    nx, ny = nx / L, ny / L
    A = np.stack([nx, ny], axis=1)
    b = nx * xs + ny * ys
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    res = np.abs(A @ sol - b)
    diag = float(np.hypot(W, H))
    return sol[0] / W, sol[1] / H, float(np.median(res)) / diag


def report(path):
    a = load(path)
    mag, ang, gx, gy = edges(a)
    thr = float(np.percentile(mag, 92))
    ms = masses(a)
    h = orient(mag, ang, thr)
    c = converge(mag, ang, gx, gy, thr)
    print("\n%s  %dx%d" % (path, a.shape[1], a.shape[0]))
    print("  면적   금 %.2f · 검정 %.2f · 하늘 %.2f" % (ms["금"], ms["검정"], ms["하늘"]))
    # 0도 = 가로선, 90도 = 세로선
    print("  방향   " + " ".join("%3d:%.02f" % (int(i * 180 / N_BIN), v)
                                 for i, v in enumerate(h)))
    print("  수직·수평 비중 %.2f   (0·90도 칸 둘의 합)" % (h[0] + h[N_BIN // 2]))
    if c:
        print("  소실점 (%.2f, %.2f)  잔차 %.3f  ← 작을수록 방사" % c)
    return ms, h, c


def demo():
    """방사 그림과 격자 그림을 지어 잰다. **잔차가 갈리는지만 본다.**"""
    W = 256
    rad = np.zeros((W, W, 3), np.float32)
    grid = np.zeros((W, W, 3), np.float32)
    cx = cy = W // 2
    for k in range(24):                      # 한가운데서 뻗는 살
        t = k * np.pi / 12.0
        for r in range(10, W // 2):
            x, y = int(cx + r * np.cos(t)), int(cy + r * np.sin(t))
            if 0 <= x < W and 0 <= y < W:
                rad[y, x] = 1.0
    grid[::16, :] = 1.0
    grid[:, ::16] = 1.0
    out = []
    for a in (rad, grid):
        mag, ang, gx, gy = edges(a)
        thr = float(np.percentile(mag, 92))
        out.append(converge(mag, ang, gx, gy, thr))
    assert out[0][2] < out[1][2] / 3.0, out      # 방사가 격자보다 훨씬 잘 모인다
    assert abs(out[0][0] - 0.5) < 0.08 and abs(out[0][1] - 0.5) < 0.08, out[0]
    print("formfit.demo OK  방사 잔차 %.3f  격자 잔차 %.3f" % (out[0][2], out[1][2]))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        for p in sys.argv[1:]:
            report(p)


def detail(path, w=512):
    """**디테일에 눈금을 준다.** 선 밀도와 덩어리 수를 센다.

    지금까지 잰 것(면적·방향·수렴)은 전부 **큰 형태**의 지표다. 그게 다 맞아도
    「조촐하다」가 남는 이유는 **작은 것의 수**를 아무도 안 쟀기 때문이다.
    셀에서 선은 기하가 내므로(LESSONS 73·74) 선 밀도는 곧 **부품 수**의 대리값이다."""
    import cv2
    a = (load(path) * 255).astype(np.uint8)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    e = cv2.Canny(g, 60, 160)
    n, _, st, _ = cv2.connectedComponentsWithStats((e > 0).astype(np.uint8), 8)
    big = int((st[1:, cv2.CC_STAT_AREA] >= 12).sum())
    return {"선화소": float(e.mean() / 255.0), "선덩어리": big,
            "면적당덩어리": big / (g.size / 1e5)}
