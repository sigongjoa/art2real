# -*- coding: utf-8 -*-
"""**느낌을 데이터로 만든다.** 두 판본을 짝으로 보여주고 사람이 고르게 한다.

    python 라벨.py            -> out/라벨/판정지_N.png · out/라벨/정답표.json
    python 라벨.py 채점 "1A 2B 3= ..."   -> 답을 out/라벨/판정.json 에 쌓고 지표와 맞춘다
    python 라벨.py 채점                  -> 쌓아둔 답으로 다시 채점 (지표를 새로 만들 때)
    python 라벨.py 자체검사              -> 일관성 필터가 위치 편향을 죽이는지 본다

## 왜

`box_score` 는 「느낌을 숫자로」 만든 값이었다. 그럴듯했고 근거로 썼고, 정답이 생기니
품질과 **반대로** 갔다. 손으로 설계한 지각 지표는 만들기 쉽고 속기도 쉽다.

그래서 규칙 하나 — **느낌 지표는 사람 판정과 맞춰본 뒤에만 쓴다.**

## 같은 쌍을 두 번 낸다 — 자가 흔들려서 고쳤다 (2026-09-10)

한 번씩만 찍은 27쌍에서 **내가 왼쪽을 78% 골랐다.** 판본이 아니라 위치를 고른 것이다.
그 판정지 위에서 「3D IoU 는 눈과 63% 일치」라고 했는데, 자가 편향이면 그 63% 는
지표 점수가 아니라 편향 점수다.

이제 케이스마다 **좌우를 바꿔 두 번** 낸다. 1회차를 전부 깔고 2회차를 뒤에 깔아
같은 쌍이 붙어 나오지 않게 한다.

    두 번 다 같은 판본      인정. 이게 얼린 판정 집합이다
    두 번이 엇갈림          뺀다 (동전던지기였다)
    한 번만 답 · 모르겠음    뺀다

**왼쪽만 고르는 사람은 인정 집합에서 전멸한다** — 좌우가 바뀌면 답도 바뀌니까.
`자체검사` 가 그걸 assert 로 잡는다.

답은 `판정.json` 에 쌓인다. 새 지표를 만들 때마다 다시 찍지 않고 `채점` 만 돌린다.

## 어떻게

케이스마다 이진 hull 과 깊이 깎기를 3/4 각도로 나란히 렌더한다. 어느 쪽이 무엇인지는
`정답표.json` 에만 적는다 (판정지에는 안 적는다 — 알고 보면 안 된다).

사람과 안 맞는 지표는 `box_score` 처럼 버린다.
"""
import json
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 각도 as A
import 대조 as C
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "라벨")
AZ, R, PER = 35, 300, 6                          # 3/4 각도 · 타일 크기 · 한 장에 몇 쌍
KEY = os.path.join(OUT, "정답표.json")
PICKS = os.path.join(OUT, "판정.json")


def make():
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(PICKS):                    # 번호가 바뀌니 옛 답은 못 쓴다. 지우진 않는다
        old = PICKS.replace(".json", "_%d.json" % int(os.path.getmtime(PICKS)))
        os.rename(PICKS, old)
        print("  옛 답을 %s 로 옮겼다 (번호가 바뀐다)" % os.path.basename(old))
    rows = json.load(open(os.path.join(os.path.dirname(OUT), "대조.json"), encoding="utf-8"))
    rnd = random.Random(11)
    reps = ([], [])
    for r in rows:
        c = r["case"]
        try:
            plain, deep, _, _ = C.build(c)
        except Exception as e:
            print("  %-30s 실패 %s" % (c, type(e).__name__)); continue
        deep_im, plain_im = A.shot(deep, AZ, R), A.shot(plain, AZ, R)
        first = rnd.random() < 0.5               # 1회차에 깊이가 왼쪽인가
        for rep in (0, 1):
            left_is_deep = first if rep == 0 else not first
            a, b = (deep_im, plain_im) if left_is_deep else (plain_im, deep_im)
            reps[rep].append({"case": c, "rep": rep, "a": a, "b": b,
                              "left": "깊이" if left_is_deep else "이진",
                              "d_iou": round(r["깊이_iou"] - r["이진_iou"], 4)})
        print("  %s" % c)
    # 1회차를 전부 깔고 2회차를 뒤에. 같은 쌍이 한 장 안에 두 번 나오면 기억으로 찍는다.
    # 반씩 나눠도 이음매(1회차 꼬리 · 2회차 머리)에서 붙으므로 간격을 강제한다
    rnd.shuffle(reps[0])
    n, gap = len(reps[0]), 2 * PER
    for _ in range(500):
        rnd.shuffle(reps[1])
        pos = {s["case"]: i for i, s in enumerate(reps[0])}
        if min(n + j - pos[s["case"]] for j, s in enumerate(reps[1])) >= gap:
            break
    else:
        raise SystemExit("두 회차를 %d 칸 이상 떼어놓지 못했다 — 케이스가 너무 적다" % gap)

    key, pages = {}, []
    for i, s in enumerate(reps[0] + reps[1], 1):
        key[str(i)] = {k: s[k] for k in ("case", "left", "rep", "d_iou")}
        if (i - 1) % PER == 0:
            pages.append([])
        pages[-1].append((i, s))

    for pi, page in enumerate(pages, 1):
        w = 2 * R + 60
        im = Image.new("RGB", (w, 56 + len(page) * (R + 40)), "white")
        d = ImageDraw.Draw(im)
        d.text((18, 12), "어느 쪽이 더 '그 물건'처럼 보이나?  (%d/%d)" % (pi, len(pages)),
               font=_font(19), fill=(20, 20, 20))
        d.text((18, 36), "왼쪽=A · 오른쪽=B · 모르겠으면 =  |  예: 1A 2B 3=",
               font=_font(12), fill=(120, 120, 120))
        for j, (i, s) in enumerate(page):
            y = 56 + j * (R + 40)
            im.paste(s["a"], (18, y)); im.paste(s["b"], (36 + R, y))
            d.rectangle([18, y, 17 + R, y + R - 1], outline=(215, 215, 215))
            d.rectangle([36 + R, y, 35 + R + R, y + R - 1], outline=(215, 215, 215))
            d.text((18, y + R + 6), "%d.  A" % i, font=_font(14), fill=(20, 20, 20))
            d.text((36 + R, y + R + 6), "B", font=_font(14), fill=(20, 20, 20))
            d.text((80, y + R + 8), s["case"][:44], font=_font(11), fill=(150, 150, 150))
        im.save(os.path.join(OUT, "판정지_%d.png" % pi))
    json.dump(key, open(KEY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %d 장 · %d 칸 (케이스 %d 개 × 2회)" % (len(pages), len(key), len(key) // 2))


def _verdicts(key, picks):
    """좌우 바꿔 두 번 찍은 답을 케이스 하나의 판정으로 접는다.

    두 번 다 같은 판본을 골랐을 때만 인정한다. 위치를 고른 답은 여기서 죽는다."""
    by = {}
    for n, ch in picks.items():
        k = key.get(n)
        if not k:
            continue
        v = None if ch == "=" else ("깊이" if (ch == "A") == (k["left"] == "깊이") else "이진")
        by.setdefault(k["case"], []).append(v)
    good, flip, part = {}, [], []
    for c, vs in sorted(by.items()):
        if len(vs) < 2 or None in vs:
            part.append(c)
        elif len(set(vs)) == 1:
            good[c] = vs[0]
        else:
            flip.append(c)
    return good, flip, part


def _read(answer):
    """쌓아둔 답에 이번 답을 얹는다. 페이지별로 나눠 찍을 수 있게."""
    picks = json.load(open(PICKS, encoding="utf-8")) if os.path.exists(PICKS) else {}
    for tok in answer.replace(",", " ").split():
        n, ch = tok[:-1], tok[-1].upper()
        if ch in "AB=":
            picks[n] = ch
    return picks


def grade(answer):
    """사람 선택 vs 지표. 지표가 고른 것과 사람이 고른 것이 몇 % 같은가."""
    key = json.load(open(KEY, encoding="utf-8"))
    rows = {r["case"]: r for r in
            json.load(open(os.path.join(os.path.dirname(OUT), "대조.json"), encoding="utf-8"))}
    picks = {n: ch for n, ch in _read(answer).items() if n in key}
    if not picks:
        print("  읽을 답이 없다. 예: 1A 2B 3="); return
    json.dump(picks, open(PICKS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    METRICS = {"3D IoU": lambda r: r["깊이_iou"] - r["이진_iou"],
               "못덮음(작을수록)": lambda r: r["이진_miss"] - r["깊이_miss"],
               "부피비 1 에 가까움": lambda r: abs(r["이진_vol"] - 1) - abs(r["깊이_vol"] - 1)}
    good, flip, part = _verdicts(key, picks)
    said = [n for n, ch in picks.items() if ch != "="]
    left = sum(1 for n in said if picks[n] == "A")
    print("  찍은 %d / %d 칸 · 케이스 %d 개" % (len(picks), len(key), len(key) // 2))
    print("  왼쪽(A) %d/%d = %.0f%%  (50%% 에서 벗어난 만큼이 위치 편향이다)"
          % (left, len(said), 100 * left / max(len(said), 1)))
    print("  **일관 %d · 뒤집힘 %d · 미완 %d** -> 셀 수 있는 %d 케이스"
          % (len(good), len(flip), len(part), len(good)))
    if flip:
        print("     뒤집힌 건 뺀다 (동전던지기였다): %s" % ", ".join(c[:20] for c in flip[:6]))
    usable = [c for c in good if c in rows]
    if not usable:
        print("  채점할 케이스가 없다. 좌우가 바뀌면 답도 바뀌어야 한다"); return
    deep = sum(1 for c in usable if good[c] == "깊이")
    print("  사람이 깊이 깎기를 고른 비율 %d/%d = %.0f%%"
          % (deep, len(usable), 100 * deep / len(usable)))
    for nm, f in METRICS.items():
        ok = tot = 0
        for c in usable:
            v = f(rows[c])
            if abs(v) < 1e-9:
                continue
            tot += 1
            ok += int((v > 0) == (good[c] == "깊이"))
        print("    %-20s 사람과 일치 %d/%d = %.0f%%" % (nm, ok, tot, 100 * ok / max(tot, 1)))
    print("  (50% 면 동전던지기. 지표가 느낌을 못 잡는다는 뜻이다)")


def selfcheck():
    """일관성 필터가 진짜로 위치 편향을 죽이는지."""
    key = {"1": {"case": "x", "left": "깊이"}, "2": {"case": "y", "left": "이진"},
           "3": {"case": "z", "left": "깊이"},
           "4": {"case": "x", "left": "이진"}, "5": {"case": "y", "left": "깊이"},
           "6": {"case": "z", "left": "이진"}}
    g, f, p = _verdicts(key, {n: "A" for n in key})           # 왼쪽만 고르는 사람
    assert g == {} and sorted(f) == ["x", "y", "z"], (g, f, p)
    g, f, p = _verdicts(key, {n: "B" for n in key})           # 오른쪽만 고르는 사람
    assert g == {} and sorted(f) == ["x", "y", "z"], (g, f, p)
    # 판본을 보고 고르는 사람 — 좌우가 바뀌면 답도 따라 바뀐다
    g, f, p = _verdicts(key, {"1": "A", "4": "B", "2": "A", "5": "B", "3": "A", "6": "B"})
    assert g == {"x": "깊이", "y": "이진", "z": "깊이"} and not f, (g, f, p)
    g, f, p = _verdicts(key, {"1": "A", "2": "A", "4": "="})  # 한 번만 · 모르겠음
    assert g == {} and sorted(p) == ["x", "y"], (g, f, p)
    print("  자체검사 통과 — 위치만 보는 답은 인정 집합에서 전멸한다")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "채점":
        grade(" ".join(sys.argv[2:]))
    elif len(sys.argv) > 1 and sys.argv[1] == "자체검사":
        selfcheck()
    else:
        make()
