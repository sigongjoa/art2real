# -*- coding: utf-8 -*-
"""**어떤 선이 부품 경계인가** — 선마다 증거 점수를 매긴다 (2026-09-21).

    python 선증거.py [케이스=오메가몬]   -> out/선증거_<케이스>.png · out/기록/선증거_*.json

사용자(09-21): 「분할로 가면 자연스럽게 선이 생기는데 왜 그걸 모르지?」
심사(GPT): 「맞다. 다만 **먹선 ≠ 무조건 부품 경계**다. 100 선 → 100 부품은 잘못된 전략이고,
seam 후보의 신뢰도를 올리는 증거가 따로 있다.」

그 증거 중 **지금 잴 수 있는 셋**을 선 조각마다 잰다:

    ① 폐곡선   그 선이 영역을 **닫는가** (닫힌 판의 테두리인가 · `binary_fill_holes` 차이)
    ② 색차     선 **양옆 칸의 색이 다른가** (다른 판이면 색이 다르다 · 원화 색으로 ΔE)
    ③ 다른 판  같은 높이에 **뒤 판에도 선이 있는가** (한 판에만 있으면 음영선일 확률이 높다)

    점수 = 0.4·폐곡선 + 0.4·색차 + 0.2·다른 판        (가중치는 **눈으로 고른 값** · guessed)

점수가 높은 선만 **나눈다**. 낮은 선은 **아무것도 안 만든다** — 홈도 안 판다.
그러면 「음영선을 깊이로 지어내는」 일이 구조적으로 막힌다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
W = H.W
OUT = H.OUT
조각최소 = 100                  # 화소. 이보다 작은 선 조각은 안 본다 (부스러기)
문턱 = 0.55                     # 이 점수 이상이면 **나눌 후보**. guessed


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    import cv2
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)

    # 앞 판 먹선과 색
    선 = H.ink_map(os.path.join(base, src["front"]))
    _, w2 = H.to_win(H.declutter(raw["front"]), 선.astype(np.float32))
    선창 = H._warp_one(w2, "front", p) > 0.5
    im = cv2.imdecode(np.fromfile(os.path.join(base, src["front"]), np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
    알 = im[:, :, 3] > 127 if im.ndim == 3 and im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    rgb = np.where(알[:, :, None], rgb, 255).astype(np.uint8)
    d = H.declutter(raw["front"])
    색창 = np.clip(np.dstack([H._warp_one(H.to_win(d, rgb[:, :, k].astype(np.float32))[1], "front", p)
                              for k in range(3)]), 0, 255).astype(np.uint8)
    # 뒤 판 먹선 (같은 창)
    선b = H.ink_map(os.path.join(base, src["back"]))
    _, wb = H.to_win(H.declutter(raw["back"]), 선b.astype(np.float32))
    선뒤 = H._warp_one(wb, "back", p) > 0.5
    if bs < 0:
        선뒤 = 선뒤[:, ::-1]

    안 = ndimage.binary_erosion(masks["front"].astype(bool), iterations=3)
    선창 &= 안
    칸, n칸 = ndimage.label(안 & ~ndimage.binary_dilation(선창, iterations=1))
    칸색 = {}
    for i in range(1, n칸 + 1):
        sel = 칸 == i
        if sel.sum() >= 80:
            칸색[i] = 색창[sel].mean(0)

    lab, n = ndimage.label(선창, np.ones((3, 3), bool))
    크 = np.bincount(lab.ravel())
    표 = []
    for i in range(1, n + 1):
        if 크[i] < 조각최소:
            continue
        comp = lab == i
        # ① 폐곡선 — 그 선만으로 닫히는 구멍이 있나
        찬 = ndimage.binary_fill_holes(comp)
        폐 = float((찬 & ~comp).sum()) / float(comp.sum())
        폐점 = float(np.clip(폐 / 3.0, 0, 1))                          # 구멍이 선 굵기의 3 배면 만점
        # ② 양옆 칸 색차
        고리 = ndimage.binary_dilation(comp, iterations=4) & ~ndimage.binary_dilation(comp, iterations=1)
        이웃 = [v for v in np.unique(칸[고리]) if v in 칸색]
        if len(이웃) >= 2:
            cs = np.array([칸색[v] for v in 이웃])
            색차 = float(np.linalg.norm(cs[:, None] - cs[None], axis=2).max())
        else:
            색차 = 0.0
        # ⚠ 처음엔 120 으로 나눴더니 거의 다 만점이었다 — RGB 대각선이 441 이다 (09-21)
        색점 = float(np.clip(색차 / 441.0, 0, 1))                       # 흰↔검정이 441
        # ③ 뒤 판에도 같은 높이에 선이 있나
        # ⚠ 처음엔 「그 행에 뒤 판 선이 하나라도 있나」로 쟀더니 **전부 1.00** 이었다 — 못 지는 자다.
        #    **같은 자리**(±3 화소)에 뒤 판 선이 있는지로 고쳤다 (09-21)
        가까 = ndimage.binary_dilation(선뒤, iterations=3)
        뒤있 = float(가까[comp].mean())
        점수 = 0.4 * 폐점 + 0.4 * 색점 + 0.2 * 뒤있
        표.append({"조각": int(i), "화소": int(크[i]), "폐곡선": round(폐점, 3), "색차": round(색차, 1),
                   "색점": round(색점, 3), "뒤 판": round(뒤있, 3), "점수": round(점수, 3)})
    표.sort(key=lambda r: -r["점수"])
    나눌 = [r for r in 표 if r["점수"] >= 문턱]
    print("  선 조각 %d 개 (>= %d 화소) · **나눌 후보 %d 개** (점수 >= %.2f)"
          % (len(표), 조각최소, len(나눌), 문턱), flush=True)
    for r in 표[:12]:
        print("   조각 %3d · %5d 화소 · 폐곡선 %.2f · 색차 %5.1f · 뒤판 %.2f · **점수 %.3f**%s"
              % (r["조각"], r["화소"], r["폐곡선"], r["색차"], r["뒤 판"], r["점수"],
                 "  <- 나눈다" if r["점수"] >= 문턱 else ""), flush=True)
    몫 = sum(r["화소"] for r in 나눌) / max(sum(r["화소"] for r in 표), 1)
    print("  나눌 선이 담은 화소 몫 %.3f" % 몫, flush=True)

    # 그림 — 점수로 색칠한 선
    rgb2 = np.full(선창.shape + (3,), 255, np.uint8)
    rgb2[masks["front"].astype(bool)] = (238, 240, 244)
    for r in 표:
        c = (30, 150, 70) if r["점수"] >= 문턱 else (215, 45, 45)
        rgb2[ndimage.binary_dilation(lab == r["조각"], iterations=1)] = c
    S = 560
    그림 = Image.fromarray(rgb2).resize((S, S), Image.LANCZOS)
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    sheet = Image.new("RGB", (2 * (S + 8) + 460, S + 150), "white")
    sheet.paste(원, (0, 140))
    sheet.paste(그림, (S + 8, 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "어떤 선이 부품 경계인가 — 선마다 증거 점수 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "점수 = 0.4·폐곡선 + 0.4·색차 + 0.2·뒤 판 대응   (가중치는 눈으로 고른 값)",
            (90, 92, 100), f본)
    dr.text((14, 80), "선 조각 %d 개 중 **나눌 후보 %d 개** · 그것이 담은 선 화소 몫 %.1f%%"
            % (len(표), len(나눌), 100 * 몫), (28, 110, 60), f본)
    dr.text((14, 110), "초록 = 나눈다(부품 경계 후보) · 빨강 = 아무것도 안 만든다(음영선일 수 있다)",
            (60, 64, 72), f작)
    x = 2 * (S + 8) + 10
    y = 140
    dr.text((x, y), "%-6s %6s %6s %6s %6s" % ("조각", "폐곡선", "색차", "뒤판", "점수"), (60, 64, 72), f작)
    y += 26
    for r in 표[:14]:
        c = (28, 110, 60) if r["점수"] >= 문턱 else (200, 40, 40)
        dr.text((x, y), "%-6d %6.2f %6.0f %6.2f %6.3f"
                % (r["조각"], r["폐곡선"], r["색차"], r["뒤 판"], r["점수"]), c, f작)
        y += 24
    o = os.path.join(OUT, "선증거_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "문턱": 문턱, "조각최소": 조각최소, "선 조각": len(표),
               "나눌 후보": len(나눌), "화소 몫": round(몫, 4), "표": 표,
               "가중치": {"폐곡선": 0.4, "색차": 0.4, "뒤 판": 0.2, "출처": "guessed(눈으로)"}},
              open(os.path.join(OUT, "기록", "선증거_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")

