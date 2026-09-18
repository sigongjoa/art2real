# -*- coding: utf-8 -*-
"""장별 접촉지 — 복셀로 깎은 것 대 불리언으로 깎은 것 (2026-09-18).

    python 불리언장별.py 타일 [n]   아직 안 그린 장 n 개를 out/불리언타일/<케이스>.png 로
    python 불리언장별.py 모으기      타일을 한 장으로 -> out/불리언_장별.png

**타일을 케이스마다 파일로 떨군다** — 무거운 장에서 끊겨도 이어서 그린다 (메모리 압박으로 두 번 죽었다).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import 대조 as C
import 앨리어싱 as AL
from 계획 import _font
from 폴리싱 import shaded
from 불리언 import boolean_hull, fitted, gen_build, voxelize, fill_gaps, union_patch, rows

TILE = os.path.join(HERE, "out", "불리언타일")
S = 300


def one(case):
    masks, bs, plain, base, axes = gen_build(case)
    gen = fitted(case, masks)
    vox = voxelize(gen, axes) & plain
    m_bool = boolean_hull(gen, masks, bs)
    patch = fill_gaps(vox, base, plain) & ~vox
    a = C.to_mesh(vox | patch, axes)                       # 복셀+보충 (지금 배포 팔)
    b = union_patch(m_bool, patch, axes)                   # 불리언+보충 (제안)
    fr = AL.frame_of(a, 45)
    im = Image.new("RGB", (2 * S + 6, S), "white")
    for j, m in enumerate((a, b)):
        t = shaded(m, 45, fr, S)
        im.paste(Image.fromarray(np.asarray(t)[:, :, ::-1] if t.ndim == 3 else t), (j * (S + 6), 0))
    im.save(os.path.join(TILE, "%s.png" % case))


def 타일(n):
    os.makedirs(TILE, exist_ok=True)
    H.register_sheets()
    todo = [c for c in rows() if not os.path.exists(os.path.join(TILE, "%s.png" % c))][:n]
    for c in todo:
        one(c)
        print("  %s" % c, flush=True)


def 모으기():
    rs = rows()
    cases = [c for c in rs if os.path.exists(os.path.join(TILE, "%s.png" % c))]
    cases.sort(key=lambda c: -(rs[c]["복셀+보충"]["거칠기"] - rs[c]["불리언+보충"]["거칠기"]))
    COLS, TOP = 3, 150
    W = 30 + COLS * (2 * S + 6 + 16)
    im = Image.new("RGB", (W, TOP + ((len(cases) + COLS - 1) // COLS) * (S + 54) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "복셀로 깎기(왼) 대 메시 불리언으로 깎기(오른) — %d장" % len(cases), font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "둘 다 「생성∩hull+보충」 이다. 같은 생성 메시 · 같은 원화 3판 · 같은 틀 · 면 법선 명암.",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "숫자 = 거칠기 (격자 한 칸 거리에서 법선이 30° 넘게 꺾인 이웃 쌍의 비율 · 낮을수록 매끈)",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 106), "거칠기가 많이 준 장부터", font=_font(16), fill=(120, 120, 120))
    for i, c in enumerate(cases):
        r, q = divmod(i, COLS)
        x, y = 30 + q * (2 * S + 6 + 16), TOP + r * (S + 54)
        im.paste(Image.open(os.path.join(TILE, "%s.png" % c)), (x, y))
        d.text((x + 2, y + S + 2), c[:38], font=_font(15), fill=(40, 40, 40))
        d.text((x + 2, y + S + 22), "거칠기 %.3f  ->  %.3f      IoU %.3f -> %.3f"
               % (rs[c]["복셀+보충"]["거칠기"], rs[c]["불리언+보충"]["거칠기"],
                  rs[c]["복셀+보충"]["iou"], rs[c]["불리언+보충"]["iou"]), font=_font(15), fill=(110, 110, 110))
    p = os.path.join(HERE, "out", "불리언_장별.png")
    im.save(p)
    print("  -> %s (%d장)" % (p, len(cases)))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "타일"
    if a == "모으기":
        모으기()
    else:
        타일(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
