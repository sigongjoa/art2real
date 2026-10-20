# 판정기준110 고침 2 천장에서 「안 됨」(코드 천장 F < 천장32 F − 0.1) 450 부품만 · 3면도 썸네일 묶음(손실 큰 순) · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
O = "G:/art2real/out/설명/캐드부품/"; te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 예 = te[json.load(open(O + "범위46.json"))]; 거 = np.load(O + "거름62.npy")
A = np.nan_to_num(np.load(O + "코드110/값.npy")); C = np.nan_to_num(np.load(O + "천장32/값.npy")); d = C[:, 0] - A[:, 0]; k = np.nonzero(거 & (d > .1))[0]; k = k[np.argsort(-d[k])]
d0 = np.load(O + "데이터.npz"); X = d0["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
def 도(a, b): img = np.ones((128, 128, 3)); img[b > 0] = (.35, .6, 1); img[a > 0] = 0; return img
열 = 6; 행 = -(-len(k) // 열); fig, ax = plt.subplots(행, 열, figsize=(열 * 4.2, 행 * 1.75))
for a in ax.ravel(): a.axis("off")
for t, j in enumerate(k):
    i = 예[j]; a = ax.ravel()[t]; a.imshow(np.concatenate([도(X[i], HX[i]), np.ones((128, 4, 3)), 도(F[i], HF[i]), np.ones((128, 4, 3)), 도(S[i], HS[i])], 1))
    a.set_title(f"{i} · 코드 {A[j, 0]:.2f} / 천장32 {C[j, 0]:.2f}", fontsize=9)
fig.suptitle(f"450 중 안 되는 {len(k)} 부품 (손실의 79 %) · 위 · 앞 · 옆 도면", fontsize=16); plt.tight_layout(); plt.savefig(O + "코드110/안됨.png", dpi=55); print(len(k))
np.save(O + "코드110/안됨.npy", 예[k])
