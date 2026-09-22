# -*- coding: utf-8 -*-
"""**천장 검산** — 외부 평가 3 회 지적을 숫자로 확인한다 (2026-09-22).

    python 천장_검산.py      얼린 10 케이스 -> out/기록/천장_검산_<때>.json

사용자(09-22): 「아니야 너 잘못하고 있어 애들한테 물어봐봐」. 외부 평가 3 회에서 셋 다 같은 지적:
「천장 160 은 나누기의 천장이 아니다 — 정답 점이 부피 밖이면 가장 가까운 라벨을 읽으니 부피가 틀려도 라벨만 주면
표면 점수가 나온다. 먼저 부피 복원 자체를 따로 검증하라.」 판정 기준(README 3 회 절)대로 숫자로 확인한다.

    ① 순환 시험   **일부러 틀린 부피**(우리 부피의 바운딩 박스 · 속이 꽉 찬 상자)에 같은 신탁 라벨을 주고 표면 짝을 잰다.
                 160 근처가 나오면 표면 신탁 천장은 부피와 상관없는 숫자다(지적이 맞다).
    ② 부피 검증   우리 부피 O 대 정답 부피 T (우리 격자) — IoU · 정밀도(O 중 정답 안) · 재현율(정답 중 O 안)

문턱(돌리기 전): ① 상자 표면 짝 ≥ 140 이면 지적이 맞다 · ② IoU 중앙 < 0.6 이면 「부피가 먼저」가 맞다.
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
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import 부품분할 as BB
import 도면벤치_천장 as DC
import 깊이추정 as GC

OUT = H.OUT


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm, w, t, Lt, o = DC.정답부피(c)
    T = DC.우리격자로(Lt, o, ux, uy, z)
    idx = ndimage.distance_transform_edt(T == 0, return_distances=False, return_indices=True)
    신 = T[tuple(idx)]
    ii = np.argwhere(O)
    lo, hi = ii.min(0), ii.max(0) + 1
    상자 = np.zeros_like(O)
    상자[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = True
    s_O = DC.표면짝(np.where(O, 신, 0), (ux, uy, z), w, t)
    s_box = DC.표면짝(np.where(상자, 신, 0), (ux, uy, z), w, t)
    Tm = T > 0
    교 = (O & Tm).sum()
    return {"신탁 표면 짝(우리 부피)": int((s_O >= 0.5).sum()), "신탁 표면 짝(상자)": int((s_box >= 0.5).sum()),
            "상자/우리 부피": float(상자.sum() / O.sum()),
            "부피 IoU": float(교 / max((O | Tm).sum(), 1)), "정밀도": float(교 / max(O.sum(), 1)),
            "재현율": float(교 / max(Tm.sum(), 1)), "정답 부품": int(t.max() + 1)}


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        r = 한케이스(c)
        기록[c] = r
        print("  %-38s 신탁 표면 짝 우리 %2d / 상자 %2d (상자 %.1f배) | 부피 IoU %.2f 정밀 %.2f 재현 %.2f  %.0f초"
              % (c, r["신탁 표면 짝(우리 부피)"], r["신탁 표면 짝(상자)"], r["상자/우리 부피"], r["부피 IoU"], r["정밀도"], r["재현율"], time.time() - t0), flush=True)
    요약 = {"신탁 표면 짝 합(우리)": sum(r["신탁 표면 짝(우리 부피)"] for r in 기록.values()),
          "신탁 표면 짝 합(상자)": sum(r["신탁 표면 짝(상자)"] for r in 기록.values()),
          "부피 IoU 중앙": float(np.median([r["부피 IoU"] for r in 기록.values()])),
          "정밀도 중앙": float(np.median([r["정밀도"] for r in 기록.values()])),
          "재현율 중앙": float(np.median([r["재현율"] for r in 기록.values()]))}
    요약["① 지적 맞음(상자 ≥ 140)"] = 요약["신탁 표면 짝 합(상자)"] >= 140
    요약["② 부피가 먼저(IoU < 0.6)"] = 요약["부피 IoU 중앙"] < 0.6
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "천장_검산_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()
