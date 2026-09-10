# -*- coding: utf-8 -*-
"""**조각 수는 나뉜 정도가 아니다.** 판 분할이 실제로 얼마나 나눴는지 잰다.

    python 분할.py [케이스]      ->  out/분할_<케이스>.png + 표

`깊이.py` 가 판을 조각으로 나눈다. 무진1997 은 front 28조각이 나왔는데, 세어보니
**2개가 전경의 90%를 덮는다.** 나머지 26개는 중앙값 93화소짜리 부스러기다.

숫자만 보면 잘 나뉜 것 같고 실제로는 통짜다. 그래서 조각 수가 아니라 **90%를 덮는 데
몇 조각이 드는가**를 본다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import win as W
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def 재기(case=None):
    case = case or "무진1997"
    rows = []
    for v in W.VIEWS:
        p = os.path.join(OUT, "깊이", case, v, "labels_grown.npy")
        assert os.path.exists(p), f"판 분할이 없다: {p} — 깊이.py 를 먼저 돌린다"
        a = np.load(p)
        s = sorted((int((a == k).sum()) for k in np.unique(a) if k > 0), reverse=True)
        tot, c, n = sum(s), 0, 0
        for x in s:
            c += x; n += 1
            if c >= 0.9 * tot:
                break
        rows.append((v, len(s), tot, n, s[0], s[len(s) // 2]))
    return case, rows


def figure(case=None):
    case, rows = 재기(case)
    img = Image.new("L", (900, 170 + 30 * len(rows)), 255)
    d = ImageDraw.Draw(img)
    d.text((16, 12), f"{case} — 조각은 많은데 큰 게 몇 개 없다", font=_font(22), fill=0)
    d.text((16, 52), "판       조각    전경 화소     90%를 덮는 조각   제일 큰 것   중앙값",
           font=_font(17), fill=0)
    for i, (v, n, tot, k, mx, med) in enumerate(rows):
        d.text((16, 82 + i * 28),
               f"{v:8} {n:5} {tot:12,} {k:14} {mx:14,} {med:10,}", font=_font(17), fill=0)
    y = 100 + 28 * len(rows)
    d.text((16, y), "조각 수는 나뉜 정도가 아니다 — 90%를 덮는 데 몇 조각이 드는가를 본다",
           font=_font(18), fill=0)
    # 크기 막대
    v, n, tot, k, mx, med = rows[0]
    a = np.load(os.path.join(OUT, "깊이", case, rows[0][0], "labels_grown.npy"))
    s = sorted((int((a == kk).sum()) for kk in np.unique(a) if kk > 0), reverse=True)
    x0, y0, wpx = 16, y + 34, 860
    for i, x in enumerate(s[:40]):
        h = max(1, int(28 * x / max(s[0], 1)))
        bx = x0 + i * (wpx // 40)
        d.rectangle([bx, y0 + 28 - h, bx + wpx // 40 - 3, y0 + 28], fill=0)
    img = img.crop((0, 0, 900, y0 + 40))
    p = os.path.join(OUT, f"분할_{case}.png")
    img.save(p)
    print(f"-> {os.path.basename(p)}")
    for v, n, tot, k, mx, med in rows:
        print(f"   {v:6} 조각 {n:3}  90%를 덮는 조각 {k}개  최대 {mx:,}  중앙값 {med:,}")
    return rows


def demo(case=None):
    rows = figure(case)
    for v, n, tot, k, mx, med in rows:
        assert k <= 5, f"{v}: 90%를 덮는 데 {k} 조각이 든다 — 잘 나뉘었다는 뜻이라 벽이 안 선다"
        assert n >= 10, f"{v}: 조각이 {n}개뿐이다 — 「숫자만 많다」가 성립 안 한다"
    print("분할 자체검사 통과 — 조각은 많고 큰 것은 몇 개 없다")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
