# -*- coding: utf-8 -*-
"""**깎여 나간 27% 가 어디 있나** — 내가 내 결함을 찾는다 (2026-09-21).

    python 깎인곳.py [케이스=오메가몬]   -> out/깎인곳_<케이스>.png · out/기록/깎인곳_*.json

사용자(09-21): 「니가 문제 찾어」

`감사.py` 가 쟀다 — **retention 0.7312**. VH(세 실루엣 교집합)의 **27% 를 타원 가정으로 깎았다.**
그런데 **어디를** 깎았는지는 안 봤다. 골고루 깎였으면 「모서리를 둥글린 것」이고,
한 군데 몰렸으면 **그 부위를 통째로 잃은 것**이다 — 후자면 결함이다.

    ① 높이별 retention  — 어느 높이에서 많이 깎았나
    ② 부위별 retention  — 어느 부품이 제일 많이 잃었나
    ③ 깎인 자리 그림     — 앞 · 옆에서 본 «VH 에는 있는데 우리 형상엔 없는» 화소

문턱을 **먼저 적는다**:

    Q1  높이별 retention 의 최솟값 >= 0.5   (어느 높이도 절반 넘게 잃지 않는다)
    Q2  부위별 retention 의 최솟값 >= 0.5
    Q3  깎인 부피의 절반 이상이 **표면 가까이**(VH 표면에서 2 칸 이내)다 — 모서리를 둥글린 것이라는 증거
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
import 면자르기 as MJ
W = H.W
OUT = H.OUT


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    N = MJ.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    f, _ = H.field_hull(masks, back_sign=bs, n=N)
    M, VH = g > 0, f > 0
    깎 = VH & ~M
    전체 = float(VH.sum())
    print("  VH %d · 우리 %d · 깎인 것 %d (retention %.4f)"
          % (VH.sum(), M.sum(), 깎.sum(), M.sum() / 전체), flush=True)

    # ① 높이별
    높이 = []
    for k in range(N):
        v, m2 = float(VH[:, :, k].sum()), float(M[:, :, k].sum())
        if v > 50:
            높이.append({"k": k, "z": round(float(ax[2][k]), 3), "retention": round(m2 / v, 3), "VH": int(v)})
    최소높이 = min(높이, key=lambda r: r["retention"]) if 높이 else None

    # ② 부위별 (우리 형상의 부위 라벨을 VH 로 넓혀서 본다)
    _, lab, _ = MJ.부위(M)
    idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
    부위VH = np.where(VH, lab[tuple(idx)], 0)
    부위 = []
    for L in [int(x) for x in np.unique(lab) if x > 0]:
        v = float((부위VH == L).sum())
        m2 = float(((lab == L) & M).sum())
        if v > 200:
            부위.append({"부위": L, "retention": round(m2 / v, 3), "VH 부피 몫": round(v / 전체, 4)})
    부위.sort(key=lambda r: r["retention"])

    # ③ 깎인 곳이 표면 가까이인가
    거리 = ndimage.distance_transform_edt(VH)                        # VH 안쪽 거리
    표면가까이 = float((깎 & (거리 <= 2)).sum()) / max(float(깎.sum()), 1)
    깊은곳 = float((깎 & (거리 > 5)).sum()) / max(float(깎.sum()), 1)
    print("  깎인 것 중 표면 2 칸 이내 %.3f · 5 칸보다 깊은 곳 %.3f" % (표면가까이, 깊은곳), flush=True)
    print("  높이별 최소 retention %.3f (z %.2f)" % (최소높이["retention"], 최소높이["z"]), flush=True)
    print("  부위별 최소 retention %.3f (부위 %d)" % (부위[0]["retention"], 부위[0]["부위"]), flush=True)
    for r in 부위[:6]:
        print("   부위 %2d · retention %.3f · VH 몫 %.3f" % (r["부위"], r["retention"], r["VH 부피 몫"]), flush=True)

    Q = {"Q1 높이별 retention >= 0.5": bool(최소높이["retention"] >= 0.5),
         "Q2 부위별 retention >= 0.5": bool(부위[0]["retention"] >= 0.5),
         "Q3 깎인 것의 절반 이상이 표면 2 칸 이내": bool(표면가까이 >= 0.5)}
    for k, v in Q.items():
        print("   %-32s %s" % (k, "통과" if v else "**짐**"), flush=True)

    # 그림 — 앞 · 옆에서 본 깎인 자리
    def 투영(축):
        a = 깎.any(축).T[::-1]
        b = M.any(축).T[::-1]
        rgb = np.full(a.shape + (3,), 255, np.uint8)
        rgb[b] = (215, 218, 224)
        rgb[a] = (220, 60, 60)
        return Image.fromarray(rgb)

    S = 460
    앞 = 투영(1).resize((S, S), Image.NEAREST)
    옆 = 투영(0).resize((S, S), Image.NEAREST)
    # 높이 곡선
    곡 = Image.new("RGB", (S, S), "white")
    dc = ImageDraw.Draw(곡)
    for i in range(len(높이) - 1):
        y0 = S - int(높이[i]["k"] / N * S)
        y1 = S - int(높이[i + 1]["k"] / N * S)
        dc.line([int(높이[i]["retention"] * S), y0, int(높이[i + 1]["retention"] * S), y1], (40, 90, 200), 3)
    dc.line([int(0.5 * S), 0, int(0.5 * S), S], (220, 60, 60), 1)
    sheet = Image.new("RGB", (3 * (S + 8), S + 150), "white")
    for i, im in enumerate((앞, 옆, 곡)):
        sheet.paste(im, (i * (S + 8), 140))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
        f작 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17)
    except OSError:
        f제 = f본 = f작 = None
    dr.text((14, 14), "깎여 나간 27%% 가 어디 있나 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "retention %.4f · 깎인 것 중 **표면 2 칸 이내 %.1f%%** · 5 칸보다 깊은 곳 %.1f%%"
            % (M.sum() / 전체, 100 * 표면가까이, 100 * 깊은곳), (40, 44, 52), f본)
    dr.text((14, 80), "높이별 최소 %.3f (z %.2f) · 부위별 최소 %.3f (부위 %d)"
            % (최소높이["retention"], 최소높이["z"], 부위[0]["retention"], 부위[0]["부위"]), (40, 44, 52), f본)
    dr.text((14, 110), "빨강 = VH 에는 있는데 우리 형상에 없는 곳 · 회색 = 우리 형상", (90, 92, 100), f작)
    for i, t in enumerate(("앞에서 본 깎인 자리", "옆에서 본 깎인 자리", "높이별 retention (빨간 선 0.5)")):
        dr.text((i * (S + 8) + 6, 122), t, (60, 64, 72), f작)
    o = os.path.join(OUT, "깎인곳_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "retention": round(float(M.sum() / 전체), 4),
               "표면 2칸 이내 몫": round(표면가까이, 4), "5칸보다 깊은 몫": round(깊은곳, 4),
               "높이별 최소": 최소높이, "부위별": 부위, "판정": Q},
              open(os.path.join(OUT, "기록", "깎인곳_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")

