# 판정기준89 — 숨은선88 을 방향마다 지역 화소로(지역틀.그림맞춤 · 입력51 실선 채널과 같은 정렬) → 숨은입력89.npy (부품, 6, N, N) uint8 · 10-19
import numpy as np
from multiprocessing import Pool
O = "G:/art2real/out/설명/캐드부품/"
def 하나(job):
    import 지역틀 as T, 여섯방향 as S6; X, F, S = job; return np.stack([T.그림맞춤(X, F, S, k) for k in S6.방향]).astype(np.uint8)
if __name__ == "__main__":
    z = np.load(O + "숨은선88.npz"); X, F, S = z["HX"], z["HF"], z["HS"]; n = len(X)
    M = np.lib.format.open_memmap(O + "숨은입력89.npy", mode="w+", dtype=np.uint8, shape=(n, 6, 128, 128))
    with Pool(6) as pool:
        for i, r in enumerate(pool.imap(하나, ((X[i], F[i], S[i]) for i in range(n)), chunksize=32)): M[i] = r
    M.flush()
    입 = np.load(O + "입력51.npy", mmap_mode="r"); d = np.load(O + "데이터.npz")["X"]; import 지역틀 as T; k = 7
    assert (T.그림맞춤(d[k], np.load(O + "데이터_앞옆.npz")["F"][k], np.load(O + "데이터_앞옆.npz")["S"][k], "위") == 입[k, 0, 0]).all(), "정렬이 실선 채널과 다름"
    print("ok", M.shape, "숨은선 화소 평균", float(M[:2000].reshape(2000, -1).sum(1).mean()))
