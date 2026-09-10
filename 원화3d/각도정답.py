# -*- coding: utf-8 -*-
"""**아무도 안 그린 각도에서 진짜와 대본다.**

    python 각도정답.py [케이스]      ->  out/각도정답_<케이스>.png + 표

`정답.py` 는 front·side·back 세 시점만 잰다. 그런데 세 판이 맞는 건 당연하다 — hull 이
그 세 판에서 나왔다. **판정은 판이 없는 각도에서 해야 한다.**

「야도」 1권 표지가 45도다. 20년 동안 팬이 제일 많이 그린 컷이 하필 아무도 판을 안
그린 각도다. 그래서 2권의 마지막 숫자가 이것이다.

    hull 을 az 만큼 돌린 실루엣  대  진짜 메시를 같은 각도로 돌린 실루엣
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import rotate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 계획 import _font
import 정답 as G

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
AZ = (0, 25, 45, 65, 90)


def iou(a, b):
    return float((a & b).sum()) / max(int((a | b).sum()), 1)


def 재기(case=None):
    case = case or "무진1997"
    A, B, out, sil = G.score(case)
    rows = []
    for az in AZ:
        if az == 0:
            ra, rb = A, B
        else:
            # x·y 평면에서 돌린다. order=0 이라 이진이 유지된다.
            ra = rotate(A.astype(np.uint8), az, axes=(0, 1), order=0, reshape=True) > 0
            rb = rotate(B.astype(np.uint8), az, axes=(0, 1), order=0, reshape=True) > 0
            n = [max(x, y) for x, y in zip(ra.shape, rb.shape)]
            pa = np.zeros(n, bool); pa[:ra.shape[0], :ra.shape[1], :ra.shape[2]] = ra
            pb = np.zeros(n, bool); pb[:rb.shape[0], :rb.shape[1], :rb.shape[2]] = rb
            ra, rb = pa, pb
        rows.append((az, iou(ra.any(1), rb.any(1))))
    return case, rows, out


def figure(case=None):
    case, rows, out = 재기(case)
    img = Image.new("L", (640, 150 + 30 * len(rows)), 255)
    d = ImageDraw.Draw(img)
    d.text((16, 12), f"{case} — 판이 없는 각도에서 진짜와 대본다", font=_font(22), fill=0)
    d.text((16, 52), "각도        실루엣 IoU", font=_font(18), fill=0)
    for i, (az, v) in enumerate(rows):
        표 = "   (판이 있다)" if az in (0, 90) else ""
        d.text((16, 82 + i * 28), f"{az:3}°  {v:14.3f}{표}", font=_font(18), fill=0)
    d.text((16, 96 + 28 * len(rows)),
           f"3D IoU {out['3D IoU']:.3f} · 부피비 {out['부피비']:.3f}", font=_font(17), fill=0)
    p = os.path.join(OUT, f"각도정답_{case}.png")
    img.save(p)
    print(f"-> {os.path.basename(p)}")
    for az, v in rows:
        print(f"   {az:3}°  실루엣 IoU {v:.3f}" + ("   (판이 있다)" if az in (0, 90) else ""))
    return rows, out


def demo(case=None):
    """**판이 있다고 맞는 게 아니다.** 2026-09-10 무진1997 에서 그게 나왔다.

    앞판(0°)은 0.929 로 제일 좋은데 옆판(90°)은 0.757 이라, 판이 하나도 없는
    25°(0.782)보다 나쁘다. 옆판은 하청의 **다른 사람이 눈으로 그린 판**이다
    (하청시트.py 가 옆면을 변주 0.6 에서 가져온다). 그래서 기준이 바뀐다 —
    판이 있느냐가 아니라 **그 판이 맞느냐**다.
    """
    rows, out = figure(case)
    d = dict(rows)
    assert d[0] > max(v for az, v in rows if az != 0), (
        f"앞판 각도가 제일 안 맞는다 — 뭔가 뒤집혔다 ({rows})")
    assert d[90] < d[25], (
        f"옆판이 판 없는 25도보다 잘 맞는다 — 이 케이스의 전제가 깨졌다 ({rows})")
    print(f"각도정답 자체검사 통과 — 앞판 {d[0]:.3f} · 표지 45° {d[45]:.3f} · "
          f"옆판 {d[90]:.3f} < 25° {d[25]:.3f}")
    print("   **판이 있다고 맞는 게 아니다. 그 판이 맞아야 맞는다**")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    (demo if "--자체검사" in sys.argv else figure)(a[0] if a else None)
