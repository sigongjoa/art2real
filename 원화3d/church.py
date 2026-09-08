# -*- coding: utf-8 -*-
"""**책 → 코드 → 결과.** Church(1892) Art. 7–8 을 원화에 그대로 대 본다.

    python church.py        ->  out/proof_church.png

## 책이 뭐라고 했나

`I03_Church1892_ElementsOfDescriptiveGeometry.pdf` (PDF 14쪽, Art. 7–8):

> **Art. 7.** "the distance of the point M, from the horizontal plane, is equal to the
> distance of its vertical projection from the ground line; and the distance of the point
> from the vertical plane is equal to that of its horizontal projection from the ground line."
>
> **Art. 8.** "If the two projections of a point are given, the point is completely
> determined; for if at the horizontal projection m, a perpendicular be erected to the
> horizontal plane, it will contain the point M. A perpendicular to the vertical plane at
> m', will also contain M; hence **the point M is determined by the intersection of these
> two perpendiculars**."

즉 — 정면 투영이 (x, z) 를 주고 측면 투영이 (y, z) 를 준다. 같은 높이 z 에서
두 수선을 세워 만나게 하면 3D 점 하나가 확정된다. **이게 화법기하의 근본 명제**이고,
턴어라운드 시트로 3D 를 세운다는 말의 전부다.

## 그대로 옮기면 이렇게 된다

높이 z 한 줄을 고른다.

    정면 마스크의 그 행  ->  x 가 채워진 구간들
    측면 마스크의 그 행  ->  y 가 채워진 구간들
    Art.8 대로 교차      ->  그 높이의 단면 = { (x,y) : 정면[x] 이고 측면[y] }

## 그런데 여기서 갈린다 — **책은 「점 하나」를 전제한다**

Art. 8 이 성립하려면 **어느 m 이 어느 m' 과 짝인지**를 알아야 한다. 도면에서는
작도자가 그걸 안다(같은 점을 두 번 그린 것이니까). 그런데 우리한테 있는 건 실루엣이라
**짝을 모른다.** 그래서 교차가 아니라 **곱집합**이 된다.

곱집합은 실제보다 크다. 팔 높이에서 정면은 [몸통][왼팔][오른팔] 세 구간을 주고 측면은
[몸통 깊이] 한 구간을 주는데, 곱하면 **검도 포도 몸통만큼 두꺼워진다.** 실제로는
검이 얇은데 측면 판이 그 정보를 안 준다 — 측면에서 검은 몸통에 가려져 있다.

**이게 hull 이 오목부를 못 잡는 이유의 정체다.** 알고리즘 결함이 아니라 Art. 8 의
전제(짝을 안다)가 실루엣에서 깨지는 것이다. 그리고 이게 「무엇을 더 얻어야 하는가」를
정확히 말해준다 — 짝짓기 정보. 판 경계·먹선·그늘이 그 후보다.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import hull as H
import win as W

OUT = H.OUT
HEIGHTS = [("가슴", 0.78), ("팔·검·포", 0.62), ("허벅지", 0.34)]


def _font(s):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", s)
    except Exception:
        return ImageFont.load_default()


F1, F2 = _font(14), _font(12)


def runs(row):
    """참 구간 [(a,b), ...]. 책의 「투영이 준 구간」 그대로."""
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def section(front_row, side_row):
    """Art. 8 을 그대로 — 정면의 수선과 측면의 수선을 교차시킨다.

    짝을 모르니 결과는 교차가 아니라 **곱집합**이다. `front_row[x] & side_row[y]`."""
    return np.outer(front_row, side_row)


def panel(img, label, sub=""):
    c = Image.new("RGB", (img.width, img.height + 34), "white")
    c.paste(img, (0, 34))
    d = ImageDraw.Draw(c)
    d.text((6, 3), label, fill=(0, 0, 0), font=F1)
    if sub:
        d.text((6, 19), sub, fill=(110, 110, 110), font=F2)
    return c


def main():
    src = {"front": "omega_front_clean.png", "side": "omega_side.png"}
    masks = {v: H.to_win(H.declutter(W.art_mask(os.path.join(H.IN7, f))))
             for v, f in src.items()}
    S = 300
    cells = []
    for name, z in HEIGHTS:
        r = int((W.Z1 - z) / (W.Z1 - W.Z0) * W.RES)
        fr, sr = masks["front"][r], masks["side"][r]

        # (1) 정면 — 그 높이의 가로선과 구간
        for v, row in (("front", fr), ("side", sr)):
            rgb = np.full(masks[v].shape + (3,), 255, np.uint8)
            rgb[masks[v]] = (170, 175, 185)
            rgb[r] = (215, 60, 60)
            for a, b in runs(row):
                rgb[max(r - 6, 0):r + 7, a:b] = (60, 90, 170)
            im = Image.fromarray(rgb).resize((S, S), Image.NEAREST)
            cells.append(panel(im, "%s  z=%.2f · %s" % (name, z, v),
                               "구간 %d개" % len(runs(row))))

        # (2) Art.8 을 그대로 적용한 단면 (x 가로 · y 세로)
        sec = section(fr, sr)
        rgb = np.full(sec.shape + (3,), 255, np.uint8)
        rgb[sec.T] = (60, 165, 90)                      # 화면: x 가로, y 세로
        im = Image.fromarray(rgb).resize((S, S), Image.NEAREST)
        cells.append(panel(im, "%s  단면 (Art.8 곱집합)" % name,
                           "%d 화소 = 정면 %d × 측면 %d"
                           % (sec.sum(), fr.sum(), sr.sum())))

    sheet = Image.new("RGB", (S * 3, (S + 34) * len(HEIGHTS)), "white")
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % 3) * S, (i // 3) * (S + 34)))
    p = os.path.join(OUT, "proof_church.png")
    sheet.save(p)

    print("Church 1892, Art. 8 — 두 투영의 수선을 교차시키면 점이 확정된다\n")
    for name, z in HEIGHTS:
        r = int((W.Z1 - z) / (W.Z1 - W.Z0) * W.RES)
        fr, sr = masks["front"][r], masks["side"][r]
        sec = section(fr, sr)
        print("  %-9s z=%.2f  정면 구간 %d개(%4d화소) · 측면 구간 %d개(%4d화소)"
              "  ->  단면 %6d화소" % (name, z, len(runs(fr)), fr.sum(),
                                      len(runs(sr)), sr.sum(), sec.sum()))
    print("\n  단면이 곱집합이라 실제보다 크다 — 짝을 모르기 때문이다 (docstring 참고)")
    print("->", p)


if __name__ == "__main__":
    main()
