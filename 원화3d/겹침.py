# -*- coding: utf-8 -*-
"""**숫자 옆에 그림.** hull 을 되받아 던져 원화 위에 겹친다.

    python 겹침.py        ->  out/겹침.png

`hull.py` 가 「못 덮은 5.24%」라고 찍어도 그게 어디인지는 안 알려준다.
경계를 따라 고르게 얇으면 마칭큐브가 등가면을 반 복셀 안쪽에 놓은 것이고,
한 군데 뭉쳐 있으면 깎기가 틀린 것이다. **숫자가 같아도 원인이 다르다.**

    검정  둘 다 있다
    빨강  원화엔 있는데 hull 이 못 덮었다   <- 이게 어떻게 생겼는지가 답이다
    파랑  hull 이 원화보다 더 나왔다
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def main():
    masks, mesh = H.main()
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)

    tiles = []
    for v in W.VIEWS:
        p = np.asarray(W.silhouette(V, F, v, H.BACK_SIGN if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        rgb = np.full(a.shape + (3,), 255, np.uint8)
        rgb[a & p] = (40, 40, 40)          # 둘 다
        rgb[a & ~p] = (220, 40, 40)        # 원화에만 — hull 이 못 덮은 자리
        rgb[~a & p] = (60, 110, 220)       # hull 에만
        tiles.append(rgb)

    sheet = np.concatenate(tiles, 1)
    Image.fromarray(sheet).resize((sheet.shape[1] // 3, sheet.shape[0] // 3)).save(
        os.path.join(OUT, "겹침.png"))
    print("-> out/겹침.png   (front · side · back / 빨강 = hull 이 못 덮은 자리)")


if __name__ == "__main__":
    main()
