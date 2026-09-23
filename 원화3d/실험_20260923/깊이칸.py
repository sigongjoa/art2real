# -*- coding: utf-8 -*-
"""**깊이 칸** — 사람이 도면에 깊이 숫자를 몇 개 적으면 부피가 얼마나 맞나 (2026-09-23).

    python 깊이칸.py            얼린 10 케이스 -> out/기록/깊이칸_<때>.json

09-23 에 자동으로 깊이를 얻으려는 시도가 잇따라 졌다(폭 사전 · TV/최소표면 · 색 대응 · DA3).
깊이 신탁은 0.90 인데 그 깊이는 **그림에 없다.** 그러면 **사람이 몇 개나 적어야 하나?** — 피규어 앱의 수치 도면이
정확히 이 질문이다(부위마다 「깊이」 칸 하나).

    부위 = `면자르기.부위`(거리장 분수령). 부위마다 정답에서 **숫자 한두 개**를 읽어 사람 입력을 흉내낸다.
    판 D1 (두께 1 개)     부위의 정답 두께(y 방향 평균 폭)만 받는다 — hull 단면의 가운데를 기준으로 그 두께로 조인다
    판 D2 (두께 + 앞면)   정답의 앞면 위치도 받는다 — 두 숫자
    칸 수를 늘려 가며 (큰 부위부터 1 · 2 · 3 · 5 · 전부) IoU 를 잰다
    ⚠ 이건 **신탁(천장)** 이다 — 09-22 교훈대로 **틀린 입력 대조군**을 같이 잰다: 부위 번호를 뒤섞어
      남의 두께를 받는다. 뒤섞어도 오르면 그 숫자는 뜻이 없다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이추정 as GC


def 숫자읽기(부위, T, l):
    """부위 l 에서 정답의 앞면 · 두께(칸)를 읽는다 — 사람이 재서 적는 숫자 둘."""
    m = (부위 == l) & T
    if m.sum() < 20:
        return None
    ii = np.argwhere(m)
    앞 = float(np.percentile(ii[:, 1], 2))
    뒤 = float(np.percentile(ii[:, 1], 98))
    return 앞, max(뒤 - 앞, 1.0)


def 조이기(O, 부위, 칸, 판):
    """부위마다 y 방향으로 주어진 두께(와 앞면)로 조인다. 칸 = {부위: (앞, 두께)}"""
    X = O.copy()
    idx = np.arange(O.shape[1])[None, :, None]
    for l, (앞, 두) in 칸.items():
        m = 부위 == l
        if not m.any():
            continue
        기둥 = m.any(axis=1)                                  # (x,z) 에 이 부위가 있나
        시작 = np.where(기둥, np.argmax(m, axis=1), 0)
        끝 = np.where(기둥, O.shape[1] - 1 - np.argmax(np.flip(m, 1), axis=1), 0)
        if 판 == "D1":                                       # 두께만: hull 단면 가운데를 지킨다
            가 = (시작 + 끝) / 2
            lo, hi = 가 - 두 / 2, 가 + 두 / 2
        else:                                                # 두께 + 앞면
            lo, hi = np.full_like(시작, 앞, np.float64), np.full_like(시작, 앞 + 두, np.float64)
        살 = (idx >= lo[:, None, :]) & (idx <= hi[:, None, :])
        X &= ~m | 살
    return X


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    _, 부위, _ = MJ.부위(O)
    부위 = BB.채우기(부위, O)
    라벨 = [l for l in np.unique(부위) if l]
    라벨.sort(key=lambda l: -(부위 == l).sum())               # 큰 부위부터
    값 = {l: 숫자읽기(부위, T, l) for l in 라벨}
    값 = {l: v for l, v in 값.items() if v}
    rng = np.random.default_rng(5)
    뒤 = list(값.values()); rng.shuffle(뒤)
    뒤값 = {l: v for l, v in zip(값.keys(), 뒤)}
    r = {"지금": PB.재기(O, T), "부위 수": len(라벨)}
    for 판 in ("D1", "D2"):
        for n in (1, 2, 3, 5, len(값)):
            칸 = {l: 값[l] for l in list(값)[:n]}
            r["%s %d칸" % (판, n * (1 if 판 == "D1" else 2))] = PB.재기(조이기(O, 부위, 칸, 판), T)
        칸 = {l: 뒤값[l] for l in list(값)}
        r["%s 뒤섞(전부)" % 판] = PB.재기(조이기(O, 부위, 칸, 판), T)
    return r


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-28s 부위%2d | " % (c[:28], r["부위 수"]) + " | ".join("%s %.2f" % (k, v["IoU"]) for k, v in r.items() if isinstance(v, dict) and (k.startswith("D") or k == "지금")) + "  %.0f초" % (time.time() - t0), flush=True)
    판들 = [k for k, v in 기록[GC.케이스들[0]].items() if isinstance(v, dict)]
    중앙 = lambda 판, m: float(np.median([기록[c][판][m] for c in GC.케이스들 if 판 in 기록[c]]))
    요약 = {p: {m: round(중앙(p, m), 3) for m in ("IoU", "정밀도", "재현율", "부피 비")} for p in 판들}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "깊이칸_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
