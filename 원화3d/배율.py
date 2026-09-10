# -*- coding: utf-8 -*-
"""**bbox 로 재면 판마다 다른 배율로 앉는다.** 그 몫을 잰다.

    python 배율.py [케이스]      ->  out/배율_<케이스>.png + 표

판마다 튀어나온 게 다르다 — 정면은 칼끝이 옆으로, 측면은 묶은 머리가 뒤로. 그래서
bbox 를 자로 쓰면 같은 인물이 판마다 다른 크기로 앉는다. `win.normalize` 가 **높이**로
한 번만 재는 이유가 이것인데, 그 이유가 숫자로 적힌 적이 없었다.

세 가지를 나란히 잰다.

    bbox 가로   판마다 얼마나 다른가            <- 칼끝·머리카락이 정하는 값
    bbox 세로   판마다 얼마나 다른가            <- 인물의 키에 가깝다
    가로로 정규화했을 때 판별 배율의 흩어짐      <- 이게 크면 bbox 를 자로 쓰면 안 된다
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


def bbox(m):
    ys, xs = np.where(m)
    return int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def measure(case=None):
    src = H.CASES[case]["src"] if case else \
        {"front": "omega_front_clean.png", "side": "omega_side.png", "back": "omega_back.png"}
    base = H.art_dir(case) if case else H.IN7
    r = {}
    for v, f in src.items():
        m = H.declutter(W.art_mask(os.path.join(base, f)))
        w, h = bbox(m)
        r[v] = {"가로": w, "세로": h, "화소": int(m.sum())}
    ws = [r[v]["가로"] for v in W.VIEWS]
    hs = [r[v]["세로"] for v in W.VIEWS]
    r["_"] = {
        "가로흩어짐": max(ws) / min(ws),      # 가로로 정규화하면 이만큼 다른 배율로 앉는다
        "세로흩어짐": max(hs) / min(hs),      # 높이로 재면 이만큼만 다르다
    }
    return r


def figure(case=None):
    r = measure(case)
    img = Image.new("L", (760, 210), 255)
    d = ImageDraw.Draw(img)
    d.text((16, 12), f"{case or '오메가몬'} — 판마다 bbox 가 다르다", font=_font(22), fill=0)
    d.text((16, 48), "판       bbox 가로   bbox 세로   전경 화소", font=_font(18), fill=0)
    for i, v in enumerate(W.VIEWS):
        a = r[v]
        d.text((16, 76 + i * 26),
               f"{v:6} {a['가로']:9,} {a['세로']:11,} {a['화소']:13,}", font=_font(18), fill=0)
    g = r["_"]
    d.text((16, 160), f"가로로 정규화하면 배율이 {g['가로흩어짐']:.3f} 배까지 벌어진다",
           font=_font(19), fill=0)
    d.text((16, 184), f"높이로 재면 {g['세로흩어짐']:.3f} 배 — 그래서 win.normalize 는 높이다",
           font=_font(19), fill=0)
    p = os.path.join(OUT, f"배율_{case}.png" if case else "배율.png")
    img.save(p)
    print(f"-> {os.path.relpath(p, os.path.dirname(p))}  "
          f"가로흩어짐 {g['가로흩어짐']:.3f} · 세로흩어짐 {g['세로흩어짐']:.3f}")
    return r


def demo(case=None):
    # 케이스를 안 주면 오메가몬을 잰다. 2026-09-10 에 `--자체검사` 만 주고 돌렸다가
    # **오메가몬 값(2.540)을 무진 값으로 착각해 대본에 넣었다.** 그래서 기본을 못 박는다.
    case = case or "무진1997"
    r = figure(case)
    g = r["_"]
    assert g["가로흩어짐"] > g["세로흩어짐"], \
        f"가로가 세로보다 안 벌어졌다 — 2화의 벽이 안 선다 ({g})"
    print("배율 자체검사 통과 — bbox 가로는 자로 못 쓴다")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
