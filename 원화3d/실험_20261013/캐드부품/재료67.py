# 67 편(잘됨) 재료 — 잘됨 묶음의 쉬운 모양 넷(정답 렌더) + 447 번 틀(윤곽 교차) 렌더 · 10-16
import json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
A = "G:/art2real/out/영상05/대화/67_잘됨/자료/"; os.makedirs(A, exist_ok=True); O = "G:/art2real/out/설명/캐드부품/"
te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; z = np.load(O + "데이터51.npz"); 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
def 렌더(q, 이름, 색):
    fig = plt.figure(figsize=(6, 6)); ax = fig.add_subplot(projection="3d"); fig.patch.set_alpha(0); ax.set_facecolor((0, 0, 0, 0))
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(35, -58); ax.set_axis_off()
    plt.savefig(A + 이름 + ".png", dpi=100, bbox_inches="tight", transparent=True); plt.close()
for j in (447, 760, 667, 365): 렌더(풀(z["정답"][te[j]]), "%d_정답" % j, "#7fc97f")
렌더(풀(z["틀"][te[365]]), "365_틀", "#f0a030")   # 10-16 447 은 틀 0.81 이라 154 에 안 듦 → 365(틀 0.997); print("ok")
