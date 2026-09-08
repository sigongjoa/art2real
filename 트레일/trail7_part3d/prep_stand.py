# -*- coding: utf-8 -*-
"""스탠드 참조 원화를 PartCrafter 입력으로. 알파로 이미 분리돼 있으니 흰 정사각에 앉힌다.

    python prep_stand.py Doggy_Style Fun_Fun_Fun ...
    python prep_stand.py --demo

**A포즈 생성본을 안 쓴다.** 그 단계가 원본 실루엣을 버린 게 이번 시험의 출발점이다 —
하트가 마네킹이 되고 샹들리에가 로봇이 됐다. 여기 넣는 건 원화 그대로다.
"""
import os
import sys

import cv2
import numpy as np

REF = r"D:\tracks\10_연출기획\out\bench\cast_ref"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "in")
RES = 1024
PAD = 0.06                      # 물건이 테두리에 닿으면 생성이 잘린 걸로 읽는다


def square(im, res=RES, pad=PAD):
    if im.ndim == 3 and im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    ys, xs = np.where((im < 250).any(2))
    if len(ys) == 0:
        raise ValueError("전경이 없다")
    im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = int(max(im.shape[:2]) * (1 + 2 * pad))
    pan = np.full((s, s, 3), 255, np.uint8)
    y0, x0 = (s - im.shape[0]) // 2, (s - im.shape[1]) // 2
    pan[y0:y0 + im.shape[0], x0:x0 + im.shape[1]] = im
    return cv2.resize(pan, (res, res), interpolation=cv2.INTER_AREA)


def demo():
    a = np.zeros((40, 60, 4), np.uint8)
    a[10:30, 20:40, :3] = 30
    a[10:30, 20:40, 3] = 255                     # 가운데만 불투명
    o = square(a, res=128, pad=0.25)   # 여백이 있어야 모서리가 흰색이다
    assert o.shape == (128, 128, 3), o.shape
    assert (o[2, 2] == 255).all(), "바탕이 흰색이어야 한다"
    assert (o[64, 64] < 100).all(), "물건이 가운데 있어야 한다"
    ys, xs = np.where((o < 250).any(2))
    assert abs((ys.max() - ys.min()) - (xs.max() - xs.min())) <= 2, "정사각 비율이 안 깨져야"
    print("자체검사 통과")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo(); raise SystemExit
    os.makedirs(OUT, exist_ok=True)
    for n in sys.argv[1:]:
        im = cv2.imdecode(np.fromfile(os.path.join(REF, n + ".png"), np.uint8),
                          cv2.IMREAD_UNCHANGED)
        p = os.path.join(OUT, "stand_%s.png" % n)
        cv2.imencode(".png", square(im))[1].tofile(p)
        print("%s  <- %s" % (p, im.shape[:2]))
