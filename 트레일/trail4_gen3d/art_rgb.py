# -*- coding: utf-8 -*-
"""원화 3판의 **RGB** 를 공통 좌표창 + 메시 정렬까지 적용해 저장한다.

    D:\imggen\venv\Scripts\python.exe art_rgb.py

art_regions.py 는 클래스 라벨만 냈다. 굽는 데는 실제 색이 필요하다.
FIT 은 step3b 격자탐색 실측값 — 판이 메시보다 이만큼 이동/축소돼 있으니
판을 메시 공간으로 되돌린다.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trail3_freecad"))
from keys_from_art import Frame, panels

RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1
# 정렬 상수는 fit_search.py 가 찾아 fit.json 에 넣는다. 여기에 박아두면
# 갱신할 때 파일마다 고쳐야 하고 실제로 한 번 엇갈렸다.
import json as _json
FIT = {k: tuple(v) for k, v in
       _json.load(open(os.path.join(HERE, "fit.json"))).items()}
SHEET = os.path.join(HERE, "..", "trail2_manga_anim", "ref", "body_turn.png")


def main():
    F = Frame()
    sheet = np.asarray(Image.open(SHEET).convert("RGB"))
    P = panels()
    us = np.linspace(U0, U1, RES)
    zs = np.linspace(Z1, Z0, RES)

    geo = {
        "front": (F.f, F.fx0, lambda u: u * F.H + F.x_mid, lambda z: F.y_bot - z * F.H),
        "side":  (F.s, F.sx0, lambda u: u * F.H + F.y_mid, lambda z: F.s_bot - z * F.H),
    }
    bsil, bx0, _ = P["back"]
    b_bot = np.nonzero(bsil.any(1))[0].max()
    c = np.nonzero(bsil[int(round(b_bot - 0.16 * F.H)):int(round(b_bot - 0.02 * F.H))].any(0))[0]
    b_mid = (c.min() + c.max()) / 2
    geo["back"] = (bsil, bx0, lambda u: -u * F.H + b_mid, lambda z: b_bot - z * F.H)

    for k, (sil, x0, fx, fy) in geo.items():
        h, w = sil.shape
        img = sheet[:h, x0:x0 + w]
        xs = np.clip(fx(us).astype(int), 0, w - 1)
        ys = np.clip(fy(zs).astype(int), 0, h - 1)
        rgb = img[np.ix_(ys, xs)]
        alpha = sil[np.ix_(ys, xs)]
        # 판 -> 메시 공간 (step3b 실측 역변환)
        dx, dy, s = FIT[k]
        yy, xx = np.mgrid[0:RES, 0:RES]
        cc = RES / 2
        # step3b 격자탐색은 "**메시**를 s배 축소하고 (dx,dy) 옮기면 원화" 였다.
        # 원화를 메시 공간으로 가져오려면 메시좌표 x -> 원화좌표 s*(x-cc)+cc+dx 로 표본.
        # 같은 식을 원화에 그대로 걸면 방향이 뒤집혀 IoU 0.729 -> 0.478 로 떨어진다.
        sx = np.clip(np.rint(s * (xx - cc) + cc + dx), 0, RES - 1).astype(int)
        sy = np.clip(np.rint(s * (yy - cc) + cc + dy), 0, RES - 1).astype(int)
        rgb = rgb[sy, sx]; alpha = alpha[sy, sx]
        out = np.dstack([rgb, np.where(alpha, 255, 0).astype(np.uint8)])
        np.save(os.path.join(HERE, f"rgb_{k}.npy"), out)
        # 메시가 원화보다 두꺼워서 투영점이 실루엣 밖으로 나가는 면이 19.7% 다.
        # 단색으로 메우면 실루엣 가장자리에 회색 띠가 생긴다. 가장 가까운 유효
        # 화소의 좌표를 미리 구해 두고 굽기에서 스냅시킨다.
        valid = (alpha > 0).astype(np.uint8)
        dist, lbl = cv2.distanceTransformWithLabels(
            1 - valid, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
        ys0, xs0 = np.nonzero(valid)               # 라벨 1..N 이 유효화소 순서다
        lut = np.zeros((len(ys0) + 1, 2), np.int32)
        lut[1:, 0] = ys0; lut[1:, 1] = xs0
        snap = lut[lbl]                             # (RES,RES,2) -> 가장 가까운 유효 화소
        np.save(os.path.join(HERE, f"snap_{k}.npy"),
                np.dstack([snap, dist.astype(np.int32)[..., None]]).astype(np.int32))
        print(f"       스냅맵: 밖 화소 거리 중앙 {np.median(dist[valid==0]):.0f}px "
              f"p90 {np.percentile(dist[valid==0],90):.0f}px")
        cv2.imwrite(os.path.join(HERE, "out", f"art_rgb_{k}.png"),
                    cv2.cvtColor(out, cv2.COLOR_RGBA2BGRA))
        print(f"{k:6s} 유효화소 {int((alpha>0).sum()):,} ({(alpha>0).mean()*100:.1f}%)")
    print("rgb_*.npy")


if __name__ == "__main__":
    main()
