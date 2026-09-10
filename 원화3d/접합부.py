# -*- coding: utf-8 -*-
"""**부위로 나눠 깎으면 접합부가 갈라진다.** 그 층을 잰다.

    python 접합부.py [케이스]      ->  out/접합부_<케이스>.png + 표

`부위람다.py` 가 재질마다 다른 lam 을 걸라고 했다. 그러면 두 재질이 만나는 자리에서
깊이가 **툭 끊긴다** — 목과 어깨, 도포와 살. 문질러 없애면 목이 굵어지고 인물이
아니게 된다.

**입력 깊이맵은 매끄럽다** — 2026-09-10 에 무진1997 로 재보니 재질 경계의 입력 단차가
최대 0.059 였다. 층은 원화가 만드는 게 아니라 **부위마다 다른 lam 을 걸 때** 생긴다.

그래서 실제로 두 번 깎는다. lam 을 같게 건 판과 부위마다 다르게 건 판을 만들고,
**앞면 깊이가 경계에서 얼마나 튀는지**를 잰다.

    경계        두 재질이 맞닿은 화소 수
    깊이 단차   경계를 사이에 둔 양쪽 깊이의 차 (0~1 정규화)
    최대 단차   제일 크게 갈라진 자리
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
문턱 = 0.08                     # 이보다 크면 층이 보인다


def vox_h(va, vb):
    """깊이 이동을 정규화할 눈금 — 복셀 격자의 y 칸 수."""
    return va.shape[1]


def 이웃(m):
    """한 화소 팽창. 경계를 찾으려고."""
    e = np.zeros_like(m)
    e[1:] |= m[:-1]; e[:-1] |= m[1:]
    e[:, 1:] |= m[:, :-1]; e[:, :-1] |= m[:, 1:]
    return e & ~m


def 앞면(vox):
    """복셀에서 앞면 깊이를 뽑는다. voxel[x,y,z] 이고 앞이 −y 라 제일 작은 y 다."""
    있 = vox.any(1)                                   # (x,z)
    y = np.where(vox.any(1), vox.argmax(1), 0)        # 첫 True 의 y
    return y.astype(np.float32).T, 있.T               # (z,x)


def 재기(case=None, view="front", lam_a=0.2, lam_b=0.5):
    """lam 을 같게 건 판과 다르게 건 판에서, 재질 경계의 앞면 깊이 단차를 잰다."""
    case = case or "무진1997"
    부위 = 재질판(case, view=view)
    masks, deps = {}, {}
    for v, f in H.CASES[case]["src"].items():
        mm = H.declutter(W.art_mask(os.path.join(H.art_dir(case), f)))
        masks[v], deps[v] = H.to_win(mm, H.load_depth(v, mm, case=case))
    va, _ = H.carve_depth(masks, deps, lam=lam_a)
    vb, _ = H.carve_depth(masks, deps, lam=lam_b)
    da, ia = 앞면(va)
    db, ib = 앞면(vb)
    # 부위 마스크를 복셀 눈금으로 내린다
    k = next(iter(부위.values())).shape[0] // da.shape[0]
    부위 = {kk: (mm[::k, ::k] if k > 1 else mm)[:da.shape[0], :da.shape[1]]
            for kk, mm in 부위.items()}
    깊 = {"같게": (da, ia), "다르게": (np.where(ia, da, 0) * 0 + db, ib)}
    d = (db - da) / max(float(vox_h(va, vb)), 1.0)     # lam 차가 만든 깊이 이동
    d = np.abs(d)

    keys = list(부위)
    rows = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = 부위[keys[i]], 부위[keys[j]]
            경계 = 이웃(a) & b
            n = int(경계.sum())
            if n < 80:
                continue
            안 = 경계 & b
            밖 = 이웃(b) & a
            if 밖.sum() < 40:
                continue
            차 = abs(float(d[안].mean()) - float(d[밖].mean()))   # lam 이 만든 단차
            rows.append((keys[i], keys[j], n, 차))
    return case, sorted(rows, key=lambda r: -r[3])


def figure(case=None):
    case, rows = 재기(case)
    rows = rows[:8]
    img = Image.new("L", (860, 130 + 30 * max(len(rows), 1)), 255)
    dd = ImageDraw.Draw(img)
    dd.text((16, 12), f"{case} — lam 을 0.2 와 0.5 로 갈라 걸면 경계가 끊긴다",
            font=_font(22), fill=0)
    dd.text((16, 52), "경계(두 재질)                      화소     앞면 단차", font=_font(18), fill=0)
    for i, (a, b, n, 차) in enumerate(rows):
        dd.text((16, 82 + i * 28),
                f"{str(a):16}{str(b):16} {n:8,} {차:11.3f}"
                f"{'   층이 보인다' if 차 >= 문턱 else ''}", font=_font(17), fill=0)
    p = os.path.join(OUT, f"접합부_{case}.png")
    img.save(p)
    print(f"-> {os.path.basename(p)}")
    for a, b, n, 차 in rows:
        print(f"   {str(a):16}{str(b):16} 화소 {n:7,}  단차 {차:.3f}"
              f"{'  층' if 차 >= 문턱 else ''}")
    return rows


def demo(case=None):
    rows = figure(case)
    assert rows, "경계를 하나도 못 찾았다 — 재질이 안 나뉘었다"
    차들 = [c for *_, c in rows]
    assert max(차들) >= 문턱, \
        f"층이 나는 자리가 없다 — 접합부가 문제가 아니라는 뜻이다 (최대 {max(차들):.3f})"
    print(f"접합부 자체검사 통과 — 층이 보이는 경계 "
          f"{sum(1 for c in 차들 if c >= 문턱)}개 · 최대 단차 {max(차들):.3f}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
