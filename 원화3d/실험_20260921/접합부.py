# -*- coding: utf-8 -*-
"""**접합부 치수를 받아서 우리 관절면에 넣어 본다** (2026-09-21).

    python 접합부.py [케이스=오메가몬] [키mm=150]   -> out/접합부_<케이스>.png · out/기록/접합부_*.json

사용자(09-21): 「그러면 **접합부도 GPT한테 만들어 달라고** 해」

받은 것은 **그림이 아니라 표**다 — 핀 지름 · 길이 · 구멍 지름 · 공차 · 가동 범위 (mm · 도).
그림은 우리가 못 먹지만 **숫자는 바로 깎을 수 있다.**

⚠ **출처를 분명히 적는다.** 이 값들은 우리가 **잰 것이 아니다** — GPT 가 준 관례값이고
근거로 Prusa 지식베이스(가동부 공차 ≥ 0.3 mm)를 들었다. 증명서에서 `given` 으로 찍힌다.
**시험 출력 한 판이면 measured 로 올라간다.**

여기서 하는 일: 우리가 **잰** 관절면 반지름(`면자르기` · mm)이 그 소켓을 품을 수 있는가.

    통과 조건   관절면 반지름 >= 구멍 지름/2 + 살 1.0 mm
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
살 = 1.0                        # mm. 구멍 둘레에 남아야 하는 살

# GPT 가 준 표 (2026-09-21 · chatgpt.com · 키 150 mm · FDM 0.4 노즐 · PLA)
# 출처: given(GPT · 근거로 Prusa 지식베이스 「가동부 공차 ≥ 0.3 mm」 인용). **우리가 잰 값이 아니다.**
표 = [
    {"관절": "목",      "방식": "볼조인트", "핀지름": 3.0, "핀길이": 4.0, "구멍지름": 6.0, "공차": 0.275, "가동": "±35°"},
    {"관절": "어깨 좌",  "방식": "볼조인트", "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 6.0, "공차": 0.275, "가동": "±45°"},
    {"관절": "어깨 우",  "방식": "볼조인트", "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 6.0, "공차": 0.275, "가동": "±45°"},
    {"관절": "팔꿈치 좌", "방식": "핀",      "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 3.6, "공차": 0.30, "가동": "0~135°"},
    {"관절": "팔꿈치 우", "방식": "핀",      "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 3.6, "공차": 0.30, "가동": "0~135°"},
    {"관절": "손목 좌",  "방식": "볼조인트", "핀지름": 2.5, "핀길이": 4.0, "구멍지름": 5.0, "공차": 0.25, "가동": "±45°"},
    {"관절": "손목 우",  "방식": "볼조인트", "핀지름": 2.5, "핀길이": 4.0, "구멍지름": 5.0, "공차": 0.25, "가동": "±45°"},
    {"관절": "허리",     "방식": "볼조인트", "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 6.0, "공차": 0.30, "가동": "±20°"},
    {"관절": "고관절 좌", "방식": "볼조인트", "핀지름": 3.5, "핀길이": 6.0, "구멍지름": 7.0, "공차": 0.25, "가동": "±40°"},
    {"관절": "고관절 우", "방식": "볼조인트", "핀지름": 3.5, "핀길이": 6.0, "구멍지름": 7.0, "공차": 0.25, "가동": "±40°"},
    {"관절": "무릎 좌",  "방식": "핀",      "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 3.6, "공차": 0.30, "가동": "0~130°"},
    {"관절": "무릎 우",  "방식": "핀",      "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 3.6, "공차": 0.30, "가동": "0~130°"},
    {"관절": "발목 좌",  "방식": "볼조인트", "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 6.0, "공차": 0.30, "가동": "±25°"},
    {"관절": "발목 우",  "방식": "볼조인트", "핀지름": 3.0, "핀길이": 5.0, "구멍지름": 6.0, "공차": 0.30, "가동": "±25°"},
]
출처 = {"표": "given(GPT · 2026-09-21 · 근거 Prusa 지식베이스 가동부 공차 >= 0.3 mm)",
        "관절면 반지름": "measured(면자르기 · 거리장 분수령 경계면)",
        "살": "guessed(1.0 mm · 눈으로)"}


def main(case="오메가몬", 키mm=150.0):
    from PIL import Image, ImageDraw
    import 조립성  # noqa: F401  (같은 환산을 쓴다)
    import hull as H
    import 면자르기 as MJ
    W = H.W
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    N = MJ.N
    g, _ = H.field_default(masks, back_sign=bs, n=N)
    셀 = (W.U1 - W.U0) / N
    O = g > 0
    D, lab, _ = MJ.부위(O)
    zs = np.where(O.any((0, 1)))[0]
    mm칸 = 키mm / (zs[-1] - zs[0] + 1)
    부품 = [int(i) for i in np.unique(lab) if i > 0]
    반지름 = []
    for i, a in enumerate(부품):
        for b in 부품[i + 1:]:
            r = MJ.관절면(lab, a, b, 셀)
            if r:
                반지름.append((r[3], r[2] / 셀 * mm칸))                 # (맞닿은 화소, mm)
    반지름.sort(key=lambda t: -t[0])
    잰것 = [r for _, r in 반지름]
    print("  우리가 잰 관절면 %d 개 · 반지름 mm: %s" % (len(잰것), ["%.1f" % v for v in 잰것[:10]]))

    필요 = sorted({r["구멍지름"] / 2 + 살 for r in 표})
    판정 = []
    for r in 표:
        need = r["구멍지름"] / 2 + 살
        맞 = [v for v in 잰것 if v >= need]
        판정.append({"관절": r["관절"], "필요 반지름 mm": round(need, 2),
                     "쓸 수 있는 관절면": len(맞), "통과": bool(맞)})
    통과수 = sum(p["통과"] for p in 판정)
    print("  GPT 표 %d 개 중 우리 관절면이 품을 수 있는 것 **%d 개**" % (len(표), 통과수))
    for p in 판정:
        print("   %-8s 필요 %4.1f mm · 되는 관절면 %2d 개 · %s"
              % (p["관절"], p["필요 반지름 mm"], p["쓸 수 있는 관절면"], "통과" if p["통과"] else "**짐**"))

    S = 1060
    sheet = Image.new("RGB", (S, 210 + 26 * (len(표) + 6)), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 18)
    except OSError:
        f제 = f본 = None
    y = 14
    dr.text((14, y), "접합부 — GPT 가 준 치수를 우리가 잰 관절면에 넣어 봤다 · %s (키 %d mm)" % (case, 키mm),
            (20, 22, 28), f제); y += 36
    dr.text((14, y), "⚠ 표의 값은 **잰 것이 아니다** — given(GPT · 근거 Prusa 가동부 공차 ≥ 0.3 mm). "
                     "시험 출력 한 판이면 measured 로 올라간다.", (200, 40, 40), f본); y += 28
    dr.text((14, y), "우리 관절면 반지름(measured) mm: %s" % ", ".join("%.1f" % v for v in 잰것[:10]),
            (28, 110, 60), f본); y += 30
    dr.text((14, y), "%-10s %-8s %7s %7s %8s %7s %9s %8s"
            % ("관절", "방식", "핀Ø", "핀길이", "구멍Ø", "공차", "가동", "판정"), (60, 64, 72), f본); y += 26
    for r, p in zip(표, 판정):
        c = (28, 110, 60) if p["통과"] else (200, 40, 40)
        dr.text((14, y), "%-10s %-8s %7.1f %7.1f %8.1f %7.2f %9s %8s"
                % (r["관절"], r["방식"], r["핀지름"], r["핀길이"], r["구멍지름"], r["공차"], r["가동"],
                   "통과" if p["통과"] else "짐"), c, f본); y += 26
    o = os.path.join(H.OUT, "접합부_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(H.OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "키mm": 키mm, "표": 표, "출처": 출처,
               "우리 관절면 반지름 mm": [round(v, 2) for v in 잰것], "판정": 판정,
               "통과": 통과수, "전체": len(표)},
              open(os.path.join(H.OUT, "기록", "접합부_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 150.0)
