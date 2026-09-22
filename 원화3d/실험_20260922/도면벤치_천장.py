# -*- coding: utf-8 -*-
"""**도면 벤치 · 천장** — 짝이 10~11 에 묶인 까닭이 나누기인지 · 부피인지 · 해상도인지 · 자인지 가른다 (2026-09-22).

    python 도면벤치_천장.py            얼린 10 케이스 -> out/기록/도면벤치_천장_<때>.json
    python 도면벤치_천장.py <케이스>

외부 평가 2 회(README): 셋 다 「나누기가 아니라 깊이 정보 · 가려진 속 부품 · 부푼 hull」. 천장 설계 지적(셋 다 · 둘)을 받아 넷을 한 번에 잰다.
나누기 판(`부위` · `껍질2`)의 짝이 각 천장의 몇 % 인지로 병목을 가른다.

    신탁(oracle)   우리 부피 O 의 복셀마다 **정답 라벨**을 준다 — 정답 부피 안은 그 자리 정답 라벨,
                   밖(hull 이 부푼 곳)은 가장 가까운 정답 라벨. 나누기를 100 점으로 한 판이다
    자 둘          표면   지금 자 — 정답 겉 점 위의 IoU (`부품분할.회수율` · 맞은 짝 = IoU ≥ 0.5)
                   부피   우리 격자 위 복셀 IoU — 정답 부품 부피 대 우리 부품 부피. **부푼 hull 에 벌을 준다** (Grok 지적)
    천장 넷
      ① 신탁 · 표면 짝            나누기를 완벽히 했을 때 지금 자로 몇 개
      ② 신탁 · 부피 짝            같은 판을 부피 자로 — 부풂이 얼마나 깎나
      ③ 해상도 생존               정답 부품이 우리 192 격자에서 8 복셀 이상 남나 (작은 캡은 0.8 mm 한두 칸)
      ④ 보이는 정답 부품          앞 · 옆 · 뒤 판 어디서든 겉 점의 20% 이상이 보이는 부품 — 원화가 말할 수 있는 부품
      (+) 재현율                   정답 겉 점 중 우리 부피(한 칸 불림) 안 몫 — hull 은 상한이라 1 에 가까워야 한다

해석을 **돌리기 전에** 적는다 (합계 기준):

    나누기가 병목    ①이 150 이상 · ② 가 ① 의 70% 이상  -> 부피 · 자는 괜찮고 나누는 법이 못 따라간다
    부피가 병목      ② 가 ① 의 50% 이하 — 부푼 hull 이 부품을 삼킨다
    자가 병목        ④ 가 182 의 60% 이하 — 원화로 볼 수 없는 부품이 많다. 벤치 자를 「보이는 부품」으로 바꿔야 한다
    해상도가 병목    ③ 이 182 의 80% 이하
    (둘 이상 걸리면 다 적는다)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import win as W
import 시트 as S
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_껍질 as DK
import 깊이추정 as GC

OUT = H.OUT


def 정답부피(case):
    """정답 부피(정답 격자) 위 부품 라벨 — 겉은 `부품분할.정답부품` 과 같은 라벨, 속은 가장 가까운 겉 라벨."""
    tm = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh")
    w, t, _ = BB.정답부품(case)
    A, o = JD.grid(tm)
    L = np.zeros(A.shape, np.int32)
    ij = np.rint(w / JD.PITCH - o).astype(int)
    L[tuple(ij.T)] = t + 1
    idx = ndimage.distance_transform_edt(L == 0, return_distances=False, return_indices=True)
    L = np.where(A, L[tuple(idx)], 0)
    return tm, w, t, L, np.asarray(o)


def 우리격자로(L, o, ux, uy, z):
    """정답 격자 라벨 -> 우리 격자 (복셀 중심에서 읽는다). 밖은 0."""
    I = [np.rint(a / JD.PITCH - o[k]).astype(int) for k, a in enumerate((ux, uy, z))]
    ok = [(i >= 0) & (i < L.shape[k]) for k, i in enumerate(I)]
    out = np.zeros((len(ux), len(uy), len(z)), np.int32)
    ii, jj, kk = np.meshgrid(np.where(ok[0])[0], np.where(ok[1])[0], np.where(ok[2])[0], indexing="ij")
    out[ii, jj, kk] = L[I[0][ii], I[1][jj], I[2][kk]]
    return out


def 부피짝(T, P, n):
    """우리 격자 위 복셀 IoU. T = 정답 라벨(0 밖) · P = 우리 라벨(0 밖). 정답 부품마다 최대 IoU (격자에서 사라진 부품은 0)."""
    m = (T > 0) | (P > 0)
    t, p = T[m].astype(np.int64), P[m].astype(np.int64)
    M = np.zeros((t.max() + 1, p.max() + 1), np.int64)
    np.add.at(M, (t, p), 1)
    iou = M / np.maximum(M.sum(1, keepdims=True) + M.sum(0, keepdims=True) - M, 1)
    best = np.zeros(n)
    if M.shape[0] > 1:
        b = iou[1:].max(1)
        best[:len(b)] = b[:n]
    return best                                           # 정답 라벨 1.. 순서 (길이 n)


def 표면짝(lab, ax, w, t):
    p = BB.표본(lab, ax, w)
    M = np.zeros((t.max() + 1, p.max() + 1), np.int64)
    np.add.at(M, (t, p), 1)
    iou = M / np.maximum(M.sum(1, keepdims=True) + M.sum(0, keepdims=True) - M, 1)
    return iou.max(1)                                     # 정답 라벨 0.. 순서


def 보임(tm, w, t):
    """정답 겉 점마다 앞 · 옆 · 뒤 판 중 하나에서라도 보이나 -> 부품마다 보이는 몫."""
    V, F = np.asarray(tm.vertices, np.float64), np.asarray(tm.faces, np.int64)
    fc = F.mean(1) if False else V[F].mean(1)
    보 = np.zeros(len(w), bool)
    for v in W.VIEWS:
        a, sign = W.VIEW_AXIS[v]
        _, ident = S.draw(V, F, np.full((len(F), 3), 200, np.uint8), np.zeros(len(F), np.int32), v, line=False)
        py, px = W.topix(sign * w[:, a], w[:, 2])
        py = np.clip(np.asarray(py, int), 0, W.RES - 1); px = np.clip(np.asarray(px, int), 0, W.RES - 1)
        f = ident[py, px]
        깊이축 = 1 - a                                     # front/back 은 y · side 는 x
        dsign = -sign if v != "side" else 1
        점깊이 = w[:, 깊이축] * dsign
        면깊이 = np.where(f >= 0, fc[np.clip(f, 0, None), 깊이축] * dsign, np.inf)
        보 |= (f >= 0) & (np.abs(점깊이 - 면깊이) < 3 * JD.PITCH)
    n = t.max() + 1
    return np.bincount(t, weights=보, minlength=n) / np.maximum(np.bincount(t, minlength=n), 1)


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    _, 부위, _ = MJ.부위(O)
    부위 = BB.채우기(부위, O)
    색, _ = BB.색라벨(c, raw, masks, p, bs, O)
    껍질2 = DK.껍질판(부위, 색, O, 2)
    tm, w, t, Lt, o = 정답부피(c)
    T = 우리격자로(Lt, o, ux, uy, z)                      # 정답 라벨 1..n (0 밖)
    # 신탁: O 안 — 정답 부피 안은 그 라벨, 밖은 가장 가까운 정답 라벨
    idx = ndimage.distance_transform_edt(T == 0, return_distances=False, return_indices=True)
    신탁 = np.where(O, T[tuple(idx)], 0)
    n = t.max() + 1
    판 = {"부위": 부위, "껍질2": 껍질2, "신탁": 신탁}
    r = {"정답 부품": int(n)}
    보몫 = 보임(tm, w, t)
    보이는 = 보몫 >= 0.2
    for k, lab in 판.items():
        s = 표면짝(lab, (ux, uy, z), w, t)
        v = 부피짝(T, lab, n)
        r[k] = {"표면 짝": int((s >= 0.5).sum()), "부피 짝": int((v >= 0.5).sum()),
                "표면 짝(보이는)": int(((s >= 0.5) & 보이는).sum()), "부피 짝(보이는)": int(((v >= 0.5) & 보이는).sum())}
    생존 = np.bincount(T[T > 0].ravel() - 1, minlength=n)
    r["해상도 생존"] = int((생존 >= 8).sum())
    r["보이는 부품"] = int(보이는.sum())
    O1 = ndimage.binary_dilation(O)
    wi = [np.clip(np.rint((w[:, k] - a[0]) / (a[1] - a[0])).astype(int), 0, len(a) - 1) for k, a in enumerate((ux, uy, z))]
    r["재현율"] = float(O1[tuple(wi)].mean())
    r["부피 비"] = float(O.sum() / max((T > 0).sum(), 1))    # 우리 부피 / 정답 부피 (우리 격자)
    return r


def main(only=None):
    cases = [only] if only else GC.케이스들
    기록 = {}
    for c in cases:
        t0 = time.time()
        r = 한케이스(c)
        기록[c] = r
        print("  %-38s 정답 %2d 보임 %2d 생존 %2d 재현 %.2f 부피비 %.2f | " % (c, r["정답 부품"], r["보이는 부품"], r["해상도 생존"], r["재현율"], r["부피 비"])
              + " | ".join("%s 표면 %2d 부피 %2d" % (k, r[k]["표면 짝"], r[k]["부피 짝"]) for k in ("부위", "껍질2", "신탁"))
              + "  %.0f초" % (time.time() - t0), flush=True)
    합 = lambda f: int(sum(f(r) for r in 기록.values()))
    요약 = {"정답 부품": 합(lambda r: r["정답 부품"]), "보이는 부품": 합(lambda r: r["보이는 부품"]),
          "해상도 생존": 합(lambda r: r["해상도 생존"]),
          "재현율 중앙": float(np.median([r["재현율"] for r in 기록.values()])),
          "부피 비 중앙": float(np.median([r["부피 비"] for r in 기록.values()]))}
    for k in ("부위", "껍질2", "신탁"):
        요약[k] = {m: 합(lambda r, m=m: r[k][m]) for m in ("표면 짝", "부피 짝", "표면 짝(보이는)", "부피 짝(보이는)")}
    s = 요약
    s["해석"] = {
        "나누기가 병목": s["신탁"]["표면 짝"] >= 150 and s["신탁"]["부피 짝"] >= 0.7 * s["신탁"]["표면 짝"],
        "부피가 병목": s["신탁"]["부피 짝"] <= 0.5 * s["신탁"]["표면 짝"],
        "자가 병목": s["보이는 부품"] <= 0.6 * s["정답 부품"],
        "해상도가 병목": s["해상도 생존"] <= 0.8 * s["정답 부품"]}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "도면벤치_천장_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
