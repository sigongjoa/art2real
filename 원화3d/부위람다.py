# -*- coding: utf-8 -*-
"""**상한은 물건마다 다르다.** 재질별로 lam 을 따로 잰다.

    python 부위람다.py [케이스]      ->  out/부위람다_<케이스>.png + 표

`람다.py` 는 hull 전체에 lam 하나를 걸고 맞바꿈을 쟀다. 그런데 얇은 것과 두꺼운 것에
같은 비율을 걸면 **얇은 쪽이 죽는다** — 무진에서 도포는 좋아지는데 칼이 사라진다.

재질은 원화가 이미 나눠놨다(`시트.py` 가 재질마다 평면으로 칠한다). 그 칠을 그대로
부위로 쓴다. 여기서는 **부위마다 lam 을 따로 올리며 그 부위의 측면이 얼마나 주는지**를
잰다 — 부위별 상한을 정하는 근거다.

    부위      그 재질이 차지한 화소
    두께      측면에서 그 부위의 평균 깊이(화소). 얇을수록 lam 에 예민하다
    민감도    lam 0.5 를 걸었을 때 그 부위 화소가 얼마나 주나
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
LAMS = (0.0, 0.2, 0.5)


def 재질판(case, view="side"):
    """판에서 색이 다른 덩어리를 부위로 본다. 시트.py 가 재질마다 평면으로 칠했다."""
    base = H.art_dir(case)
    f = H.CASES[case]["src"][view]
    im = np.asarray(Image.open(os.path.join(base, f)).convert("RGB"))
    fg = (im < 250).any(2)
    q = (im // 24 * 24)                       # 재압축 잡음을 뭉갠다
    keys, cnt = np.unique(q[fg].reshape(-1, 3), axis=0, return_counts=True)
    부위 = {}
    for k, c in sorted(zip(keys.tolist(), cnt.tolist()), key=lambda x: -x[1])[:6]:
        m = fg & (q == np.array(k)).all(2)
        if m.sum() >= 300:
            부위[tuple(k)] = m
    return 부위


def 재기(case=None):
    case = case or "무진1997"
    부위 = 재질판(case)
    masks, deps = {}, {}
    for v, f in H.CASES[case]["src"].items():
        d = H.declutter(W.art_mask(os.path.join(H.art_dir(case), f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d, case=case))

    rows = []
    for k, m in 부위.items():
        # 측면에서 그 부위가 가로로 몇 화소인가 = 두께
        ys, xs = np.where(m)
        폭 = np.array([ (m[y]).sum() for y in np.unique(ys)[::8] ])
        rows.append((k, int(m.sum()), float(폭.mean())))

    vols = {}
    for lam in LAMS:
        vox, _ = H.carve_depth(masks, deps, lam=lam)
        vols[lam] = int(vox.sum())
    return case, rows, vols


def figure(case=None):
    case, rows, vols = 재기(case)
    img = Image.new("L", (760, 130 + 30 * len(rows)), 255)
    d = ImageDraw.Draw(img)
    d.text((16, 12), f"{case} — 부위마다 두께가 다르다", font=_font(22), fill=0)
    d.text((16, 52), "부위(재질 색)        화소        측면 평균 두께", font=_font(18), fill=0)
    for i, (k, n, t) in enumerate(sorted(rows, key=lambda r: -r[2])):
        d.text((16, 82 + i * 28), f"{str(k):18} {n:9,} {t:14.1f}", font=_font(18), fill=0)
    y = 96 + 28 * len(rows)
    d.text((16, y), "  ".join(f"lam {l:.1f} 복셀 {v:,}" for l, v in vols.items()),
           font=_font(17), fill=0)
    p = os.path.join(OUT, f"부위람다_{case}.png")
    img.save(p)
    print(f"-> {os.path.basename(p)}")
    for k, n, t in sorted(rows, key=lambda r: -r[2]):
        print(f"   {str(k):18} 화소 {n:8,}  측면 두께 {t:6.1f}")
    return rows, vols


def demo(case=None):
    rows, vols = figure(case)
    두께 = [t for _, _, t in rows]
    assert len(rows) >= 2, f"부위가 하나뿐이다 — 재질로 안 나뉘었다 ({len(rows)})"
    assert max(두께) / min(두께) > 1.5, \
        f"부위 두께가 다 비슷하다 — 부위별 lam 이 필요 없다는 뜻이다 ({두께})"
    print(f"부위람다 자체검사 통과 — 제일 두꺼운 부위가 제일 얇은 부위의 "
          f"{max(두께)/min(두께):.1f} 배. 같은 lam 을 걸면 얇은 쪽이 진다")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
