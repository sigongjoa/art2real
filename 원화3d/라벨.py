# -*- coding: utf-8 -*-
"""**느낌을 데이터로 만든다.** 두 판본을 짝으로 보여주고 사람이 고르게 한다.

    python 라벨.py            -> out/라벨/판정지_N.png · out/라벨/정답표.json
    python 라벨.py 채점 "1A 2B 3= ..."   -> 지표별로 사람 선택과 몇 % 맞는지

## 왜

`box_score` 는 「느낌을 숫자로」 만든 값이었다. 그럴듯했고 근거로 썼고, 정답이 생기니
품질과 **반대로** 갔다. 손으로 설계한 지각 지표는 만들기 쉽고 속기도 쉽다.

그래서 규칙 하나 — **느낌 지표는 사람 판정과 맞춰본 뒤에만 쓴다.**

## 어떻게

케이스마다 이진 hull 과 깊이 깎기를 3/4 각도로 나란히 렌더한다. **좌우는 무작위로 섞고**
어느 쪽이 무엇인지는 `정답표.json` 에만 적는다 (판정지에는 안 적는다 — 알고 보면 안 된다).

사람이 고른 뒤 `채점` 으로 각 지표가 그 선택과 몇 % 일치하는지 센다.
사람과 안 맞는 지표는 `box_score` 처럼 버린다.

**이게 되면 두 가지가 한꺼번에 풀린다** — 느낌이 숫자가 되고, 고객 원화처럼
정답 메시가 없는 자리에서도 쓸 수 있는 지표 후보가 생긴다.
"""
import json
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import 각도 as A
import 대조 as C
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "라벨")
AZ, R, PER = 35, 300, 6                          # 3/4 각도 · 타일 크기 · 한 장에 몇 쌍


def make():
    os.makedirs(OUT, exist_ok=True)
    rows = json.load(open(os.path.join(os.path.dirname(OUT), "대조.json"), encoding="utf-8"))
    rnd = random.Random(11)
    key, pages, cur = {}, [], []
    for i, r in enumerate(rows, 1):
        c = r["case"]
        try:
            plain, deep, _, _ = C.build(c)
        except Exception as e:
            print("  %-30s 실패 %s" % (c, type(e).__name__)); continue
        left_is_deep = rnd.random() < 0.5
        a, b = (deep, plain) if left_is_deep else (plain, deep)
        key[str(i)] = {"case": c, "left": "깊이" if left_is_deep else "이진",
                       "d_iou": round(r["깊이_iou"] - r["이진_iou"], 4)}
        cur.append((i, c, A.shot(a, AZ, R), A.shot(b, AZ, R)))
        print("  %2d %s" % (i, c))
        if len(cur) == PER:
            pages.append(cur); cur = []
    if cur:
        pages.append(cur)

    for pi, page in enumerate(pages, 1):
        w = 2 * R + 60
        im = Image.new("RGB", (w, 56 + len(page) * (R + 40)), "white")
        d = ImageDraw.Draw(im)
        d.text((18, 12), "어느 쪽이 더 '그 물건'처럼 보이나?  (%d/%d)" % (pi, len(pages)),
               font=_font(19), fill=(20, 20, 20))
        d.text((18, 36), "왼쪽=A · 오른쪽=B · 모르겠으면 =  |  예: 1A 2B 3=",
               font=_font(12), fill=(120, 120, 120))
        for j, (i, c, ia, ib) in enumerate(page):
            y = 56 + j * (R + 40)
            im.paste(ia, (18, y)); im.paste(ib, (36 + R, y))
            d.rectangle([18, y, 17 + R, y + R - 1], outline=(215, 215, 215))
            d.rectangle([36 + R, y, 35 + R + R, y + R - 1], outline=(215, 215, 215))
            d.text((18, y + R + 6), "%d.  A" % i, font=_font(14), fill=(20, 20, 20))
            d.text((36 + R, y + R + 6), "B", font=_font(14), fill=(20, 20, 20))
            d.text((80, y + R + 8), c[:44], font=_font(11), fill=(150, 150, 150))
        im.save(os.path.join(OUT, "판정지_%d.png" % pi))
    json.dump(key, open(os.path.join(OUT, "정답표.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  -> %d 장 · %d 쌍" % (len(pages), len(key)))


def grade(answer):
    """사람 선택 vs 지표. 지표가 고른 것과 사람이 고른 것이 몇 % 같은가."""
    key = json.load(open(os.path.join(OUT, "정답표.json"), encoding="utf-8"))
    rows = {r["case"]: r for r in
            json.load(open(os.path.join(os.path.dirname(OUT), "대조.json"), encoding="utf-8"))}
    picks = {}
    for tok in answer.replace(",", " ").split():
        n, ch = tok[:-1], tok[-1].upper()
        if n in key and ch in "AB=":
            picks[n] = ch
    if not picks:
        print("  읽을 답이 없다. 예: 1A 2B 3="); return
    METRICS = {"3D IoU": lambda r: r["깊이_iou"] - r["이진_iou"],
               "못덮음(작을수록)": lambda r: r["이진_miss"] - r["깊이_miss"],
               "부피비 1 에 가까움": lambda r: abs(r["이진_vol"] - 1) - abs(r["깊이_vol"] - 1)}
    usable = [n for n, ch in picks.items() if ch != "=" and key[n]["case"] in rows]
    print("  찍은 %d 쌍 · 모르겠음 %d · 채점불가라 제외 %d -> 셀 수 있는 %d 쌍"
          % (len(picks), sum(1 for v in picks.values() if v == "="),
             sum(1 for n, ch in picks.items() if ch != "=" and key[n]["case"] not in rows),
             len(usable)))
    deep_picked = sum(1 for n in usable
                      if (picks[n] == "A") == (key[n]["left"] == "깊이"))
    print("  사람이 깊이 깎기를 고른 비율 %d/%d = %.0f%%" % (deep_picked, len(usable),
                                                            100 * deep_picked / max(len(usable), 1)))
    left = sum(1 for n in usable if picks[n] == "A")
    print("  왼쪽(A)을 고른 비율 %d/%d = %.0f%%  (50%% 에서 크게 벗어나면 위치 편향)"
          % (left, len(usable), 100 * left / max(len(usable), 1)))
    for nm, f in METRICS.items():
        ok = tot = 0
        for n, ch in picks.items():
            if ch == "=":
                continue
            k = key[n]
            if k["case"] not in rows:
                continue                          # 지금 채점불가인 케이스는 지표값을 못 믿는다
            human_deep = (ch == "A") == (k["left"] == "깊이")     # 사람이 깊이를 골랐나
            v = f(rows[k["case"]])
            if abs(v) < 1e-9:
                continue
            tot += 1
            ok += int((v > 0) == human_deep)
        print("    %-20s 사람과 일치 %d/%d = %.0f%%" % (nm, ok, tot, 100 * ok / max(tot, 1)))
    print("  (50% 면 동전던지기. 지표가 느낌을 못 잡는다는 뜻이다)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "채점":
        grade(" ".join(sys.argv[2:]))
    else:
        make()
