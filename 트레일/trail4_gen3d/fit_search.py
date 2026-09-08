# -*- coding: utf-8 -*-
"""3판 정렬 상수를 다시 찾는다. **다른 스크립트와 같은 표본 규약**으로.

    D:\imggen\venv\Scripts\python.exe fit_search.py

규약(39번): 원화를 메시 공간으로 가져올 때
    표본좌표 = s*(x - c) + c + dx        (x 는 메시 좌표)
cv2.warpAffine 은 순방향 매핑이라 이것과 반대다. 한 번 그렇게 짰다가
기존 IoU 가 0.803 인데 0.539 로 나왔다 — 규약이 다르면 비교가 안 된다.
행/열이 분리되므로 np.ix_ 로 1차원 인덱스만 만들면 격자탐색이 빠르다.
"""
import json, os
import cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 1024
c = RES / 2
ax = np.arange(RES)


def warp(a, dx, dy, s):
    sx = np.clip(np.rint(s * (ax - c) + c + dx), 0, RES - 1).astype(int)
    sy = np.clip(np.rint(s * (ax - c) + c + dy), 0, RES - 1).astype(int)
    return a[np.ix_(sy, sx)]


def sil(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    return a[..., 3] > 128


def search(A, G):
    best = None
    for s in np.arange(0.86, 1.09, 0.01):
        for dx in range(-48, 49, 4):
            for dy in range(-40, 41, 4):
                w = warp(A, dx, dy, s)
                i = (w & G).sum() / max((w | G).sum(), 1)
                if best is None or i > best[0]:
                    best = (i, int(dx), int(dy), round(float(s), 3))
    _, bx, by, bs = best
    for s in np.arange(bs - 0.01, bs + 0.011, 0.0025):
        for dx in range(bx - 4, bx + 5):
            for dy in range(by - 4, by + 5):
                w = warp(A, dx, dy, s)
                i = (w & G).sum() / max((w | G).sum(), 1)
                if i > best[0]:
                    best = (i, int(dx), int(dy), round(float(s), 4))
    return best


OLD = {"front": (8, 8, 0.94), "side": (8, 24, 0.94), "back": (40, 24, 0.94)}
MESH = {k: f"out/dfwin_{k}.png" for k in OLD}
new = {}
print(f"{'판':6s} {'기존 IoU':>9s} {'새 IoU':>8s} {'개선':>7s}   새 상수")
for k in OLD:
    A = np.load(os.path.join(HERE, f"true_{k}_clean.npy"))
    G = sil(os.path.join(HERE, MESH[k]))
    o = warp(A, *OLD[k])
    i0 = (o & G).sum() / max((o | G).sum(), 1)
    b = search(A, G)
    new[k] = [b[1], b[2], b[3]]
    print(f"{k:6s} {i0:9.3f} {b[0]:8.3f} {b[0]-i0:+7.3f}   dx{b[1]:+3d} dy{b[2]:+3d} s{b[3]:.4f}")
json.dump(new, open(os.path.join(HERE, "fit.json"), "w"), indent=1)
print("fit.json 갱신:", new)
