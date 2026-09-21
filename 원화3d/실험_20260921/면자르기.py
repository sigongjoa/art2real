# -*- coding: utf-8 -*-
"""**면으로 자른다** — 관절면은 높이가 아니라 **그 부위 축에 직각인 면**이다 (2026-09-21).

    python 면자르기.py [케이스=오메가몬]   -> out/면자르기_<케이스>.png · out/기록/면자르기_*.json · out/관절_<케이스>.json

사용자(09-21): 「어떠한 피규어가 **높이 기반으로 자르냐**. **면 기반으로 잘라야지**」 — 맞다.
`부위나누기.py` 는 z 수평면으로 끊었다. 그건 **차렷 자세에서만 우연히 맞는다** —
팔꿈치는 팔 축에 직각인 면이고, 비스듬한 칼은 수평으로 자르면 엉뚱한 데가 잘린다.

**높이를 안 쓰고 잘록한 데를 찾는 법** (전부 잰 것):

    ① 거리장   O 안쪽 거리장 D. 팔 · 다리의 **속심**에서 크고 관절에서 작다
    ② 씨앗     D 의 h-극대 (얕은 봉우리는 합친다) -> 부위마다 씨앗 하나
    ③ 분수령   -D 위의 watershed. 물은 **제일 잘록한 데서 갈린다** — 방향을 안 정해 준다
    ④ 관절면   갈린 두 부위의 **맞닿은 화소**에 평면을 맞춘다 (무게중심 + 최소분산 방향)
               -> 관절 = {점, 법선, 반지름}. **기울기가 z 에서 얼마나 벗어났는지**가 이 설계의 증거다

통과 조건을 **먼저 적는다**:

    Q1  관절면 중 **z 축에서 15° 이상 기운 것이 하나 이상** (전부 수평이면 높이 자르기와 같다)
    Q2  부피 보존 오차 < 2%
    Q3  구조 부품 3 개 이상 · 제일 큰 조각 < 90%
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H
W = H.W
OUT = H.OUT
H봉우리 = 2.0                    # 칸. 이보다 얕은 거리장 봉우리는 이웃과 합친다 (부위가 잘게 부서지는 것을 막는다)
최소몫 = 0.005                   # 전체 부피 대비. 이보다 작은 조각은 이웃에 돌려준다
N = 192                          # 격자. 거리장 · 분수령은 256³ 이면 무겁다 (형상은 같다)


def 부위(O):
    """거리장 분수령 — **방향을 안 정해 주고** 잘록한 데서 가른다."""
    from skimage.morphology import h_maxima
    from skimage.segmentation import watershed
    D = ndimage.distance_transform_edt(O).astype(np.float32)
    씨 = h_maxima(D, H봉우리) & O
    씨, n = ndimage.label(씨, np.ones((3, 3, 3), bool))
    lab = watershed(-D, 씨, mask=O)
    # 부스러기는 제일 큰 이웃에 돌려준다
    크기 = np.bincount(lab.ravel())
    크기[0] = 0
    작 = np.where((크기 > 0) & (크기 < 최소몫 * O.sum()))[0]
    if len(작):
        큰 = ~np.isin(lab, 작) & (lab > 0)
        i = ndimage.distance_transform_edt(~큰, return_distances=False, return_indices=True)
        메움 = lab[tuple(i)]
        lab = np.where(np.isin(lab, 작), 메움, lab)
    return D, lab, n


def 관절면(lab, a, b, 셀):
    """부위 a · b 가 맞닿은 화소에 평면을 맞춘다 -> (점, 법선, 반지름, 넓이)."""
    A = ndimage.binary_dilation(lab == a, np.ones((3, 3, 3), bool))
    면 = A & (lab == b)
    pts = np.argwhere(면).astype(float)
    if len(pts) < 8:
        return None
    c = pts.mean(0)
    u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    n = vt[2]                                            # 분산이 제일 작은 방향 = 면의 법선 = **부위 축**
    r = float(np.sqrt(len(pts) / np.pi)) * 셀            # 맞닿은 넓이를 원으로 보면 반지름
    return c, n / np.linalg.norm(n), r, int(len(pts))


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    g, (ux, uy, z) = H.field_default(masks, back_sign=bs, n=N)
    셀 = (W.U1 - W.U0) / N
    O = g > 0
    D, lab, 씨수 = 부위(O)

    크기 = np.bincount(lab.ravel())
    크기[0] = 0
    부품 = [int(i) for i in np.argsort(-크기) if 크기[i] > 0]
    전체 = int(O.sum())

    # 이웃 쌍마다 관절면
    관절 = []
    for i, a in enumerate(부품):
        for b in 부품[i + 1:]:
            r = 관절면(lab, a, b, 셀)
            if r is None:
                continue
            c, n, rad, 화소 = r
            기울 = float(np.degrees(np.arccos(min(1.0, abs(n[2])))))    # 0° = 수평면(z 자르기) · 90° = 수직면
            세계 = [float(ux[int(round(c[0]))]), float(uy[int(round(c[1]))]), float(z[int(round(c[2]))])]
            관절.append({"부위": [int(a), int(b)], "점": [round(v, 4) for v in 세계],
                         "법선": [round(float(v), 3) for v in n], "반지름": round(rad, 4),
                         "맞닿은 화소": 화소, "z 에서 기운 각": round(기울, 1),
                         "src": "measured(분수령 경계면에 맞춘 평면)"})
    관절.sort(key=lambda j: -j["맞닿은 화소"])

    Q = {"Q1 15° 이상 기운 관절면 있음": bool(any(j["z 에서 기운 각"] >= 15 for j in 관절)),
         "Q2 부피 보존 오차 < 2%": bool(abs(1 - float(크기.sum()) / max(전체, 1)) < 0.02),
         "Q3 부품 >= 3 · 최대 < 90%": bool(len(부품) >= 3 and 크기[부품[0]] / max(전체, 1) < 0.90)}

    # ---- 그림
    팔 = [(230, 70, 70), (70, 140, 230), (70, 190, 110), (240, 170, 40), (170, 100, 220),
          (40, 190, 200), (230, 120, 180), (140, 150, 60), (120, 120, 200), (200, 90, 60),
          (90, 170, 90), (210, 150, 210), (150, 110, 70), (100, 190, 240), (250, 120, 90)]
    첫 = np.zeros((N, N), np.int32)
    for j in range(N):
        v = lab[:, j, :].T
        새 = (첫 == 0) & (v > 0)
        첫[새] = v[새]
    rgb = np.full((N, N, 3), 255, np.uint8)
    for i, l in enumerate(부품[:len(팔)]):
        rgb[첫 == l] = 팔[i]
    rgb[(첫 > 0) & ~np.isin(첫, 부품[:len(팔)])] = (185, 188, 195)
    S = 640
    색칠 = Image.fromarray(rgb[::-1]).resize((S, S), Image.NEAREST)
    dr2 = ImageDraw.Draw(색칠)
    for j in 관절[:14]:                                   # 관절면을 앞에서 본 **선분**으로 (기울기가 보인다)
        cx = (j["점"][0] - W.U0) / (W.U1 - W.U0) * S
        cz = (1 - (j["점"][2] - W.Z0) / (W.Z1 - W.Z0)) * S
        nx, nz = j["법선"][0], j["법선"][2]
        L = max(j["반지름"] / (W.U1 - W.U0) * S, 6)
        dx, dz = -nz, nx                                  # 면 방향 = 법선에 직각
        m = max((dx ** 2 + dz ** 2) ** 0.5, 1e-6)
        dr2.line([cx - dx / m * L, cz + dz / m * L, cx + dx / m * L, cz - dz / m * L], (20, 20, 20), 4)
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    sheet = Image.new("RGB", (S * 2 + 470, S + 92), "white")
    sheet.paste(원, (0, 82))
    sheet.paste(색칠, (S + 10, 82))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    dr.text((14, 18), "면 자르기 — 관절면은 부위 축에 직각이다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 52), "거리장 분수령으로 가르고(방향을 안 정해 준다) 맞닿은 면에 평면을 맞췄다. "
                      "검은 선분 = 관절면을 앞에서 본 것", (90, 92, 100), f본)
    x, y = S * 2 + 30, 92
    dr.text((x, y), "부품 %d · 관절면 %d · 씨앗 %d" % (len(부품), len(관절), 씨수), (40, 44, 52), f본); y += 34
    for k, v in Q.items():
        dr.text((x, y), "%s  %s" % (k, "통과" if v else "짐"), (28, 110, 60) if v else (200, 40, 40), f본); y += 30
    y += 10
    dr.text((x, y), "관절면 (맞닿은 넓이 순)", (40, 44, 52), f본); y += 30
    dr.text((x, y), "  z 기울   반지름   화소", (120, 122, 130), f본); y += 26
    for j in 관절[:11]:
        col = (200, 40, 40) if j["z 에서 기운 각"] >= 15 else (60, 64, 72)
        dr.text((x, y), "  %5.1f°   %.3f   %d" % (j["z 에서 기운 각"], j["반지름"], j["맞닿은 화소"]), col, f본)
        y += 28
    o = os.path.join(OUT, "면자르기_%s.png" % case)
    sheet.save(o)

    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    rec = {"케이스": case, "격자": N, "부품": len(부품), "씨앗": 씨수,
           "부피 몫": [round(float(크기[l]) / max(전체, 1), 4) for l in 부품[:15]],
           "판정": Q, "관절": 관절,
           "손잡이": {"H봉우리": H봉우리, "최소몫": 최소몫, "격자": N, "출처": "guessed(눈으로)"}}
    json.dump(rec, open(os.path.join(OUT, "기록", "면자르기_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                        "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"schema": "art-to-3d/joints/1", "case": case, "unit": "총높이 = 1.0",
               "joints": [{"id": "j%02d" % i, "parts": j["부위"], "cut": {"point": j["점"], "normal": j["법선"]},
                           "r": j["반지름"], "tilt_deg": j["z 에서 기운 각"], "src": j["src"]}
                          for i, j in enumerate(관절)]},
              open(os.path.join(OUT, "관절_%s.json" % case), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  부품 %d · 관절면 %d · 씨앗 %d" % (len(부품), len(관절), 씨수))
    for k, v in Q.items():
        print("   %-28s %s" % (k, "통과" if v else "짐"))
    for j in 관절[:10]:
        print("   기울 %5.1f°  반지름 %.3f  화소 %5d  부위 %s" % (j["z 에서 기운 각"], j["반지름"], j["맞닿은 화소"], j["부위"]))
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
