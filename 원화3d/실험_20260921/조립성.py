# -*- coding: utf-8 -*-
"""**조립에 용이한가** — 우리가 내는 부품을 mm 로 재서 판정한다 (2026-09-21).

    python 조립성.py [케이스=오메가몬] [키mm=150]   -> out/조립성_<케이스>.png · out/기록/조립성_*.json

사용자(09-21): 「우리 파이프라인이 **조립에 용이한지**도 봐야 하고」

지금까지는 「닮았나」만 쟀다. 조립은 **다른 자**가 필요하다. 문턱을 먼저 적는다
(키 150 mm · FDM 0.4 노즐 기준. 전부 **손잡이가 아니라 출력 상식**에서 온 값이다):

    Q1  부품이 전부 **닫힌 메시**다            안 닫히면 슬라이서가 거부한다
    Q2  **관절면 반지름 >= 3 mm**            핀 2 mm + 살 1 mm. 이보다 얇으면 관절이 부러진다
    Q3  **두께 0.8 mm 미만 부피 < 1%**       벽 두 겹(0.4×2). 이보다 얇으면 안 찍힌다
    Q4  부품 수 <= 15                      늘수록 국소점 · 조립 오차가 는다 (기획 09-20 9 절)
    Q5  부품마다 **이웃과 닿는다**              떠 있는 부품은 조립할 수 없다
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 면자르기 as MJ
import 파츠보기 as PV
W = H.W
OUT = H.OUT
핀 = 3.0                        # mm. 관절면 반지름 문턱
벽 = 0.8                        # mm. 두께 문턱 (FDM 0.4 노즐 두 겹)
부품상한 = 15


def main(case="오메가몬", 키mm=150.0):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    N = MJ.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    셀 = (W.U1 - W.U0) / N
    O = g > 0
    D, lab, _ = MJ.부위(O)
    # 창 한 변이 키의 몇 배인지로 mm 를 잡는다 — 키 = z 방향 차지한 높이
    zs = np.where(O.any((0, 1)))[0]
    키칸 = (zs[-1] - zs[0] + 1)
    mm칸 = 키mm / 키칸                                              # 칸 하나가 몇 mm 인가
    print("  키 %d 칸 = %.0f mm -> 칸 하나 %.3f mm" % (키칸, 키mm, mm칸), flush=True)

    부품 = [int(i) for i in np.unique(lab) if i > 0]
    조각, _, _ = PV.파츠만들기(case)                                   # 부품마다 따로 깎은 메시
    표 = []
    얇 = 0.0
    전체 = float(O.sum())
    for L in 부품:
        M = lab == L
        두께 = 2 * D[M] * mm칸                                        # 안쪽 거리 × 2 = 국소 두께
        얇 += float((두께 < 벽).sum())
        표.append({"부위": L, "부피 몫": round(float(M.sum()) / 전체, 4),
                   "중앙 두께 mm": round(float(np.median(두께)), 2),
                   "얇은 몫": round(float((두께 < 벽).mean()), 4)})
    얇몫 = 얇 / 전체

    # 관절면 — 면자르기와 같은 식
    관절 = []
    for i, a in enumerate(부품):
        for b in 부품[i + 1:]:
            r = MJ.관절면(lab, a, b, 셀)
            if r is None:
                continue
            c, n, rad, 화소 = r
            관절.append({"부위": [a, b], "반지름 mm": round(rad / (W.U1 - W.U0) * (W.U1 - W.U0) / 셀 * mm칸, 2),
                         "기울": round(float(np.degrees(np.arccos(min(1.0, abs(n[2]))))), 1),
                         "맞닿은 화소": 화소})
    관절.sort(key=lambda j: -j["맞닿은 화소"])
    닿는부품 = set()
    for j in 관절:
        닿는부품.update(j["부위"])

    닫힘 = [bool(m.is_watertight) for _, m, _ in 조각]
    Q = {"Q1 부품이 전부 닫혔다": bool(all(닫힘)),
         "Q2 관절면 반지름 >= %.0f mm" % 핀: bool(관절 and min(j["반지름 mm"] for j in 관절[:len(부품)]) >= 핀),
         "Q3 얇은 부피 < 1%%": bool(얇몫 < 0.01),
         "Q4 부품 수 <= %d" % 부품상한: bool(len(부품) <= 부품상한),
         "Q5 뜬 부품이 없다": bool(len(닿는부품) == len(부품))}
    print("  부품 %d · 닫힘 %d/%d · 얇은 부피 몫 %.4f · 관절면 %d"
          % (len(부품), sum(닫힘), len(닫힘), 얇몫, len(관절)), flush=True)
    for j in 관절[:8]:
        print("   관절 반지름 %5.2f mm · 기울 %5.1f° · 부위 %s" % (j["반지름 mm"], j["기울"], j["부위"]), flush=True)
    for k, v in Q.items():
        print("   %-26s %s" % (k, "통과" if v else "**짐**"), flush=True)

    # ---- 그림 (표만 · 모양은 파츠보기에 있다)
    S = 980
    sheet = Image.new("RGB", (S, 190 + 26 * (len(표) + len(관절[:8]) + len(Q) + 6)), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 27)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    y = 16
    dr.text((14, y), "조립에 용이한가 — 키 %d mm 로 환산해서 쟀다 · %s" % (키mm, case), (20, 22, 28), f제); y += 40
    dr.text((14, y), "칸 하나 = %.3f mm · 부품 %d · 관절면 %d" % (mm칸, len(부품), len(관절)), (60, 64, 72), f본); y += 30
    dr.text((14, y), "부품별 중앙 두께 / 얇은 몫", (20, 22, 28), f본); y += 26
    for r in sorted(표, key=lambda r: -r["부피 몫"])[:12]:
        c = (200, 40, 40) if r["중앙 두께 mm"] < 벽 * 3 else (60, 64, 72)
        dr.text((30, y), "부위 %2d · 부피 %.3f · 중앙 두께 %5.2f mm · 얇은 몫 %.3f"
                % (r["부위"], r["부피 몫"], r["중앙 두께 mm"], r["얇은 몫"]), c, f본); y += 26
    y += 10
    dr.text((14, y), "관절면 (맞닿은 넓이 순)", (20, 22, 28), f본); y += 26
    for j in 관절[:8]:
        c = (200, 40, 40) if j["반지름 mm"] < 핀 else (28, 110, 60)
        dr.text((30, y), "반지름 %5.2f mm · 기울 %5.1f° · 부위 %s" % (j["반지름 mm"], j["기울"], j["부위"]), c, f본); y += 26
    y += 10
    for k, v in Q.items():
        dr.text((14, y), "%s  %s" % (k, "통과" if v else "짐"), (28, 110, 60) if v else (200, 40, 40), f본); y += 28
    o = os.path.join(OUT, "조립성_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "키mm": 키mm, "칸 mm": round(mm칸, 4), "부품": 표,
               "관절": 관절, "판정": Q, "문턱": {"핀 mm": 핀, "벽 mm": 벽, "부품 상한": 부품상한}},
              open(os.path.join(OUT, "기록", "조립성_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 150.0)
