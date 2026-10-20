# 판정기준110 고친 판 진단 그림 — 「후보에 정답 없음」 화소가 많은 시험 부품 넷: 제 도면 + 영역 · 정답 층 · 코드 천장 층 · 빨강 = 후보 없음 / 주황 = 후보는 있는데 영역 하나로 못 맞춤 · 10-20
import pickle, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
import 코드110 as C
R = pickle.load(open(C.D + "특징_시험.pkl", "rb")); T = np.load(C.D + "층.npy", mmap_mode="r"); 줄 = []
for t, (i, rs) in enumerate(R):
    g6 = C.층32[i].astype(int); s6 = C.껍32[i].astype(int); 깎6 = (C.입[i][:, 1] > 0) & (g6 < 32) & (g6 >= s6 + 2)
    for n in range(6):
        g = g6[n].ravel(); 없 = np.zeros(128 * 128, bool); 못 = np.zeros(128 * 128, bool); 영 = np.zeros(128 * 128, int)
        for r, (nn, idx, vs, f, 신) in enumerate(rs):
            if nn != n: continue
            V = np.stack([v.astype(int) for v in vs]); e = np.abs(V - g[idx][None]); k = 깎6[n].ravel()[idx]; 없[idx] = k & ~(e <= 1).any(0); 못[idx] = k & (e <= 1).any(0) & ~(e[신] <= 1); 영[idx] = r + 1
        줄.append((없.sum(), t, i, n, 없.reshape(128, 128), 못.reshape(128, 128), 영.reshape(128, 128)))
줄.sort(key=lambda x: -x[0]); 고른 = []; 본 = set()
for x in 줄:
    if x[2] not in 본: 고른.append(x); 본.add(x[2])
    if len(고른) == 4: break
fig, ax = plt.subplots(4, 4, figsize=(17, 17))
for r, (k, t, i, n, 없, 못, 영) in enumerate(고른):
    안 = C.입[i, n, 1] > 0; g = C.층32[i, n].astype(float)
    ax[r, 0].imshow(np.where(안, 영 % 20, np.nan), cmap="tab20"); ax[r, 0].contour(C.입[i, n, 0] > 0, [.5], colors="k", linewidths=.4); ax[r, 0].set_title(f"부품 {i} · 방향 {C.H.방[n]} · 제 도면 선 + 영역")
    ax[r, 1].imshow(np.where(안 & (g < 32), g, np.nan), vmin=0, vmax=31); ax[r, 1].set_title("정답 층")
    ax[r, 2].imshow(np.where(안, T[t, n].astype(float), np.nan), vmin=0, vmax=31); ax[r, 2].set_title("코드 천장 층(신탁 고르기)")
    im = np.ones((128, 128, 3)); im[안] = .88; im[못] = (.95, .55, .1); im[없] = (.85, .15, .15); ax[r, 3].imshow(im); ax[r, 3].set_title(f"빨강 후보 없음 {없.sum()} · 주황 영역 하나로 못 맞춤 {못.sum()}")
for a in ax.ravel(): a.axis("off")
fig.suptitle("판정기준110 고친 판 천장 0.924 — 깎인 속의 43 % 는 영역의 어느 후보에도 정답이 없다", fontsize=15); plt.tight_layout(); plt.savefig(C.D + "진단.png", dpi=65); print("저장", [(x[2], x[3], x[0]) for x in 고른])
