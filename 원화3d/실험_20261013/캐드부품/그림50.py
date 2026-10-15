# 판정기준50 그림 — 새 깎기(섬 살림)로 가장 많이 오른 6 개 · 위 선 그림 · 정답 · 42 옛 깎기 · 42 새 깎기 · 10-15
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
v46 = np.load(O + "부피IoU_46_42.npy"); a = np.load(O + "부피IoU_50.npy"); 범 = json.load(open(O + "범위46.json")); M = np.load(O + "학습42/시험예측.npz"); P, PD = M["P"], M["D"].astype(np.float32)
ks = list(np.argsort(-(a[:, 0] - v46[:, 0]))[:6])
def 면(ax, q):
    if q.sum() == 0: ax.text2D(.5, .5, "빈 칸", transform=ax.transAxes, ha="center", fontsize=20, color="r"); ax.set_axis_off(); return
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors="#c8c8d0", linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(35, -58); ax.set_axis_off()
fig = plt.figure(figsize=(24, 5.5 * len(ks)))
for r, k in enumerate(ks):
    j = 범[k]; vv, ff, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H)
    ax = fig.add_subplot(len(ks), 4, r * 4 + 1); ax.imshow(1 - X[j], cmap="gray"); ax.axis("off"); ax.set_title("%d 번 · 위 선 그림" % j, fontsize=22)
    for c, (q, t) in enumerate(((J.점유_메시(vv, ff), "정답"), (J.점유_캐드(J.옛깎기(몸, P[j], PD[j], H, True)), "옛 짓기  %.2f" % v46[k, 0]), (J.점유_캐드(J.깎기(몸, P[j], PD[j], H, True)), "고친 짓기  %.2f" % a[k, 0]))):
        ax = fig.add_subplot(len(ks), 4, r * 4 + 2 + c, projection="3d"); 면(ax, q); ax.set_title(t, fontsize=24, color="tab:green" if "고친" in t else "k")
    print(j, flush=True)
fig.suptitle("판정기준50 — 깎는 영역 안의 섬을 살렸더니 · 같은 모델 칠 · 712 개 평균 0.653 → 0.663", fontsize=28)
plt.savefig(O + "결과50.png", dpi=40, bbox_inches="tight")
