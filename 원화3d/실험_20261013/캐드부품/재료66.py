# 66 편(영역) 재료 — 942 위 그림 영역 색칠 · 영역 수 대 (천장 − 나) 산점 · 475 앞 정답 깊이 지도(한 영역 안 깊이가 변함) + 선 · 10-15
import sys, json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
import 여섯방향 as S6, 지역틀 as T, 영역53 as R
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False; plt.rcParams["xtick.labelsize"] = plt.rcParams["ytick.labelsize"] = 18; A = "G:/art2real/out/영상05/대화/66_영역/자료/"; os.makedirs(A, exist_ok=True); O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; 층 = np.load(O + "데이터51.npz")["층"]
for j, k in ((942, "위"), (475, "앞")):
    그 = T.그림맞춤(X[j], F[j], S[j], k); lab, n = R.영역들(그); rng = np.random.default_rng(3); 색 = np.vstack([[1, 1, 1], rng.uniform(.35, .95, (n, 3))]); im = 색[lab]; im[그 > 0] = 0
    plt.imsave(A + "%d_영역.png" % j, im); print(j, k, "영역", n)
그 = T.그림맞춤(X[475], F[475], S[475], "앞"); 깊 = 층[te[475]][list(S6.방향).index("앞")].astype(float); 깊[깊 == 17] = np.nan
fig, ax = plt.subplots(figsize=(6, 6)); ax.imshow(깊, cmap="viridis"); ax.imshow(np.ma.masked_where(그 == 0, 그), cmap="gray_r", alpha=1); ax.axis("off"); plt.savefig(A + "475_앞깊이.png", dpi=110, bbox_inches="tight", transparent=True); plt.close()
a = np.load(O + "영역53.npy"); 나 = np.load(O + "학습51나_판0전체/부피IoU.npy")[:, 0]; m = a[:, 0] >= .5
fig, ax = plt.subplots(figsize=(7, 5)); ax.scatter(a[m, 5], (a[:, 0] - 나)[m], s=22, c="#5b9bd5", alpha=.6); ax.set_xscale("log"); ax.set_xlabel("선으로 닫힌 칸 수(여섯 방향 합)", fontsize=24); ax.set_ylabel("정답 깊이 점수 - 모델 점수", fontsize=22); ax.axhline(0, c="k", lw=1)
ax.spines[["top", "right"]].set_visible(False); plt.savefig(A + "상관.png", dpi=110, bbox_inches="tight", transparent=True); plt.close()
