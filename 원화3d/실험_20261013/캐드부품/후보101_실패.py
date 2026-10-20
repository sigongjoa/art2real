# 판정기준97 안 되는 곳 — 시험 300 부품마다 넓은 ∪ 후보에서 깎인 속 정답 ±1 이 빠진 화소 · 부품별 빠짐 몫 · 10-20
# 사용(venv · ART_MEM_GB=10): 후보101_실패.py → out/설명/캐드부품/후보101_실패.npz (부품 · 깎인 수 · 빠진 수 · 빠짐 지도 packbits)
import numpy as np
import 후보101 as P
O = P.O; K = 32
d = np.load(O + "데이터.npz"); P.X = d["X"]; 시 = d["시험"]; e = np.load(O + "데이터_앞옆.npz"); P.F, P.S = e["F"], e["S"]
h = np.load(O + "숨은선88.npz"); P.HX, P.HF, P.HS = h["HX"], h["HF"], h["HS"]; P.반 = np.load(O + "데이터51.npz")["반"]
I = np.load(O + "후보96_색인.npy").astype(np.int64); 층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
부품 = np.nonzero(시)[0][:300]; 깎수 = np.zeros((300, 6), int); 빠수 = np.zeros((300, 6), int); 지도 = np.zeros((300, 6, 128, 128), bool)
for t, i in enumerate(부품):
    C = P.후보(i, True)
    for n in range(6):
        q = (C[n, 0][I[n, 0]] | C[n, 1][I[n, 1]]).astype(np.int64); g = 층[i, n].astype(np.int64); 안 = (입[i, n, 1] > 0) & (g < K); 깎 = 안 & (g >= 껍[i, n].astype(np.int64) + 2)
        bit = lambda L: ((q >> np.clip(L, 0, 31)) & 1) > 0; 곁 = bit(g) | bit(g - 1) | bit(g + 1)
        지도[t, n] = 깎 & ~곁; 깎수[t, n] = 깎.sum(); 빠수[t, n] = 지도[t, n].sum()
np.savez_compressed(O + "후보101_실패.npz", 부품=부품, 깎수=깎수, 빠수=빠수, 지도=np.packbits(지도, axis=-1))
몫 = 빠수.sum(1) / np.maximum(깎수.sum(1), 1); 큰 = 깎수.sum(1) >= 200
print("전체 빠짐", 빠수.sum() / 깎수.sum(), "· 깎인 ≥200 부품", 큰.sum(), "· 그중 빠짐 > 0.3", (몫[큰] > .3).sum(), "· > 0.5", (몫[큰] > .5).sum())
for t in np.argsort(-몫 * 큰)[:12]: print(부품[t], 깎수[t].sum(), round(몫[t], 3), 빠수[t].tolist())
