# 64 편(섬) 재료 — 475 너트 · 264 플랜지 · 942 원뿔 컵: 정답 · 옛 짓기 · 고친 짓기 렌더 + 475 칠 · 단면 · 10-15
import json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
from matplotlib.colors import ListedColormap
import 짓기 as J
A = "G:/art2real/out/영상05/대화/64_섬/자료/"; os.makedirs(A, exist_ok=True); O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Yt = d["Y"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
M = np.load(O + "학습42/시험예측.npz"); P, PD = M["P"], M["D"].astype(np.float32)
def 렌더(q, 이름, 색):
    fig = plt.figure(figsize=(6, 6)); ax = fig.add_subplot(projection="3d"); fig.patch.set_alpha(0); ax.set_facecolor((0, 0, 0, 0))
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(35, -58); ax.set_axis_off()
    plt.savefig(A + 이름 + ".png", dpi=110, bbox_inches="tight", transparent=True); plt.close()
for j in (475, 264, 942):
    v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H)
    렌더(J.점유_메시(v, f), "%d_정답" % j, "#7fc97f"); 렌더(J.점유_캐드(J.옛깎기(몸, P[j], PD[j], H, True)), "%d_옛" % j, "#f0a030"); 렌더(J.점유_캐드(J.깎기(몸, P[j], PD[j], H, True)), "%d_새" % j, "#5b9bd5"); print(j, flush=True)
cm = ListedColormap(["white", "#888888", "#e04040", "#4080e0"])
for n, im in (("475_정답칠", Yt[475]), ("475_모델칠", P[475])): plt.imsave(A + n + ".png", im, cmap=cm, vmin=0, vmax=3)
