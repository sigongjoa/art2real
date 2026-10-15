# 판정기준51 (가) 첫 판 그림 — 정해 둔 4 개(942 원뿔 컵 · 769 누운 원통 · 475 너트 · 264 플랜지) + 무작위 8 개 · 정답 · 42 + 고친 짓기 · (가) · 10-15
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
범 = json.load(open(O + "범위46.json")); 자리 = {j: k for k, j in enumerate(범)}; z = np.load(O + "데이터51.npz"); 정 = z["정답"]
D = O + "학습51가_첫판/"; P = np.load(D + "예측.npy"); 자 = {int(i): n for n, i in enumerate(np.load(D + "예측부품.npy"))}; a = np.load(D + "부피IoU.npy"); c = np.load(O + "부피IoU_52대조.npy")
M = np.load(O + "학습42/시험예측.npz"); YP, DP = M["P"], M["D"].astype(np.float32); 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
고른 = [942, 769, 475, 264] + list(np.random.default_rng(51).choice([j for j in 범 if j not in (942, 769, 475, 264)], 8, replace=False))
def 면(ax, q, 색):
    if q.sum() == 0: ax.text2D(.5, .5, "빈 칸", transform=ax.transAxes, ha="center", fontsize=20, color="r"); ax.set_axis_off(); return
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); m = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(m[0] - r, m[0] + r); ax.set_ylim(m[1] - r, m[1] + r); ax.set_zlim(m[2] - r, m[2] + r); ax.view_init(35, -58); ax.set_axis_off()
fig = plt.figure(figsize=(22, 5.2 * len(고른)))
for row, j in enumerate(고른):
    k = 자리[j]; i = int(te[j]); vv, ff, H = J.정규메시(L[i]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); q42 = J.점유_캐드(J.깎기(몸, YP[j], DP[j], H, True, J.다각섬4))
    ax = fig.add_subplot(len(고른), 4, row * 4 + 1); ax.imshow(1 - X[j], cmap="gray"); ax.axis("off"); ax.set_title("%d 번 · 위 선 그림" % j, fontsize=20)
    for col, (q, t, 색) in enumerate(((풀(정[i]), "정답", "#7fc97f"), (q42, "42 + 고친 짓기 %.2f" % c[k, 0], "#f0a030"), (풀(P[자[i]]), "(가) 칸 %.2f" % a[k, 0], "#5b9bd5"))):
        ax = fig.add_subplot(len(고른), 4, row * 4 + 2 + col, projection="3d"); 면(ax, q, 색); ax.set_title(t, fontsize=22)
    print(j, flush=True)
fig.suptitle("판정기준51 (가) 첫 판 — 위 4 개는 정해 둔 부품 · 아래 8 개는 무작위 · 712 개 평균 (가) 0.677 · 42 + 고친 짓기 0.663", fontsize=26)
plt.savefig(O + "결과51가_첫판.png", dpi=36, bbox_inches="tight")
