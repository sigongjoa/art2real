# 판정기준51 CAD 천장 그림 — 정답 깊이로 지은 여섯 방향 CAD(지킴짓기) · 위에서만 정답 칠(판정50 천장) · 정답 · 정해 둔 4 개 + 0.5 아래 4 개 + 무작위 4 개 · 10-15
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J, 여섯방향 as S6, 여섯방향_빠른 as S6빠
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; Yt, Dt = d["Y"][te], d["D"][te].astype(np.float32); del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
범 = json.load(open(O + "범위46.json")); 자리 = {j: k for k, j in enumerate(범)}; R = json.load(open(O + "천장51c_전부.json", encoding="utf-8")); c50 = np.load(O + "부피IoU_52대조.npy")
cad = np.array([x["CAD"] for x in R]); g = np.random.default_rng(52)
낮 = [범[k] for k in g.choice(np.nonzero(cad < .5)[0], 4, replace=False)]; 아무 = [범[k] for k in g.choice(len(범), 4, replace=False)]; 고른 = [942, 769, 475, 264] + 낮 + 아무
def 면(ax, q, 색):
    if q.sum() == 0: ax.text2D(.5, .5, "빈 칸", transform=ax.transAxes, ha="center", fontsize=20, color="r"); ax.set_axis_off(); return
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / 48
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); m = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(m[0] - r, m[0] + r); ax.set_ylim(m[1] - r, m[1] + r); ax.set_zlim(m[2] - r, m[2] + r); ax.view_init(35, -58); ax.set_axis_off()
fig = plt.figure(figsize=(22, 5.2 * len(고른)))
for row, j in enumerate(고른):
    k = 자리[j]; v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H); 지 = S6.깊이지도(v, f); s, _ = S6빠.지킴짓기(몸, 지)
    q6 = J.점유_캐드(s) if s.vals() else np.zeros((48,) * 3, bool); q1 = J.점유_캐드(J.깎기(몸, Yt[j], Dt[j], H, True, J.다각섬4))
    ax = fig.add_subplot(len(고른), 4, row * 4 + 1); ax.imshow(1 - X[j], cmap="gray"); ax.axis("off"); ax.set_title("%d 번 · %s" % (j, "정해 둔" if row < 4 else "0.5 아래" if row < 8 else "무작위"), fontsize=20)
    for col, (q, t, 색) in enumerate(((J.점유_메시(v, f), "정답", "#7fc97f"), (q1, "위에서만 정답 칠 %.2f" % c50[k, 1], "#f0a030"), (q6, "여섯 방향 정답 CAD %.2f" % cad[k], "#5b9bd5"))):
        ax = fig.add_subplot(len(고른), 4, row * 4 + 2 + col, projection="3d"); 면(ax, q, 색); ax.set_title(t, fontsize=22)
    print(j, flush=True)
fig.suptitle("CAD 천장(정답을 넣었을 때) — 위에서만 0.680 → 여섯 방향 0.803 · 712 중 0.9 넘음 395 · 0.5 아래 84", fontsize=26)
plt.savefig(O + "결과51_천장.png", dpi=36, bbox_inches="tight")
