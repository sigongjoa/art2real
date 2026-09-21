# -*- coding: utf-8 -*-
"""**자를 자리를 잰다** — 관절 후보를 원화에서 찾는다 (2026-09-21).

    python 관절후보.py [케이스=오메가몬]   -> out/관절후보_<케이스>.png · out/기록/관절후보_<케이스>_<때>.json

부위별로 세우려면 **어디서 자를지**를 먼저 정해야 한다. 지어내면 09-13 의 「판마다 짓기」와 같은
길이다(부품 IoU 0.892 -> 전체 0.619). 그래서 **재서 고른다.** 채널 둘, 둘 다 정답이 필요 없다.

    ① 잘록한 곳   hull 단면적 A(z) 의 국소 최소. 목 · 손목 · 발목 · 허리는 **가늘다**
    ② 갈라지는 곳 앞 판 행의 **덩어리 개수**가 바뀌는 높이. 팔이 몸통에서 떨어지는 자리

둘 다 **연속 장 hull 에서 그대로 읽는다** — 새 추정기도, 새 자도 없다.
사람은 이 후보에서 **고르기만** 한다 (메모리 `no-ground-truth-is-the-core`).
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H
W = H.W
OUT = H.OUT
돌출 = 0.12                    # 국소 최소가 이만큼(양쪽 봉우리 대비) 파여야 후보. **눈으로 고른 값**
최소간격 = 6                   # 칸. 이보다 가까운 후보는 깊은 쪽만 남긴다
런최소 = 8                     # 화소. 이보다 가는 덩어리는 세지 않는다 (선 · 부스러기)


def 잘록(A, 돌출=돌출):
    """A(z) 의 국소 최소를 **양쪽 봉우리 대비 파인 깊이**로 고른다. (scipy.find_peaks 와 같은 뜻 · 4 줄)"""
    out = []
    for k in range(1, len(A) - 1):
        if A[k] <= 0 or not (A[k] <= A[k - 1] and A[k] <= A[k + 1]):
            continue
        l = A[:k].max() if k else 0
        r = A[k + 1:].max()
        d = (min(l, r) - A[k]) / max(min(l, r), 1)
        if d >= 돌출:
            out.append((k, d))
    out.sort(key=lambda t: -t[1])
    고름 = []
    for k, d in out:
        if all(abs(k - j) >= 최소간격 for j, _ in 고름):
            고름.append((k, d))
    return sorted(고름)


def 덩어리수(mask, 행):
    n = 0
    for s, e in H._구간(mask[행]):
        if e - s + 1 >= 런최소:
            n += 1
    return n


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    g, (_, _, z) = H.field_default(masks, back_sign=bs)
    n = g.shape[2]
    A = np.array([(g[:, :, k] > 0).sum() for k in range(n)], float)

    후보 = [{"종류": "잘록", "k": int(k), "z": round(float(z[k]), 4), "세기": round(float(d), 3),
             "단면적": int(A[k])} for k, d in 잘록(A)]
    # ② 갈라지는 높이 — 앞 판에서 덩어리 개수가 바뀌는 행
    R = masks["front"].shape[0]
    수 = np.array([덩어리수(masks["front"], r) for r in range(R)])
    버팀 = 20                                                   # 행. 바뀐 개수가 이만큼 이어져야 진짜 (팔 · 다리가 갈라짐)
    for r in range(1, R):
        if (수[r] != 수[r - 1] and min(수[r], 수[r - 1]) >= 1
                and (수[r:r + 버팀] == 수[r]).all() and (수[max(0, r - 버팀):r] == 수[r - 1]).all()):
            zz = W.Z1 - (r + 0.5) / R * (W.Z1 - W.Z0)
            k = int(np.clip(np.searchsorted(z, zz), 0, n - 1))
            if any(abs(k - c["k"]) < 최소간격 for c in 후보 if c["종류"] == "갈라짐"):
                continue
            후보.append({"종류": "갈라짐", "k": k, "z": round(float(zz), 4),
                         "덩어리": "%d→%d" % (수[r - 1], 수[r]), "단면적": int(A[k])})
    후보.sort(key=lambda c: -c["z"])

    # 도안(buildspec)의 목 후보와 맞대 본다 — 서로 다른 길로 잰 것끼리
    bp = os.path.join(OUT, "원화도안", case, "buildspec.json")
    도안목 = 0
    if os.path.exists(bp):
        j = json.load(open(bp, encoding="utf-8"))
        도안목 = sum(1 for q in j["parts"] if q["necks"])

    # ---- 그림: 원화 + 후보선 + A(z) 곡선
    S = 760
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    im = Image.open(흰).convert("RGB") if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    im = im.resize((S, S))
    sheet = Image.new("RGB", (S + 460, S + 90), "white")
    sheet.paste(im, (0, 70))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    dr.text((14, 16), "관절 후보 — 원화에서 잰다 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 46), "파랑 잘록한 곳(단면적 국소 최소) · 주황 갈라지는 곳(덩어리 수가 바뀌는 높이)  "
                      "— 둘 다 정답 없이 나온다", (90, 92, 100), f본)
    # A(z) 곡선 (z 가 세로)
    x0, x1 = S + 40, S + 420
    for i in range(n - 1):
        y = 70 + int((1 - (z[i] - W.Z0) / (W.Z1 - W.Z0)) * S)
        y2 = 70 + int((1 - (z[i + 1] - W.Z0) / (W.Z1 - W.Z0)) * S)
        dr.line([x0 + int(A[i] / max(A.max(), 1) * (x1 - x0)), y,
                 x0 + int(A[i + 1] / max(A.max(), 1) * (x1 - x0)), y2], (60, 64, 72), 2)
    dr.text((x0, 48), "단면적 A(z)", (60, 64, 72), f본)
    for c in 후보:
        y = 70 + int((1 - (c["z"] - W.Z0) / (W.Z1 - W.Z0)) * S)
        col = (50, 110, 210) if c["종류"] == "잘록" else (225, 130, 30)
        dr.line([0, y, S, y], col, 2)
        dr.line([x0 - 8, y, x1, y], col, 1)
        꼬 = "%.2f" % c.get("세기", 0) if c["종류"] == "잘록" else c.get("덩어리", "")
        dr.text((6, y - 22), "%s %s" % (c["종류"], 꼬), col, f본)
    o = os.path.join(OUT, "관절후보_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    rec = {"케이스": case, "격자": n, "후보": 후보, "도안 목 후보 부품": 도안목,
           "손잡이": {"돌출": 돌출, "최소간격": 최소간격, "런최소": 런최소, "출처": "guessed(눈으로)"}}
    json.dump(rec, open(os.path.join(OUT, "기록", "관절후보_%s_%s.json"
                                     % (case, time.strftime("%Y%m%d_%H%M"))), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  후보 %d 개 (잘록 %d · 갈라짐 %d) · 도안의 목 후보 부품 %d"
          % (len(후보), sum(c["종류"] == "잘록" for c in 후보), sum(c["종류"] == "갈라짐" for c in 후보), 도안목))
    for c in 후보:
        print("   %-4s z %.3f  %s" % (c["종류"], c["z"], c.get("덩어리") or "세기 %.2f" % c["세기"]))
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")

