# -*- coding: utf-8 -*-
"""**숫자 옆에 그림.** hull 을 되던져 원화 위에 겹친다. 정렬 전과 후를 나란히.

    python 겹침.py        ->  out/겹침.png

`hull.py` 가 「못 덮은 5.09%」라고 찍어도 그게 어디인지는 안 알려준다.
경계를 따라 고르게 얇으면 이산화이고, 한 군데 뭉쳐 있으면 판들이 싸운 것이다.
**숫자가 같아도 원인이 다르다.**

    검정  둘 다 있다
    빨강  원화엔 있는데 hull 이 못 덮었다   <- 이게 어떻게 생겼는지가 답이다
    파랑  hull 이 원화보다 더 나왔다

두 줄 다 `hull.project` 로 그린다 — 메시가 아니라 **정확한 hull** 이다. 마칭큐브가 경계를
반 복셀 깎는 몫이 섞이면 전후 비교가 사과 대 배가 된다. 메시로 되던진 값은 `hull.py` 가 찍는다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
TH = 300                                            # 타일 한 변


def tile(masks):
    """세 시점 겹침 그림 + 못 덮은 비율."""
    p, m = H.project(masks), H.miss(masks)
    out = []
    for v in W.VIEWS:
        a, q = masks[v], p[v]
        rgb = np.full(a.shape + (3,), 255, np.uint8)
        rgb[a & q] = (40, 40, 40)          # 둘 다
        rgb[a & ~q] = (220, 40, 40)        # 원화에만 — hull 이 못 덮은 자리
        rgb[~a & q] = (60, 110, 220)       # hull 에만
        out.append((Image.fromarray(rgb).resize((TH, TH), Image.LANCZOS), m[v]))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    src = {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}
    pre = {v: H.to_win(H.declutter(W.art_mask(os.path.join(H.IN7, f)))) for v, f in src.items()}
    fit = H.align(pre)
    rows = [("정렬 전 — 판마다 자기 bbox 키로 늘렸다", tile(pre)),
            ("정렬 후 — side(dy %+.0f s %.4f) · back(dx %+.0f dy %+.0f s %.4f)" % tuple(fit),
             tile(H._warp(pre, fit)))]

    W_, H_ = 3 * TH + 4 * 20, 2 * (TH + 54) + 44
    sheet = Image.new("RGB", (W_, H_), "white")
    d = ImageDraw.Draw(sheet)
    f13, f15 = _font(13), _font(15)
    d.text((20, 12), "빨강 = hull 이 원화를 못 덮은 자리", font=f15, fill=(20, 20, 20))
    for r, (label, ts) in enumerate(rows):
        y = 44 + r * (TH + 54)
        d.text((20, y), label, font=f13, fill=(90, 90, 90))
        for i, (im, mv) in enumerate(ts):
            x = 20 + i * (TH + 20)
            sheet.paste(im, (x, y + 20))
            d.text((x, y + TH + 24), "%s  못 덮음 %.2f%%" % (W.VIEWS[i], 100 * mv), font=f13,
                   fill=(200, 60, 60) if mv > .01 else (90, 90, 90))
    sheet.save(os.path.join(OUT, "겹침.png"))
    print("-> out/겹침.png   (위 정렬 전 · 아래 정렬 후)")


if __name__ == "__main__":
    main()
