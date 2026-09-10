# -*- coding: utf-8 -*-
"""**hull 의 입력은 그림이 아니라 이진 마스크다.** 그 마스크가 임계값에 따라 얼마나
달라지는지를 잰다.

    python 임계값.py [케이스]     ->  out/임계값.png

원화가 깨끗한 PNG 면 임계값을 옮겨도 실루엣이 거의 안 바뀐다. 그런데 팬들 사이에 도는
자료는 스캔을 다시 압축한 것이라 경계에 링잉이 낀다. 그 상태에서는 **한 칸 옮길 때마다
다른 물건이 들어온다** — hull 이 아무리 정확해도 입력이 흔들리면 소용이 없다.

여기서 재압축을 흉내내는 게 아니라 **실제로 JPEG 로 다시 굽는다**(q=25). 그리고 세
임계값에서 나온 마스크의 화소 수와 서로 간 IoU 를 찍는다.
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import win as W
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
CUTS = (200, 235, 250)      # 이 밝기보다 어두우면 전경. art_mask 의 기본은 250
QUALITY = 25                # 재업로드본이 겪은 만큼


def recompress(png, quality=QUALITY):
    """PNG → JPEG(q) → 회색 배열. 경계에 링잉이 실제로 생긴다."""
    im = Image.open(png).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    return np.asarray(Image.open(buf).convert("L"))


def figure(case="소체"):
    src = os.path.join(OUT, "시트", case, "front.png")
    assert os.path.exists(src), f"판이 없다: {src}"
    g = recompress(src)
    masks = [g < c for c in CUTS]

    th, pad, lab = 420, 16, 78
    w = pad + len(masks)*(th+pad)
    img = Image.new("L", (w, lab + th + pad + 34), 255)
    d = ImageDraw.Draw(img)
    d.text((pad, 10), f"같은 판 · JPEG q{QUALITY} 로 다시 구운 뒤 임계값만 바꿨다",
           font=_font(22), fill=0)
    for i, (c, m) in enumerate(zip(CUTS, masks)):
        tile = Image.fromarray(np.where(m, 0, 255).astype(np.uint8)).resize(
            (th, th), Image.NEAREST)
        x = pad + i*(th+pad)
        img.paste(tile, (x, lab))
        d.rectangle([x, lab, x+th-1, lab+th-1], outline=0)
        d.text((x, lab-30), f"임계값 {c}   {int(m.sum()):,} 화소", font=_font(20), fill=0)
    ious = [W.iou(masks[i], masks[i+1]) for i in range(len(masks)-1)]
    d.text((pad, lab+th+8),
           "이웃한 두 장 IoU  " + " · ".join(f"{v:.3f}" for v in ious),
           font=_font(20), fill=0)

    p = os.path.join(OUT, "임계값.png")
    img.save(p)
    print(f"-> out/임계값.png   화소 {[int(m.sum()) for m in masks]}  IoU {[round(v,3) for v in ious]}")
    return masks, ious


def demo():
    """임계값을 옮기면 마스크가 실제로 달라지는가. 안 달라지면 이 그림은 거짓말이다."""
    masks, ious = figure()
    assert all(i < 0.999 for i in ious), f"임계값이 마스크를 안 바꿨다 — {ious}"
    counts = [int(m.sum()) for m in masks]
    assert counts == sorted(counts), f"임계값이 높을수록 전경이 넓어야 한다 — {counts}"
    print("임계값 자체검사 통과")


if __name__ == "__main__":
    if "--자체검사" in sys.argv:
        demo()
    else:
        figure(sys.argv[1] if len(sys.argv) > 1 else "소체")
