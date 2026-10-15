# 판정기준51 (나) 입력 — 부품 10,000 × 여섯 방향: [맞춘 선 그림 · 채운 윤곽 · 껍질 깊이 층(0 ~ 17)] uint8 128² · 반높이는 데이터51 의 「반」(틀 상자) · 10-15
# 사용(venv): 입력51.py → out/설명/캐드부품/입력51.npy (memmap · 10000 × 6 × 3 × 128 × 128)
import sys, numpy as np
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
import 여섯방향 as S6, 지역틀 as T, 윤곽바탕 as W
O = "G:/art2real/out/설명/캐드부품/"
def _채움(m):
    try: return W.바깥(m)[0]
    except ValueError: return np.zeros(m.shape, bool)
def 하나(job):
    X, F, S, 반 = job; 껍 = T.껍질(_채움(X), _채움(F), _채움(S)); out = np.zeros((6, 3, 128, 128), np.uint8)
    for n, k in enumerate(S6.방향):
        그 = T.그림맞춤(X, F, S, k); out[n, 0] = 그; out[n, 1] = _채움(그); out[n, 2] = T.깊이층(껍, k, float(반[n])) if 반[n] > 0 else 17
    return out
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); X = d["X"]; del d; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; 반 = np.load(O + "데이터51.npz")["반"]; n = len(X)
    M = np.lib.format.open_memmap(O + "입력51.npy", mode="w+", dtype=np.uint8, shape=(n, 6, 3, 128, 128))
    with Pool(6, maxtasksperchild=200) as pool:
        for i, r in enumerate(pool.imap(하나, ((X[i], F[i], S[i], 반[i]) for i in range(n)), chunksize=16)):
            M[i] = r
            if i % 1000 == 0: print(i, flush=True)
    M.flush(); print("ok", M.shape)
