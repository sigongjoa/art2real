# 판정기준95 기하 처리 — 여섯 방향 깊이 후보: 깊이 축 a 에 수직인 선(실선 + 점선 · 그 축이 아닌 쪽으로 5 화소 넘게 이어짐)의 a 좌표 → 그 방향 32 층 · 화소 후보 = 두 도면 열 후보의 교집합 · 10-19
# 저장: out/설명/캐드부품/후보96.npy (부품, 6, 2, 128) uint32 bit = 층 · 후보96_색인.npy (6, 2, 128, 128) 지역 화소 → 두 열 번호 · 쓰기: 후보(i, k) = C[i,k,0][IA[k,0]] & C[i,k,1][IA[k,1]]
# 사용(venv · ART_MEM_GB=10): 후보96.py [시험] → 시험 = 300 부품 방향별 정답 층이 후보 안 몫만
import sys, numpy as np, cv2
import 여섯방향 as S6, 지역틀 as T
O = "G:/art2real/out/설명/캐드부품/"; N = 128; K = 32; 칸 = S6.칸; g = S6.g
방 = list(S6.방향); 축 = {"위": (2, 1), "아래": (2, -1), "앞": (1, 1), "뒤": (1, -1), "옆": (0, 1), "반옆": (0, -1)}
def 색인():   # 방향마다 지역 (Y, X) → 세계 칸 (x, y, z) 중 깊이 축 아닌 둘 · A 열 · B 열
    Y, X = np.meshgrid(np.arange(N), np.arange(N), indexing="ij"); out = np.zeros((6, 2, N, N), np.int16)
    for n, k in enumerate(방):
        p = np.stack([g[X], -g[Y], np.zeros_like(g[X])], -1) @ S6.R(*S6.방향[k]).T; i = T._세계칸(p); a = 축[k][0]
        out[n] = {2: (i[..., 0], i[..., 1]), 1: (i[..., 0], i[..., 2]), 0: (i[..., 1], i[..., 2])}[a]
    return out
def 이음(L, ax):   # ax 방향으로 5 화소 넘게 이어진 선만
    k = np.ones((5, 1) if ax == 0 else (1, 5), np.uint8); return cv2.dilate(cv2.erode(L.astype(np.uint8), k), k) > 0
def 열후보(Lxy, Lxz, Lyz):   # 세계 선 지도 셋 → 축마다 (A 열 → a 칸 bool, B 열 → a 칸 bool)
    z = (이음(Lxz, 0), 이음(Lyz, 0)); y = (이음(Lxy, 0), 이음(Lyz, 1).T); x = (이음(Lxy, 1).T, 이음(Lxz, 1).T)
    return {2: z, 1: y, 0: x}   # 각 (열 수 N, a 칸 N)
def 하나(X, F, S, HX, HF, HS, 반):
    Lxy = np.maximum(X, HX)[::-1].T > 0; Lxz = np.maximum(F, HF)[::-1].T > 0; Lyz = np.maximum(S, HS)[::-1].T > 0   # [x, y] · [x, z] · [y, z]
    열 = 열후보(Lxy, Lxz, Lyz); out = np.zeros((6, 2, N), np.uint32)
    for n, k in enumerate(방):
        a, s = 축[k]; h = float(반[n])
        if h <= 0: continue
        w = s * g + 칸 / 2; 층 = np.clip(np.floor((h - w) / (2 * h / K) + 1e-6), 0, K - 1).astype(np.int64)   # a 칸 → 층
        for j in range(2):
            m = 열[a][j]; bits = np.zeros(N, np.uint64)
            for c in np.nonzero(m.any(0))[0]: bits[m[:, c]] |= np.uint64(1) << np.uint64(층[c])
            out[n, j] = bits.astype(np.uint32)
    return out
def 펴기(C, I):   # (6, 2, N) bit · 색인 → (6, N, N) uint32 화소 후보
    return np.stack([C[n, 0][I[n, 0]] & C[n, 1][I[n, 1]] for n in range(6)])
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
    반 = np.load(O + "데이터51.npz")["반"]; I = 색인(); np.save(O + "후보96_색인.npy", I)
    if sys.argv[1:] == ["시험"]:
        층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r"); a = np.zeros((6, 6))
        for i in np.nonzero(시)[0][:300]:
            P = 펴기(하나(X[i], F[i], S[i], HX[i], HF[i], HS[i], 반[i]), I)
            for n in range(6):
                gg = 층[i, n].astype(np.int64); 안 = (입[i, n, 1] > 0) & (gg < K); s = 껍[i, n].astype(np.int64); q = P[n].astype(np.uint64)
                맞 = ((q >> gg.clip(0, 31).astype(np.uint64)) & 1) > 0; 곁 = 맞 | (((q >> (gg - 1).clip(0, 31).astype(np.uint64)) & 1) > 0) | (((q >> (gg + 1).clip(0, 31).astype(np.uint64)) & 1) > 0)
                허 = 곁 | (gg == s) | (q == 0); 깎 = 안 & (gg >= s + 2)
                a[n] += [안.sum(), (맞 & 안).sum(), (곁 & 안).sum(), (허 & 안).sum(), 깎.sum(), (맞 & 깎).sum()]
        for n, k in enumerate(방): print(k, "후보 안 %.3f · ±1 %.3f · B 허용 안 %.3f · 속 깎임 후보 안 %.3f" % (a[n, 1] / a[n, 0], a[n, 2] / a[n, 0], a[n, 3] / a[n, 0], a[n, 5] / max(a[n, 4], 1)))
        t = a.sum(0); print("전체 후보 안 %.3f · ±1 %.3f · B 허용 안 %.3f · 속 깎임 %.3f" % (t[1] / t[0], t[2] / t[0], t[3] / t[0], t[5] / t[4])); sys.exit()
    from multiprocessing import Pool
    M = np.lib.format.open_memmap(O + "후보96.npy", mode="w+", dtype=np.uint32, shape=(len(X), 6, 2, N))
    for i in range(len(X)):
        M[i] = 하나(X[i], F[i], S[i], HX[i], HF[i], HS[i], 반[i])
        if i % 2000 == 0: print(i, flush=True)
    M.flush(); print("ok")
