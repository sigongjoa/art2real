# 판정기준94 — 껍질(윤곽 셋 교집합) 깊이를 32 단 내림으로(정답 층32 와 같은 규칙) · 지금 입력51 2 번은 16 단(× 2 로 씀) · 10-19
# 사용(venv · ART_MEM_GB=12): 껍질94.py 시험 → 300 부품으로 정답 대비 몫만 · 껍질94.py → out/설명/캐드부품/껍질32.npy (부품 × 6 × 128² uint8 · 32 = 통째)
import sys, numpy as np
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
import 여섯방향 as S6, 지역틀 as T, 입력51 as I51
O = "G:/art2real/out/설명/캐드부품/"; K = 32
def 층32(칸128, k, h):   # 지역틀.깊이층 과 같은 기둥 · 내림만 32 단
    i = T.모으기(k); 기둥 = 칸128[i[0], i[1], i[2]]; 있 = 기둥.any(-1); 첫 = 기둥.argmax(-1)
    w = np.where(있, S6.g[::-1][첫] + S6.칸 / 2, np.nan); d = np.where(np.isnan(w), 2 * h + .1, h - w)
    q = np.floor(np.clip(d, 0, None) / (2 * h / K) + 1e-6); return np.where(d > 2 * h, K, np.clip(q, 0, K - 1)).astype(np.uint8)
def 하나(job):
    X, F, S, 반 = job; 껍 = T.껍질(I51._채움(X), I51._채움(F), I51._채움(S))
    return np.stack([층32(껍, k, float(반[n])) if 반[n] > 0 else np.full((128, 128), K, np.uint8) for n, k in enumerate(S6.방향)])
def 몫(C, idx):   # 윤곽 안 화소에서 정답 − 껍질 차의 몫
    입 = np.load(O + "입력51.npy", mmap_mode="r"); 층 = np.load(O + "층32.npy", mmap_mode="r"); c = np.zeros(5)
    for j, i in enumerate(idx):
        안 = 입[i, :, 1] > 0; g = 층[i].astype(int); s = C[j].astype(int); 옛 = np.where(입[i, :, 2] == 17, 32, 입[i, :, 2].astype(int) * 2)
        c += [안.sum(), (안 & (g < s)).sum(), (안 & (g == s)).sum(), (안 & (g == s + 1)).sum(), (안 & (g < 옛)).sum()]
    return {"정답 < 껍질": round(c[1] / c[0], 4), "정답 = 껍질": round(c[2] / c[0], 4), "정답 = 껍질 + 1": round(c[3] / c[0], 4), "옛 껍질에서 정답 < 껍질": round(c[4] / c[0], 4)}
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); X = d["X"]; del d; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; 반 = np.load(O + "데이터51.npz")["반"]; n = len(X)
    if sys.argv[1:] == ["시험"]:
        idx = np.random.default_rng(94).choice(n, 300, replace=False)
        with Pool(6) as pool: C = np.stack(pool.map(하나, [(X[i], F[i], S[i], 반[i]) for i in idx]))
        print(몫(C, idx)); sys.exit()
    M = np.lib.format.open_memmap(O + "껍질32.npy", mode="w+", dtype=np.uint8, shape=(n, 6, 128, 128))
    with Pool(6, maxtasksperchild=200) as pool:
        for i, r in enumerate(pool.imap(하나, ((X[i], F[i], S[i], 반[i]) for i in range(n)), chunksize=16)):
            M[i] = r
            if i % 2000 == 0: print(i, flush=True)
    M.flush(); print("ok", M.shape, 몫(M[:300], np.arange(300)))
