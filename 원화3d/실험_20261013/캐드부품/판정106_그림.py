# 판정기준106 그림 — 시험 부품 넷 · 방향 하나: 정답 층 · 판0 · 부드러움 예측 · 두 판의 |틀림| · 10-20
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
O = "G:/art2real/out/설명/캐드부품/"; te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r")
P0 = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); P1 = np.load(O + "학습69_부드러움/예측.npy", mmap_mode="r")
부 = [(325, 1), (2435, 5), (1569, 0), (59, 0)]; fig, ax = plt.subplots(len(부), 5, figsize=(19, 4 * len(부)))
for r, (i, n) in enumerate(부):
    t = int(np.nonzero(te == i)[0][0]); g = 층[i, n].astype(float); 안 = (입[i, n, 1] > 0) & (g < 32); M = lambda a: np.where(안, a, np.nan)
    for j, (a, 제) in enumerate(((g, "정답 층"), (P0[t, n], "판0 예측"), (P1[t, n], "부드러움 예측"))): ax[r, j].imshow(M(a.astype(float)), vmin=0, vmax=31); ax[r, j].set_title(f"부품 {i} · {제}")
    for j, (a, 제) in enumerate(((P0[t, n], "판0"), (P1[t, n], "부드러움"))):
        e = np.abs(a.astype(int) - g.astype(int)); m = ax[r, 3 + j].imshow(M(e.astype(float)), cmap="magma", vmin=0, vmax=8); ax[r, 3 + j].set_title(f"{제} |틀림| 층 · ±1 안 {((e <= 1) & 안).sum() / 안.sum():.3f}")
    for a in ax[r]: a.axis("off")
fig.suptitle("판정기준106 실패 — 부드러운 정답으로 바꿔도 틀리는 곳 · 틀림 크기가 거의 그대로 (시험 300 안 ±1 0.871 대 0.872)", fontsize=15)
plt.tight_layout(); plt.savefig(O + "판정106.png", dpi=70); print("저장")
