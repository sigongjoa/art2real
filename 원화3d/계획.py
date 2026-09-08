# -*- coding: utf-8 -*-
"""**하려는 것 한 장.** 실제 데이터로 그린다. 개념도가 아니다.

    python 계획.py        ->  out/계획.png

칸마다 진짜 그림이 들어간다. 다만 마지막 칸은 **아직 안 해본 것**이라 비워 둔다 —
거기 무엇이 들어오는지가 이 계획의 전부다.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
TH = 190                                            # 썸네일 한 변


def _font(sz):
    for p in (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\NanumGothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def thumb(a, rgb=None):
    """bool 마스크 또는 RGB 배열 -> 썸네일."""
    if rgb is None:
        rgb = np.where(a[..., None], np.uint8([40, 40, 40]), np.uint8([255, 255, 255]))
    return Image.fromarray(rgb.astype(np.uint8)).resize((TH, TH), Image.NEAREST)


def main():
    masks, mesh = H.main()
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)

    raw = {v: W.art_mask(os.path.join(H.IN7, f)) for v, f in
           {"front": "omega_front_clean.png", "side": "omega_side.png",
            "back": "omega_back.png"}.items()}

    ov = {}
    for v in W.VIEWS:
        p = np.asarray(W.silhouette(V, F, v, H.BACK_SIGN if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        g = np.full(a.shape + (3,), 255, np.uint8)
        g[a & p] = (40, 40, 40); g[a & ~p] = (220, 40, 40); g[~a & p] = (60, 110, 220)
        ov[v] = g

    Wd, Ht = 2000, 640
    sheet = Image.new("RGB", (Wd, Ht), "white")
    d = ImageDraw.Draw(sheet)
    f14, f12, f20 = _font(15), _font(13), _font(21)

    d.text((28, 22), "지금 파이프라인과, 바꾸려는 칸 하나", font=f20, fill=(20, 20, 20))

    cols = [
        ("① 원화 3판  (측면의 가로줄이 지시선이다)", [raw[v] for v in W.VIEWS], None,
         "그려진 키 924 · 892 · 894\n판마다 3.6% 다르다"),
        ("② 창에 앉힌다", [masks[v] for v in W.VIEWS], None,
         "지금: 판마다 자기 키로 늘림\n자유도 0"),
        ("③ 깎고 되던진다", None, [ov[v] for v in W.VIEWS],
         "빨강 = hull 이 못 덮은 자리\n5.24 · 1.03 · 6.87%"),
    ]

    x = 28
    for title, ms, rgbs, cap in cols:
        d.text((x, 66), title, font=f14, fill=(20, 20, 20))
        for i in range(3):
            im = thumb(ms[i]) if rgbs is None else thumb(None, rgbs[i])
            sheet.paste(im, (x + i * (TH + 6), 92))
        d.multiline_text((x, 300), cap, font=f12, fill=(90, 90, 90), spacing=5)
        x += 3 * (TH + 6) + 46
        if x < Wd - 260:
            d.text((x - 36, 170), "→", font=f20, fill=(150, 150, 150))

    # ── 바꾸려는 칸 ──────────────────────────────────────────────
    bx, by = 28, 372
    d.rectangle([bx, by, Wd - 28, Ht - 26], outline=(200, 60, 60), width=2)
    d.text((bx + 18, by + 14), "바꾸려는 것은 ② 한 칸이다", font=f14, fill=(200, 60, 60))
    d.multiline_text(
        (bx + 18, by + 44),
        "지금   판마다 자기 bbox 키를 1.0 으로 늘린다. 미지수 0개.\n"
        "       판이 안 맞으면 그 어긋남이 전부 형태로 흘러간다 — 그게 잘린 발이다.\n\n"
        "바꾸면 front 를 기준으로 고정하고, side·back 에 (가로 이동 · 세로 이동 · 배율) 을 준다.\n"
        "       미지수 6개. 겹침이 제일 좋아지는 값을 찾는다. warp_art() 가 이미 win.py 에 있다.",
        font=f12, fill=(70, 70, 70), spacing=6)

    d.multiline_text(
        (Wd - 470, by + 44),
        "그리고 ③ 을 다시 뽑는다\n\n"
        "  빨강이 줄면   →  정렬 문제였다\n"
        "  그대로면      →  작화 모순이다\n\n"
        "둘 다 답이다. 아직 안 해봤다.",
        font=f12, fill=(200, 60, 60), spacing=6)

    sheet.save(os.path.join(OUT, "계획.png"))
    print("-> out/계획.png")


if __name__ == "__main__":
    main()
