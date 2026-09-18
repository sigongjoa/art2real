# -*- coding: utf-8 -*-
"""**보충 입력 측정 (연구 루프 1)** — 보충이 무엇이고 얼마나 되돌리나 (2026-09-18).

    python 보충입력.py [n]   -> out/기록/보충입력.json

0 문제 (`out/기록/불리언_20260918_1532.json`): 불리언∩hull 거칠기 0.109 인데 **보충을 붙이면 0.165** 다.
보충 패치만 복셀(마칭큐브)이라 계단이 부분적으로 돌아온다. 방법을 탓하기 전에 입력부터 —
보충이 **얼마나 크고 어디에 붙나**.

    부피몫      보충 칸 / 최종 칸
    표면몫      보충이 만든 표면 칸 / 최종 표면 칸   ← 거칠기에 들어가는 것은 이쪽이다
    빈자리      원화 실루엣 중 불리언 투영이 못 덮은 화소 몫 (시점별)
    덩이        보충 패치가 몇 덩어리로 흩어지나
"""
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 표면 as SF
from 겉면채점 import bench_cases
from 생성깎기 import build as gen_build, voxelize, fill_gaps
from 불리언 import boolean_hull, fitted

OUTJ = os.path.join(HERE, "out", "기록", "보충입력.json")


def surface(vox):
    """표면 칸 — 6이웃에 빈 칸이 있는 켜진 칸."""
    p = np.pad(vox, 1)
    nb = (p[:-2, 1:-1, 1:-1] & p[2:, 1:-1, 1:-1] & p[1:-1, :-2, 1:-1] &
          p[1:-1, 2:, 1:-1] & p[1:-1, 1:-1, :-2] & p[1:-1, 1:-1, 2:])
    return vox & ~nb


def one(case):
    t0 = time.time()
    masks, bs, plain, base, axes = gen_build(case)
    gen = fitted(case, masks)
    vox = voxelize(gen, axes) & plain
    m_bool = boolean_hull(gen, masks, bs)
    vb = voxelize(m_bool, axes)
    patch = fill_gaps(vox, base, plain) & ~vox
    final = vb | patch
    sf, sp = surface(final), surface(final) & patch
    # 빈 자리 — 원화 실루엣 중 불리언 투영이 못 덮은 몫
    비 = {}
    for v, ax in (("front", 1), ("side", 0)):
        proj = vb.any(ax)
        g = np.zeros((W.RES, W.RES), np.uint8)
        a, b = np.nonzero(proj)
        u, z = axes[0], axes[2]
        py, px = W.topix(W.VIEW_AXIS[v][1] * u[a], z[b])
        g[py, px] = 1
        s = cv2.dilate(g, np.ones((5, 5), np.uint8)).astype(bool)
        m = masks[v]
        비[v] = round(float((m & ~s).sum() / max(m.sum(), 1)), 4)
    from scipy import ndimage
    lab, n = ndimage.label(patch, structure=np.ones((3, 3, 3)))
    big = int((np.bincount(lab.ravel())[1:] >= 50).sum()) if n else 0
    return {"case": case,
            "부피몫": round(float(patch.sum() / max(final.sum(), 1)), 4),
            "표면몫": round(float(sp.sum() / max(sf.sum(), 1)), 4),
            "빈자리": 비, "덩이": big, "초": round(time.time() - t0, 1)}


def main():
    H.register_sheets()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    old = json.load(open(OUTJ, encoding="utf-8")) if os.path.exists(OUTJ) else {}
    todo = [c for c in bench_cases() if c != "소체" and c not in old][:n]
    for c in todo:
        r = one(c)
        old[c] = r
        json.dump(old, open(OUTJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  %-30s 부피 %.3f · 표면 %.3f · 빈자리 f %.3f s %.3f · 덩이 %d · %.0f초"
              % (c, r["부피몫"], r["표면몫"], r["빈자리"]["front"], r["빈자리"]["side"], r["덩이"], r["초"]), flush=True)
    if old:
        f = lambda k: float(np.median([v[k] for v in old.values()]))
        print("  중앙 (%d장) 부피 %.3f · 표면 %.3f · 덩이 %.0f"
              % (len(old), f("부피몫"), f("표면몫"), f("덩이")))


if __name__ == "__main__":
    main()
