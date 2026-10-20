# 판정기준97 해석 — 누운 원기둥 66 아래 방향 단면의 후보가 어느 도면 · 어느 선에서 왔나 · 10-20
# 사용(venv · ART_MEM_GB=8): 후보101_출처.py → out/설명/캐드부품/후보101_출처.png
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
import 후보96 as H, 후보101 as P
O = P.O; K = 32; N = 128
d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
반 = np.load(O + "데이터51.npz")["반"]; I = np.load(O + "후보96_색인.npy").astype(np.int64)
층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r")
i, n, y = 66, 1, 63; assert H.방[n] == "아래" and H.축["아래"][0] == 2   # 깊이 축 z · 출처 0 = 앞 도면 [x, z] · 출처 1 = 옆 도면 [y, z]
H.열후보 = P.열후보_넓게; C = H.하나(X[i], F[i], S[i], HX[i], HF[i], HS[i], 반[i])
bits = lambda q: np.stack([((q.astype(np.int64) >> c) & 1) > 0 for c in range(K)], -1)
A = bits(C[n, 0][I[n, 0]])[y]; B = bits(C[n, 1][I[n, 1]])[y]
g = 층[i, n].astype(np.int64); 안 = (입[i, n, 1] > 0) & (g < K); 깎 = 안 & (g >= 껍[i, n].astype(np.int64) + 2)
xp = int(np.nonzero(깎[y])[0][2]); ca, cb = int(I[n, 0][y, xp]), int(I[n, 1][y, xp])
h0 = float(반[i][n]); w = -H.g + H.칸 / 2; 층z = np.clip(np.floor((h0 - w) / (2 * h0 / K) + 1e-6), 0, K - 1).astype(int)   # z 칸 → 층
fig = plt.figure(figsize=(18, 10)); gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 2.2])
for j, (그림, 숨, c, 이름, 색) in enumerate(((F[i], HF[i], ca, "앞 도면", "#e05020"), (S[i], HS[i], cb, "옆 도면", "#8040c0"))):
    a = fig.add_subplot(gs[j, 0]); img = np.ones((N, N, 3)); img[숨 > 0] = (.55, .7, 1); img[그림 > 0] = 0
    a.imshow(img); a.axvline(c, color=색, lw=2.5); a.set_title(f"{이름} (검정 실선 · 하늘 숨은선)\n세로줄 = 단면의 칸 하나가 읽는 열", fontsize=11); a.axis("off")
    a = fig.add_subplot(gs[j, 1]); 열 = (그림[:, c] > 0) | (숨[:, c] > 0); 층열 = 층z[N - 1 - np.arange(N)]   # 원본 행 r → z = N-1-r
    a.imshow(np.where(열[:, None], 0, 1) * np.ones((1, 12)), cmap="gray", aspect="auto", extent=(0, 1, N, 0))
    for r in np.nonzero(열)[0]: a.text(1.1, r, f"층 {층열[r]}", va="center", fontsize=7, color=색)
    a.set_xlim(0, 2.2); a.set_xticks([]); a.set_title(f"그 열을 위에서 아래로\n선이 지나는 곳마다 깊이 후보 하나", fontsize=11)
a = fig.add_subplot(gs[:, 2]); xs = np.arange(N); gy = np.where(안[y], g[y], np.nan)
a.fill_between(xs, gy, K, where=안[y], color="#eeeeee", step="mid")
for x in xs[안[y]]:
    for c in np.nonzero(A[x] | B[x])[0]:
        a.add_patch(plt.Rectangle((x - .5, c - .5), 1, 1, lw=0, color="#2a7fd4" if A[x, c] and B[x, c] else ("#e05020" if A[x, c] else "#8040c0")))
a.step(xs, gy, "k-", where="mid", lw=2.5); a.plot(xs[깎[y]], gy[깎[y]], "o", color="r", ms=3); a.axvline(xp, color="k", ls=":", lw=1)
for c, 색, 이름 in (("#e05020", "#e05020", "앞 도면에서 온 후보 — x 열마다 다름"), ("#8040c0", "#8040c0", "옆 도면에서 온 후보 — 이 줄 전체가 같은 열 하나를 읽음"), ("#2a7fd4", "#2a7fd4", "두 도면 모두 (교집합)")): a.add_patch(plt.Rectangle((0, 0), 0, 0, color=색, label=이름))
a.plot([], [], "k-", lw=2.5, label="실제 면 = 정답"); a.legend(loc="lower right", fontsize=10)
a.set_ylim(K, -1); a.set_xlim(xs[안[y]].min() - 3, xs[안[y]].max() + 3); a.set_xlabel("가로 위치 x"); a.set_ylabel("깊이 층 (0 = 아래에서 본 맨 앞)")
a.set_title(f"부품 66 아래에서 본 단면 · 점선 칸 x={xp} 의 후보 = 앞 도면 열 {ca} 의 선 ∪ 옆 도면 열 {cb} 의 선\n앞 {A[xp].sum()}개 + 옆 {B[xp].sum()}개", fontsize=12)
fig.suptitle("잡음이 아니다: 도면 한 장은 축 하나를 지운다 → 그 열에 있는 물체의 모든 선(반대쪽 원 · 안쪽 원 · 숨은선)이 이 칸의 후보가 된다", fontsize=14)
plt.tight_layout(); plt.savefig(O + "후보101_출처.png", dpi=85); print("저장", xp, ca, cb, A[xp].sum(), B[xp].sum())
