# 65 편(천장) 재료 — 942 원뿔 컵 · 475 너트: 정답 · 위에서만 정답 칠 · 여섯 방향 정답 CAD 렌더 · 10-15
import json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J, 여섯방향 as S6, 여섯방향_빠른 as S6빠
A = "G:/art2real/out/영상05/대화/65_천장/자료/"; os.makedirs(A, exist_ok=True); O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Yt, Dt = d["Y"][te], d["D"][te].astype(np.float32); del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
def 렌더(q, 이름, 색):
    fig = plt.figure(figsize=(6, 6)); ax = fig.add_subplot(projection="3d"); fig.patch.set_alpha(0); ax.set_facecolor((0, 0, 0, 0))
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(35, -58); ax.set_axis_off()
    plt.savefig(A + 이름 + ".png", dpi=110, bbox_inches="tight", transparent=True); plt.close()
for j in (942, 475):
    v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); 지 = S6.깊이지도(v, f); s, _ = S6빠.지킴짓기(몸, 지)
    렌더(J.점유_메시(v, f), "%d_정답" % j, "#7fc97f"); 렌더(J.점유_캐드(J.깎기(몸, Yt[j], Dt[j], H, True, J.다각섬4)), "%d_위" % j, "#f0a030"); 렌더(J.점유_캐드(s), "%d_여섯" % j, "#5b9bd5"); print(j, flush=True)
