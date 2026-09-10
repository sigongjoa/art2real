# -*- coding: utf-8 -*-
"""**대칭은 인물의 성질이 아니라 부위의 성질이다.** 재질마다 좌우가 맞는지 잰다.

    python 대칭.py [케이스]      ->  out/대칭_<케이스>.png + 표

미러를 통째로 걸면 몸은 맞고 **칼이 둘이 된다.** 무진은 칼을 허리 뒤에 가로로 차고
머리를 한쪽으로 묶었다 — 그 둘은 좌우가 다른 게 정상이다.

정면 판에서 재질마다 좌우를 뒤집어 겹쳐 IoU 를 잰다. 1 에 가까우면 미러를 걸어도 되고,
낮으면 걸면 안 된다. **어디에 걸지를 눈이 아니라 이 표가 정한다.**
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
from 계획 import _font
from 부위람다 import 재질판

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
문턱 = 0.85                      # 이보다 높으면 미러를 걸어도 된다


def 재기(case=None):
    case = case or "무진1997"
    부위 = 재질판(case, view="front")
    # **인물의 중심으로 접는다.** 부위 제 중심으로 접으면 도포도 0.387 이 나온다 —
    # 칼이 가로지르는 부위는 제 bbox 중심이 몸 중심이 아니다.
    전경 = np.zeros_like(next(iter(부위.values())))
    for m in 부위.values():
        전경 |= m
    xs0 = np.where(전경.any(0))[0]
    lo, hi = int(xs0.min()), int(xs0.max())
    # bbox 중심도 몸 중심이 아니다 — 칼이 한쪽으로 삐져나와 축을 끌고 간다.
    # 그래서 **전경이 제일 잘 접히는 축**을 찾는다. 그게 인물의 대칭축이다.
    def 접기(전, cc):
        ww = min(cc - lo, hi - cc)
        if ww < 8:
            return 0.0, ww
        aa, bb = 전[:, cc - ww:cc], 전[:, cc:cc + ww][:, ::-1]
        nn = min(aa.shape[1], bb.shape[1])
        return W.iou(aa[:, -nn:], bb[:, -nn:]), ww
    c, best = (lo + hi) // 2, -1.0
    for cc in range((lo + hi) // 2 - 80, (lo + hi) // 2 + 81, 2):
        v, _ = 접기(전경, cc)
        if v > best:
            best, c = v, cc
    w = min(c - lo, hi - c) or 1
    rows = []
    for k, m in 부위.items():
        a = m[:, c - w:c]
        b = m[:, c:c + w][:, ::-1]
        n = min(a.shape[1], b.shape[1])
        rows.append((k, int(m.sum()), W.iou(a[:, -n:], b[:, -n:])))
    return case, sorted(rows, key=lambda r: -r[1])


def figure(case=None):
    case, rows = 재기(case)
    img = Image.new("L", (720, 130 + 30 * len(rows)), 255)
    d = ImageDraw.Draw(img)
    d.text((16, 12), f"{case} — 재질마다 좌우가 맞나 (정면)", font=_font(22), fill=0)
    d.text((16, 52), "부위(재질 색)        화소       좌우 IoU     미러", font=_font(18), fill=0)
    for i, (k, n, v) in enumerate(rows):
        d.text((16, 82 + i * 28),
               f"{str(k):18} {n:9,} {v:11.3f} {'   걸어도 된다' if v >= 문턱 else '   걸면 안 된다'}",
               font=_font(18), fill=0)
    d.text((16, 96 + 28 * len(rows)), f"문턱 {문턱} · 대칭축을 찾아서 접었다",
           font=_font(17), fill=0)
    p = os.path.join(OUT, f"대칭_{case}.png")
    img.save(p)
    print(f"-> {os.path.basename(p)}")
    for k, n, v in rows:
        print(f"   {str(k):18} 화소 {n:8,}  좌우 IoU {v:.3f}  "
              f"{'미러 O' if v >= 문턱 else 'ㅁ미러 X'}")
    return rows


def demo(case=None):
    rows = figure(case)
    vals = [v for _, _, v in rows]
    assert len(rows) >= 2, "부위가 하나뿐이다"
    assert max(vals) - min(vals) > 0.1, \
        f"부위마다 대칭이 다 비슷하다 — 부위별로 정할 이유가 없다는 뜻이다 ({vals})"
    걸 = [k for k, _, v in rows if v >= 문턱]
    안 = [k for k, _, v in rows if v < 문턱]
    print(f"대칭 자체검사 통과 — 미러 걸 곳 {len(걸)}개 · 걸면 안 되는 곳 {len(안)}개")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
