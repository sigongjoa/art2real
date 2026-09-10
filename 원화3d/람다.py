# -*- coding: utf-8 -*-
"""**깎을수록 45도는 좋아지고 측면은 나빠진다.** 그 맞바꿈을 잰다.

    python 람다.py [케이스]      ->  out/람다_<케이스>.png + 표

`hull.LAM` 은 부조가 쓰는 기둥 깊이 비율이다. 0 이면 이진 hull(순수 상자)이고, 올릴수록
앞뒤를 깊이맵으로 깎아 45도에서 덩어리가 형태로 바뀐다. 그런데 깎으면 **측면 실루엣이
줄어든다** — 그리고 측면은 취향이 아니라 데이터다.

**「안 싸우는 최대」는 없었다.** 2026-09-10 에 무진1997 로 재보니 lam 을 올릴수록 측면
IoU 가 조금씩 계속 준다 — 공짜인 구간이 없다. 그래서 이 표가 하는 일은 최대를 찾는 게
아니라 **얼마를 내주고 얼마를 사는지**를 적는 것이다.

    단면 형태값   0 이면 순수 상자. 클수록 45도가 형태다
    측면 못 덮음   측면 원화를 hull 이 못 덮은 비율. 커지면 데이터와 싸운 것이다
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
LAMS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)


def load(case=None):
    src = H.CASES[case]["src"] if case else \
        {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}
    base = H.art_dir(case) if case else H.IN7
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d, case=case))
    p = H.align(masks)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    return masks, deps


def sweep(case=None):
    masks, deps = load(case)
    rows = []
    for lam in LAMS:
        vox, _ = H.carve_depth(masks, deps, lam=lam)
        # voxel[x,y,z] = F[z,x] & B[z,x] & S[z,y] 이므로 되던진 실루엣은 이렇게 나온다.
        side = vox.any(0).T                       # (z,y) — 측면
        # 복셀은 256³ 이고 원화 마스크는 1024² 다. 눈금을 맞춘다 — 4칸마다 하나.
        # ponytail: 단순 솎아내기다. 경계 한 화소가 중요해지면 블록 최댓값으로.
        k = masks["side"].shape[0] // side.shape[0]
        m = masks["side"][::k, ::k] if k > 1 else masks["side"]
        miss = float((m & ~side).sum()) / max(int(m.sum()), 1)
        rows.append((lam, H.box_score(vox), int(vox.sum()), miss, W.iou(m, side)))
    return rows


def figure(case=None):
    rows = sweep(case)
    img = Image.new("L", (860, 118 + 30 * len(rows)), 255)
    d = ImageDraw.Draw(img)
    d.text((16, 12), f"{case or '오메가몬'} — 깎을수록 45도는 형태가 되고 측면은 줄어든다",
           font=_font(22), fill=0)
    d.text((16, 52), "lam    단면 형태값     측면 못 덮음     측면 IoU", font=_font(18), fill=0)
    for i, (lam, box, vol, miss, iou) in enumerate(rows):
        d.text((16, 82 + i * 28),
               f"{lam:.1f} {box:13.2f} {100*miss:14.2f}% {iou:13.3f}", font=_font(18), fill=0)
    p = os.path.join(OUT, f"람다_{case}.png" if case else "람다.png")
    img.save(p)
    print(f"-> {os.path.basename(p)}")
    for lam, box, vol, miss, iou in rows:
        print(f"   lam {lam:.1f}  형태값 {box:.2f}  측면 못 덮음 {100*miss:.2f}%  측면 IoU {iou:.3f}")
    return rows


def demo(case=None):
    case = case or "무진1997"
    rows = figure(case)
    boxes = [r[1] for r in rows]
    ious = [r[4] for r in rows]
    assert boxes[0] < boxes[-1], f"lam 을 올려도 형태값이 안 는다 — {boxes}"
    assert ious[0] >= ious[-1], f"깎았는데 측면이 안 줄었다 — 맞바꿈이 없다 ({ious})"
    # 「안 싸우는 최대」는 없다. 조금씩 계속 준다 — 공짜가 없다는 게 이 표의 답이다.
    쓰는값 = H.LAM
    a = next(r for r in rows if abs(r[0] - 쓰는값) < 1e-6)
    print(f"람다 자체검사 통과 — 쓰는 lam {쓰는값:.2f} 는 측면 IoU "
          f"{ious[0]:.3f}→{a[4]:.3f}({ious[0]-a[4]:+.3f}) 를 내주고 형태값 {a[1]:.2f} 를 산다")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
