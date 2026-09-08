# -*- coding: utf-8 -*-
"""턴어라운드 판의 재질 영역(armor/dark/gold)을 **공통 좌표창**으로 리샘플한다.

    D:\imggen\venv\Scripts\python.exe art_regions.py

좌표창 (WIN): 이미지 1024x1024
    가로 = 월드 u in [-0.6, 0.6]   (front 는 u=x, side 는 u=y, back 은 u=-x)
    세로 = 월드 z in [ 1.1, -0.1]  (위가 z 큰 쪽)
메시도 같은 창으로 직교 렌더하면 화소가 일대일로 맞는다.
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trail3_freecad"))
from keys_from_art import Frame

RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1


def to_win(q, px_of_u, py_of_z):
    """판 화소맵 q -> 좌표창. 최근접 표본 (라벨맵이라 보간 금지)."""
    us = np.linspace(U0, U1, RES)
    zs = np.linspace(Z1, Z0, RES)
    xs = np.clip(px_of_u(us).astype(int), 0, q.shape[1] - 1)
    ys = np.clip(py_of_z(zs).astype(int), 0, q.shape[0] - 1)
    return q[np.ix_(ys, xs)]


def main():
    F = Frame()
    out = {}
    # front: 화면 x = 월드 +x, 세로는 정면 접지선
    out["front"] = to_win(F.fq, lambda u: u * F.H + F.x_mid,
                          lambda z: F.y_bot - z * F.H)
    # side: 화면 x = 월드 +y (앞이 화면 왼쪽), 세로는 측면 접지선
    out["side"] = to_win(F.sq, lambda u: u * F.H + F.y_mid,
                         lambda z: F.s_bot - z * F.H)
    # back: 화면 x = 월드 -x
    P = __import__("keys_from_art").panels()
    bsil, bx0, bq = P["back"]
    b_bot = np.nonzero(bsil.any(1))[0].max()
    c = np.nonzero(bsil[int(round(b_bot - 0.16 * F.H)):int(round(b_bot - 0.02 * F.H))].any(0))[0]
    b_mid = (c.min() + c.max()) / 2
    out["back"] = to_win(bq, lambda u: -u * F.H + b_mid,
                         lambda z: b_bot - z * F.H)

    pal = np.array([[255, 255, 255], [205, 205, 212], [28, 28, 34], [226, 176, 62]], np.uint8)
    tiles = []
    for k in ("front", "side", "back"):
        np.save(os.path.join(HERE, f"win_{k}.npy"), out[k])
        n = [int((out[k] == i).sum()) for i in range(4)]
        print(f"{k:6s} 배경 {n[0]:>7,} 갑주 {n[1]:>7,} 검정 {n[2]:>6,} 금색 {n[3]:>6,}")
        t = pal[out[k]]
        cv2.putText(t, k, (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        tiles.append(cv2.resize(t, (420, 420)))
    cv2.imwrite(os.path.join(HERE, "out", "step3a_regions.png"),
                cv2.cvtColor(np.hstack(tiles), cv2.COLOR_RGB2BGR))
    print("out/step3a_regions.png")


if __name__ == "__main__":
    main()
