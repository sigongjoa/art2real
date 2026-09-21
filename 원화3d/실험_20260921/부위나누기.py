# -*- coding: utf-8 -*-
"""**붙어 버린 팔이 갈리나** — 부위 분할의 1 번 위험을 먼저 잰다 (2026-09-21).

    python 부위나누기.py [케이스=오메가몬]   -> out/부위나누기_<케이스>.png · out/기록/부위나누기_*.json

설계(`claudedocs/설계_부위조립_20260921.md` 9 절)의 첫 번째 「틀릴 수 있는 길」:
**오메가몬은 팔이 몸통에 닿아 있어 3D 연결성분으로는 한 덩어리일 수 있다.**
가동 피규어로 가려면 팔이 갈려야 하므로 **더 짓기 전에 이걸 먼저 잰다.**

    ① 관절 후보(`관절후보.잘록`)의 높이에서 장을 **한 칸 끊는다** (자르는 면)
    ② 남은 것의 3D 연결성분 -> 구조 부품 후보
    ③ 부피 0.5% 미만 조각은 「부스러기」로 따로 센다

통과 조건을 **먼저 적는다**:

    Q1  구조 부품이 **3 개 이상** 나온다 (통짜면 1 개다)
    Q2  제일 큰 조각이 전체 부피의 **90% 미만** (하나가 다 먹으면 안 갈린 것이다)
    Q3  부피 합이 원래와 같다 (자르는 면 한 칸 말고는 안 잃는다 · 오차 < 2%)
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
import 관절후보 as JC
W = H.W
OUT = H.OUT
부스러기 = 0.005                 # 전체 부피 대비 이보다 작으면 부스러기로 센다


def 나누기(g, 면):
    """자르는 면(칸 번호)에서 장을 한 칸 끊고 3D 연결성분."""
    O = g > 0
    C = O.copy()
    for k in 면:
        C[:, :, k] = False
    lab, n = ndimage.label(C)
    return O, lab, n


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    g, (_, _, z) = H.field_default(masks, back_sign=bs)
    A = np.array([(g[:, :, k] > 0).sum() for k in range(g.shape[2])], float)
    면 = [k for k, _ in JC.잘록(A)]
    O, lab, n = 나누기(g, 면)

    크기 = np.bincount(lab.ravel())
    크기[0] = 0
    전체 = int(O.sum())
    순 = np.argsort(-크기)
    구조 = [int(i) for i in 순 if 크기[i] >= 부스러기 * 전체]
    조각 = {"구조 부품": len(구조), "부스러기": int((크기 > 0).sum()) - len(구조),
            "제일 큰 조각 몫": round(float(크기[순[0]]) / max(전체, 1), 3),
            "부피 보존": round(float(크기.sum()) / max(전체, 1), 3)}
    Q = {"Q1 구조 부품 >= 3": len(구조) >= 3,
         "Q2 제일 큰 조각 < 90%": 조각["제일 큰 조각 몫"] < 0.90,
         "Q3 부피 보존 오차 < 2%": abs(1 - 조각["부피 보존"]) < 0.02}

    # ---- 그림: 앞에서 본 색칠 (제일 앞 복셀의 이름)
    팔 = [(230, 70, 70), (70, 140, 230), (70, 190, 110), (240, 170, 40), (170, 100, 220),
          (40, 190, 200), (230, 120, 180), (140, 150, 60), (120, 120, 200), (200, 90, 60)]
    nx, ny, nz = lab.shape
    첫 = np.zeros((nz, nx), np.int32)
    for j in range(ny):                                            # y 가 작을수록 앞 (-y 가 앞)
        면있 = (첫 == 0) & (lab[:, j, :].T > 0)
        첫[면있] = lab[:, j, :].T[면있]
    rgb = np.full((nz, nx, 3), 255, np.uint8)
    for i, l in enumerate(구조[:len(팔)]):
        rgb[첫 == l] = 팔[i]
    나머지 = (첫 > 0) & ~np.isin(첫, 구조[:len(팔)])
    rgb[나머지] = (185, 188, 195)
    색칠 = Image.fromarray(rgb[::-1]).resize((620, 620), Image.NEAREST)

    S = 620
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    sheet = Image.new("RGB", (S * 2 + 430, S + 90), "white")
    sheet.paste(원, (0, 80))
    sheet.paste(색칠, (S + 10, 80))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    dr.text((14, 18), "부위 나누기 — 붙어 버린 팔이 갈리나 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "관절 후보 높이 %d 곳에서 장을 한 칸 끊고 3D 연결성분. 색 = 부피 큰 부품 열, 회색 = 11 번 이후 부품 · 부스러기"
            % len(면), (90, 92, 100), f본)
    x = S * 2 + 30
    y = 90
    for k, v in 조각.items():
        dr.text((x, y), "%s  %s" % (k, v), (40, 44, 52), f본); y += 30
    y += 12
    for k, v in Q.items():
        dr.text((x, y), "%s  %s" % (k, "통과" if v else "**짐**"), (28, 110, 60) if v else (200, 40, 40), f본)
        y += 30
    y += 12
    dr.text((x, y), "부품별 부피 몫", (40, 44, 52), f본); y += 30
    for i, l in enumerate(구조[:10]):
        dr.rectangle([x, y + 4, x + 18, y + 20], fill=팔[i])
        dr.text((x + 28, y), "%d 번  %.1f%%" % (i + 1, 100 * 크기[l] / max(전체, 1)), (40, 44, 52), f본)
        y += 30
    o = os.path.join(OUT, "부위나누기_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "자르는 면 z": [round(float(z[k]), 4) for k in 면], "조각": 조각,
               "판정": Q, "부품 부피 몫": [round(float(크기[l]) / max(전체, 1), 4) for l in 구조[:12]]},
              open(os.path.join(OUT, "기록", "부위나누기_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  자르는 면 %d · %s" % (len(면), 조각))
    for k, v in Q.items():
        print("   %-24s %s" % (k, "통과" if v else "짐"))
    print("  부품 몫 %s" % ["%.3f" % (크기[l] / max(전체, 1)) for l in 구조[:8]])
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")

