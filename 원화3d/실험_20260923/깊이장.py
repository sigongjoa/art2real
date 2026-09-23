# -*- coding: utf-8 -*-
"""**깊이장** — 고정 두께를 버리고, 덩어리마다 깊이를 제 폭으로 묶는다 (2026-09-23).

    python 깊이장.py            얼린 10 케이스 -> out/기록/깊이장_<때>.json

외부 평가 4 회에서 채택한 실험. 지금 타원 장은 높이마다 **앞 구간 × 옆 구간**을 곱해 단면을 만든다 —
팔이 있는 높이에서 팔의 깊이가 **몸통 옆폭**을 받아 통나무가 된다(부풂의 큰 몫).
고침: 구간 짝마다 깊이 반폭 b 를 **제 폭의 k 배**로 묶는다 — b = min(옆 반폭, k · 앞 반폭).
    k = ∞ 이면 지금과 같다 · k = 1 이면 단면이 원 이하 (팔 · 다리는 원기둥에 가깝다는 사전)
사전은 **깊이 후보를 제한하는 데만** 쓴다(형상 생성기가 아니다) — 외부 평가 셋의 교집합.

판정(README 4 회 절 · 보내기 전에 적었다 · 중앙값): **부피 IoU ≥ 0.70 · 정밀도 ≥ 0.75 · 재현율 ≥ 0.85**
k 는 정답으로 고르지 않는다 — **홀수 케이스 5 장에서 고르고 짝수 5 장에서 잰다**(홀드아웃).
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import win as W
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이추정 as GC

Ks = [np.inf, 2.0, 1.5, 1.2, 1.0, 0.8]


def 장(masks, back_sign, k, n=None):
    """`hull.field_ellipse` 와 같되, 깊이 반폭을 앞 반폭의 k 배로 묶는다."""
    n = n or BB.N
    u = W.U0 + (np.arange(n) + 0.5) / n * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(n) + 0.5) / n * (W.Z1 - W.Z0)
    rows = np.clip(((W.Z1 - z) / (W.Z1 - W.Z0) * W.RES).astype(int), 0, W.RES - 1)
    F, S = masks["front"], masks["side"]
    B = masks["back"][:, ::-1] if back_sign < 0 else masks["back"]
    cell = (W.U1 - W.U0) / n
    g = np.full((n, n, n), -2.0, np.float32)
    for kk, r in enumerate(rows):
        xr, yr = H._구간(F[r] & B[r]), H._구간(S[r])
        if not xr or not yr:
            continue
        X, A = H._축값(xr, u)                      # 앞: 정규화 거리² · 반폭
        Y, Bh = H._축값(yr, u)                     # 옆
        Bk = np.minimum(Bh[None, :], k * A[:, None]) if np.isfinite(k) else np.broadcast_to(Bh[None, :], (n, n))
        Yk = Y[None, :] * (Bh[None, :] / np.maximum(Bk, 1e-9)) ** 2     # 반폭을 줄이면 정규화 거리는 그만큼 커진다
        g[:, :, kk] = (1.0 - X[:, None] - Yk) * np.minimum(A[:, None], Bk) / 2 / cell
    return g, (u, u, z)


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    gh, ax = H.field_hull(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    r = {"hull": PB.재기(gh > 0, T)}
    for k in Ks:
        g, _ = 장(masks, bs, k)
        r["k=%s" % ("inf" if not np.isfinite(k) else k)] = PB.재기(g > 0, T)
    return r


def 검사():
    """k = inf 는 지금 기본(`hull.field_ellipse`)과 같아야 한다."""
    c = GC.케이스들[0]
    raw, masks, bs, p = BB.판(c)
    a, _ = 장(masks, bs, np.inf, n=64)
    b, _ = H.field_ellipse(masks, back_sign=bs, n=64)
    assert np.allclose(a, b, atol=1e-4), (np.abs(a - b).max())


def main():
    검사()
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-38s " % c + " | ".join("%s %.2f" % (k, v["IoU"]) for k, v in r.items()) + "  %.0f초" % (time.time() - t0), flush=True)
    판들 = list(기록[GC.케이스들[0]].keys())
    중앙 = lambda 판, m, 집합: float(np.median([기록[c][판][m] for c in 집합]))
    홀, 짝 = GC.케이스들[0::2], GC.케이스들[1::2]
    요약 = {"전체": {p: {m: 중앙(p, m, GC.케이스들) for m in ("IoU", "정밀도", "재현율", "부피 비")} for p in 판들}}
    고른 = max([p for p in 판들 if p.startswith("k=")], key=lambda p: 중앙(p, "IoU", 홀))
    요약["고름(홀수 5 장에서)"] = 고른
    요약["홀드아웃(짝수 5 장)"] = {m: 중앙(고른, m, 짝) for m in ("IoU", "정밀도", "재현율")}
    h = 요약["홀드아웃(짝수 5 장)"]
    요약["판정"] = {"IoU ≥ 0.70": h["IoU"] >= 0.70, "정밀도 ≥ 0.75": h["정밀도"] >= 0.75, "재현율 ≥ 0.85": h["재현율"] >= 0.85}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "깊이장_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
