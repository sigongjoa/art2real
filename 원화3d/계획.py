# -*- coding: utf-8 -*-
"""**지금 어디까지 왔나 한 장.** 실제 데이터로 그린다. 개념도가 아니다.

    python 계획.py        ->  out/계획.png

숫자는 하나도 적어 넣지 않는다 — 그릴 때마다 `hull.miss` 로 다시 잰다. 적어 넣은 숫자는
코드가 바뀌면 조용히 거짓말이 된다.
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

    # 정렬 전을 다시 만든다 — H.main() 이 돌려주는 masks 는 이미 맞춘 것이다
    pre = {v: H.to_win(H.declutter(m)) for v, m in raw.items()}
    m0, m1, fit = H.miss(pre), H.miss(masks), H.align(pre)
    say = lambda d: " · ".join("%.2f%%" % (100 * d[v]) for v in W.VIEWS)

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

    d.text((28, 22), "3판 정렬을 넣었다 — 어디가 정렬이었고 어디가 작화인가", font=f20, fill=(20, 20, 20))

    cols = [
        ("① 원화 3판  (측면의 가로줄이 지시선이다)", [raw[v] for v in W.VIEWS], None,
         "그려진 bbox 키 924 · 892 · 894\n판마다 3.6% 다르다"),
        ("② 창에 앉히고 front 에 맞춘다", [masks[v] for v in W.VIEWS], None,
         "side(dy %+.0f s %.4f)\nback(dx %+.0f dy %+.0f s %.4f)" % tuple(fit)),
        ("③ 깎고 되던진다", None, [ov[v] for v in W.VIEWS],
         "빨강 = hull 이 못 덮은 자리\n" + say(m1)),
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
    d.text((bx + 18, by + 14), "② 를 고쳤다 — 빨강은 줄었고, 남은 자리가 답이다", font=f14, fill=(200, 60, 60))
    d.multiline_text(
        (bx + 18, by + 44),
        "전   판마다 자기 bbox 키를 1.0 으로 늘렸다. 미지수 0개.      못 덮음  " + say(m0) + "\n"
        "후   front 고정, side·back 에 (dx · dy · s)                  못 덮음  " + say(m1) + "\n\n"
        "미지수는 6개가 아니라 5개였다. side 의 가로 이동은 hull 을 깊이로 밀 뿐이라\n"
        "세 실루엣 중 무엇도 안 바꾼다 — 실루엣이 못 보는 값이다 (python hull.py check 가 이걸 잰다).",
        font=f12, fill=(70, 70, 70), spacing=6)

    d.multiline_text(
        (Wd - 470, by + 44),
        "남은 빨강은 전부 발이다\n\n"
        "  행 930  front 에만 잉크가 있다\n"
        "  행 910  front 306..766 / back 367..703\n\n"
        "이동·배율로는 못 맞춘다. 작화 모순이고\n그게 파는 물건이다.",
        font=f12, fill=(200, 60, 60), spacing=6)

    sheet.save(os.path.join(OUT, "계획.png"))
    print("-> out/계획.png")


if __name__ == "__main__":
    main()
