# -*- coding: utf-8 -*-
"""깊이학습 데이터 — 그림이 주는 것(실루엣 · 선)으로 6 방향 깊이를 맞히는 학습 · 10-10
입력 3 칸: 실루엣 S · 선 L(실루엣 윤곽 + 깊이 끊김 + 꺾임) · 윤곽 교차 깊이 Dh(세 실루엣 교집합 · 그림만으로 계산됨)
정답: 실물 깊이 D · 실물학습 2,883 부품(시험 36 부품의 모델은 통째로 빠짐) + 시험 35 부품(평가만)
python runs/깊이학습/준비.py [일꾼=6]  →  학습.npz · 시험.npz"""
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub"), T0]
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; N = 128

def 교차깊이(S):
    """세 실루엣의 교집합(복셀) → 6 방향 깊이 (실물보기 규약: 낮은 쪽 d=(i+.5)/n · 높은 쪽 1−(i+.5)/n · 빈 곳 1)"""
    s0, s1, s2 = S[0] > .5, S[2] > .5, S[4] > .5                       # ax0:(y,z) ax1:(x,z) ax2:(x,y)
    V = s0[None, :, :] & s1[:, None, :] & s2[:, :, None]; n = V.shape[0]; D = []
    for ax in range(3):
        v = np.moveaxis(V, ax, -1); any_ = v.any(-1)
        lo = v.argmax(-1); hi = n - 1 - v[..., ::-1].argmax(-1)
        D.append(np.where(any_, (lo + .5) / n, 1.0)); D.append(np.where(any_, 1 - (hi + .5) / n, 1.0))
    return np.stack(D).astype(np.float32)

def 선(S, D):
    """그림의 선 흉내: 실루엣 윤곽 + 깊이 끊김(1 차 차분 > 0.03) + 꺾임(2 차 차분 > 0.004)"""
    import cv2
    L = []
    for s, d in zip(S, D):
        s8 = (s > .5).astype(np.uint8); out = s8 - cv2.erode(s8, np.ones((3, 3), np.uint8))
        gx, gy = np.abs(np.diff(d, axis=0, append=d[-1:])), np.abs(np.diff(d, axis=1, append=d[:, -1:]))
        cx, cy = np.abs(np.diff(d, 2, axis=0, prepend=d[:1], append=d[-1:])), np.abs(np.diff(d, 2, axis=1, prepend=d[:, :1], append=d[:, -1:]))
        l = ((gx > .03) | (gy > .03) | (cx > .004) | (cy > .004)) & (s8 > 0)
        L.append(((l | (out > 0))).astype(np.float32))
    return np.stack(L)

def 일(p):
    import trimesh
    from s0 import unit
    from 실물보기 import 실물보기
    try:
        m = unit(trimesh.load(RR + p, force="mesh")); S, D = 실물보기(m, N)
        return np.stack([S, 선(S, D), 교차깊이(S), D]).astype(np.float16)    # (4, 6, N, N)
    except Exception: return None

if __name__ == "__main__":
    from multiprocessing import Pool
    W = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    목록 = json.load(open(os.path.join(R, "실물학습", "목록.json"), encoding="utf-8")); 키 = sorted(목록)
    시험 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
    with Pool(W) as po:
        X = po.map(일, [목록[k] for k in 키], chunksize=8); T = po.map(일, 시험)
    ok = [i for i, x in enumerate(X) if x is not None]; print("학습", len(ok), "/", len(X), "시험", sum(t is not None for t in T))
    np.savez(os.path.join(H, "학습.npz"), X=np.stack([X[i] for i in ok])); np.savez(os.path.join(H, "시험.npz"), X=np.stack(T), 부품=np.array(시험))
