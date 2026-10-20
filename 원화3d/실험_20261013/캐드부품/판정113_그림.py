# 판정기준113 그림 — 안 되던 88 부품: 고침 2 F 대 회전 후보 F(점) · 3면도 썸네일로 가장 오른 넷 · 안 오른 넷 · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
O = "G:/art2real/out/설명/캐드부품/"; te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 예 = list(te[json.load(open(O + "범위46.json"))])
N = np.nan_to_num(np.load(O + "코드110/값.npy")); P = np.nan_to_num(np.load(O + "코드110/고침2/값.npy")); 안 = list(np.load(O + "코드110/안됨.npy")); k = np.array([예.index(i) for i in 안])
d0 = np.load(O + "데이터.npz"); X = d0["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
도 = lambda a, b: np.where((a > 0)[..., None], 0., np.where((b > 0)[..., None], np.array([.45, .65, 1.]), 1.))
fig = plt.figure(figsize=(18, 9)); ax = fig.add_axes([.04, .1, .36, .8]); ax.scatter(P[k, 0], N[k, 0], c=np.where(N[k, 0] > P[k, 0] + .02, "#28a050", np.where(N[k, 0] < P[k, 0] - .02, "#d8262b", "#9aa3ad")), s=30)
ax.plot([0, 1], [0, 1], "k--", lw=1); ax.set_xlabel("고침 2 (회전 후보 전) F@1"); ax.set_ylabel("회전 후보 넣은 뒤 F@1"); ax.set_title(f"안 되던 88 부품 · 평균 {P[k,0].mean():.3f} → {N[k,0].mean():.3f} (기준 +0.05 못 넘음)", fontsize=13)
줄 = np.argsort(-(N[k, 0] - P[k, 0])); 고 = [k[j] for j in 줄[:4]] + [k[j] for j in 줄[-4:]]
for q, j in enumerate(고):
    i = 예[j]; a = fig.add_axes([.43 + (q % 4) * .145, .52 - (q // 4) * .44, .14, .36]); a.imshow(np.concatenate([도(X[i], HX[i]), 도(F[i], HF[i])], 0)); a.axis("off")
    a.set_title(f"{'오름' if q < 4 else '안 오름'} {i}\n{P[j,0]:.2f} → {N[j,0]:.2f}", fontsize=11, color="#28a050" if q < 4 else "#d8262b")
fig.suptitle("판정기준113 실패 — 회전 후보: 공 · 원 영역은 오르지만 안 되던 88 은 +0.034 · 450 F 0.928 → 0.935 · 울퉁 4.5 → 5.9 %", fontsize=15)
plt.savefig(O + "판정113.png", dpi=70); print("저장")
