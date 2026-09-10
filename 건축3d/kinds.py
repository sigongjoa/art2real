# -*- coding: utf-8 -*-
"""**종류를 센다.** 개수가 아니라 「서로 다른 형태가 몇 가지냐」다.

    python kinds.py D:/imggen/blades6/r6_gate_front.png [내판.png ...] [--min 40]

## 왜 필요한가

밀도(10만 화소당 선 덩어리)만 향해 루프를 돌렸더니 기둥이 **나사산**이 됐다.
같은 마디를 스물두 개 깔면 밀도는 오르는데 그림은 나빠진다.

`5_blender/부품/거리.py` 가 이미 같은 병을 적어놨다 —
`vend` 는 **물건 35개인데 종류는 여덟**이었고, 「화소는 찼는데 종류가 없었다」.

그래서 눈금이 둘이어야 한다. **밀도와 종류.**

## 어떻게 세나

윤곽마다 **푸리에 기술자**를 뽑는다. 윤곽 점을 복소수 z=x+iy 로 놓고 FFT 를 하면 —

    첫 계수(k=0)를 버리면      위치가 사라진다 (평행이동 불변)
    |계수| 만 쓰면             회전과 시작점이 사라진다
    |c1| 로 나누면             크기가 사라진다 (**큰 크로켓과 작은 크로켓이 같은 종류**)

남은 벡터가 「모양」이다. 가까운 것끼리 묶으면 그 묶음 수가 종류 수다.

## 문턱을 하나로 안 박는다

묶는 거리 문턱은 임의값이라, **여러 문턱에서 세서 같이 찍는다.**
표본 하나로 눈금을 긋지 않는다 (`LESSONS` — loop 를 표본 셋으로 그은 실수).

`demo()` 로 눈금을 잡았다 — **원·사각·삼각을 크기 셋씩 그려 놓으면 0.10 에서 셋으로 갈린다.**
그보다 넓으면 사각과 삼각이 붙고, 0.30 이면 다 한 가지가 된다.
장식처럼 서로 비슷한 것들은 더 좁혀야 할 수 있다 — 그래서 넷을 같이 찍는다.
"""
import sys

import cv2
import numpy as np

N_PT = 128                 # 윤곽을 몇 점으로 다시 샘플링하나
N_HARM = 16                # 쓸 하모닉 수. 낮을수록 큰 형태만 본다
THRESHOLDS = (0.10, 0.15, 0.20, 0.30)


def gold_mask(bgr):
    """`gate_trace.py` 와 같은 마스크. 두 파일이 갈리면 종류와 밀도가 다른 걸 센다."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = ((h > 12) & (h < 45) & (s > 60) & (v > 90)).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, k, iterations=1)


def resample(c, n=N_PT):
    """윤곽을 **둘레 등간격** n 점으로. 점 수가 제각각이면 기술자를 못 비교한다."""
    p = c.reshape(-1, 2).astype(np.float64)
    d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(np.r_[p, p[:1]], axis=0).T))]
    if d[-1] < 1e-9:
        return None
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[np.interp(t, d, np.r_[p[:, 0], p[0, 0]]),
                 np.interp(t, d, np.r_[p[:, 1], p[0, 1]])]


def descriptor(c):
    """푸리에 기술자. 평행이동·회전·크기·시작점에 불변인 벡터."""
    p = resample(c)
    if p is None:
        return None
    f = np.fft.fft(p[:, 0] + 1j * p[:, 1])
    f[0] = 0                                   # 위치 버림
    a = np.abs(f)
    # **시계/반시계에 따라 기본 하모닉이 a[1] 이 아니라 a[-1] 에 온다.**
    # a[1] 로만 나눴더니 시계방향 윤곽에서 0 에 가까운 수로 나눠 거리가 10^4 로 튀었다
    base = max(a[1], a[-1])
    if base < 1e-9:
        return None
    a = a / base                               # 크기 버림
    return np.r_[a[2:2 + N_HARM], a[-N_HARM:][::-1]]


def cluster(ds, thr):
    """**탐욕 묶기.** 먼저 온 것을 대표로 삼고 문턱 안이면 붙인다.

    계층 군집을 쓸 수도 있지만 여기서는 「몇 가지냐」만 알면 되고,
    탐욕이 순서에 의존하는 건 **큰 것부터 넣어** 줄인다."""
    reps, lab = [], []
    for d in ds:
        for i, r in enumerate(reps):
            if np.linalg.norm(d - r) < thr:
                lab.append(i)
                break
        else:
            reps.append(d)
            lab.append(len(reps) - 1)
    return lab, len(reps)


def count(path, min_area=40.0, hgt=1024):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    assert im is not None, path
    im = cv2.resize(im, (int(round(im.shape[1] * hgt / im.shape[0])), hgt),
                    interpolation=cv2.INTER_AREA)
    m = gold_mask(im)
    cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cs = [c for c in cs if cv2.contourArea(c) >= min_area and len(c) >= 8]
    cs.sort(key=cv2.contourArea, reverse=True)     # 큰 것이 대표가 되게
    ds = [d for d in (descriptor(c) for c in cs) if d is not None]
    out = {"path": path, "덩어리": len(ds)}
    for t in THRESHOLDS:
        out["종류@%.2f" % t] = cluster(ds, t)[1]
    return out


def demo():
    """세 모양(원·사각·별)을 크기를 바꿔 여러 개 그리고, **종류가 셋**으로 세지는지 본다."""
    gold = (60, 200, 240)                          # BGR
    im = np.zeros((520, 900, 3), np.uint8)         # 겹치면 윤곽이 합쳐진다. 넉넉히
    for i, r in enumerate((16, 28, 42)):
        cv2.circle(im, (110 + i * 190, 90), r, gold, -1)
    for i, r in enumerate((16, 28, 42)):
        cv2.rectangle(im, (110 + i * 190 - r, 250 - r), (110 + i * 190 + r, 250 + r), gold, -1)
    for i, r in enumerate((18, 30, 44)):            # 삼각형
        cx, cy = 110 + i * 190, 430
        pts = np.array([[cx, cy - r], [cx - r, cy + r], [cx + r, cy + r]], np.int32)
        cv2.fillPoly(im, [pts], gold)
    r = count_array(im, 40.0)
    assert r["덩어리"] == 9, r
    # **크기가 셋씩 달라도 세 가지**로 세져야 한다. 원·사각·삼각이 갈리는 문턱이 0.10 이다
    assert r["종류@0.10"] == 3, r
    ks = [r["종류@%.2f" % t] for t in THRESHOLDS]
    assert ks == sorted(ks, reverse=True), ks      # 문턱이 넓어지면 종류는 줄기만 한다
    print("kinds.demo OK  덩어리 9 -> 종류 %s (문턱 %s)" % (ks, list(THRESHOLDS)))


def count_array(im, min_area):
    m = gold_mask(im)
    cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cs = [c for c in cs if cv2.contourArea(c) >= min_area and len(c) >= 8]
    cs.sort(key=cv2.contourArea, reverse=True)
    ds = [d for d in (descriptor(c) for c in cs) if d is not None]
    out = {"덩어리": len(ds)}
    for t in THRESHOLDS:
        out["종류@%.2f" % t] = cluster(ds, t)[1]
    return out


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        av = sys.argv[1:]
        mn = 40.0
        if "--min" in av:
            i = av.index("--min")
            mn = float(av[i + 1])
            del av[i:i + 2]                        # **값까지 지운다.** 안 지웠더니 "40" 을 경로로 열었다
        for p in [a for a in av if not a.startswith("--")]:
            r = count(p, mn)
            print("%-46s 덩어리 %4d   " % (r["path"][-46:], r["덩어리"])
                  + "  ".join("%s %3d" % (k, v) for k, v in r.items()
                              if k.startswith("종류")))


COLORS = [(60, 200, 240), (240, 120, 60), (90, 220, 120), (220, 90, 220),
          (240, 230, 90), (120, 120, 250), (250, 170, 90), (140, 250, 250),
          (200, 60, 140), (90, 250, 190), (250, 90, 90), (170, 200, 60),
          (120, 60, 250), (60, 140, 200), (200, 200, 200), (250, 60, 200),
          (60, 250, 60), (200, 140, 250)]


def draw(path, dst, min_area=40.0, thr=0.10, hgt=1024):
    """**무엇을 어떻게 셌는지 그림으로 낸다.** 왼쪽은 원본 위 색칠, 오른쪽은 종류 견본.

    같은 색 = 같은 종류다. 숫자는 종류 번호. 크기가 달라도 모양이 같으면 같은 색이 나온다."""
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    assert im is not None, path
    im = cv2.resize(im, (int(round(im.shape[1] * hgt / im.shape[0])), hgt),
                    interpolation=cv2.INTER_AREA)
    m = gold_mask(im)
    cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    cs = [c for c in cs if cv2.contourArea(c) >= min_area and len(c) >= 8]
    cs.sort(key=cv2.contourArea, reverse=True)
    pair = [(c, descriptor(c)) for c in cs]
    pair = [(c, d) for c, d in pair if d is not None]
    lab, n = cluster([d for _, d in pair], thr)

    left = (im * 0.30).astype(np.uint8)
    for (c, _), k in zip(pair, lab):
        cv2.drawContours(left, [c], -1, COLORS[k % len(COLORS)], 2)
        x, y, w, h = cv2.boundingRect(c)
        cv2.putText(left, str(k), (x, max(12, y - 3)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, COLORS[k % len(COLORS)], 1, cv2.LINE_AA)

    # 오른쪽 — 종류마다 대표 하나를 같은 크기로 정규화해 나란히
    cell, cols = 96, 4
    rows = (n + cols - 1) // cols
    right = np.zeros((max(hgt, rows * cell), cols * cell, 3), np.uint8)
    first = {}
    for (c, _), k in zip(pair, lab):
        first.setdefault(k, c)
    for k in range(n):
        c = first[k].reshape(-1, 2).astype(np.float64)
        c -= c.mean(axis=0)
        s = max(np.abs(c).max(), 1e-6)
        c = (c / s * (cell * 0.36) + [cell * (k % cols) + cell / 2,
                                      cell * (k // cols) + cell / 2]).astype(np.int32)
        cv2.fillPoly(right, [c], COLORS[k % len(COLORS)])
        cv2.putText(right, str(k), (cell * (k % cols) + 4, cell * (k // cols) + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    if right.shape[0] < left.shape[0]:
        right = np.vstack([right, np.zeros((left.shape[0] - right.shape[0],
                                            right.shape[1], 3), np.uint8)])
    out = np.hstack([left, right[:left.shape[0]]])
    cv2.imwrite(dst, out)
    print("DRAW %s  덩어리 %d · 종류 %d (문턱 %.2f) -> %s"
          % (path.split("/")[-1], len(pair), n, thr, dst))
    return n
