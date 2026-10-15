# 판정기준49 모양 그림 — 오른 2 · 그대로 4 · 내린 2 · 줄마다 선 그림 셋 + 정답 · 48 칸 틀 · 96 칸 틀(마칭 큐브 면) · 10-15
import json, os, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; 조 = O + "평가49/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; X = d["X"][te]; del d; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
v48 = np.load(O + "부피IoU_46_42.npy"); 범 = json.load(open(O + "범위46.json")); v = {}
for fn in os.listdir(조): dd = json.load(open(조 + fn, encoding="utf-8")); v.update({k: x[1] for k, x in zip(dd["자리"], dd["값"])})
ks = sorted(v); 차 = {k: v[k] - v48[k, 1] for k in ks}
오 = sorted(ks, key=lambda k: -차[k])[:2]; 그 = sorted([k for k in ks if abs(차[k]) < .02], key=lambda k: -v48[k, 1]); 그 = 그[::max(len(그) // 4, 1)][:4]; 내 = sorted(ks, key=lambda k: 차[k])[:2]
def 면(ax, q, 색, n):
    if q.sum() == 0: ax.text2D(.5, .5, "빈 칸", transform=ax.transAxes, ha="center", fontsize=20, color="r"); ax.set_axis_off(); return
    vv, ff, _, _ = marching_cubes(np.pad(q, 1).astype(float), .5); vv = (vv - 1) / n
    ax.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 45)))
    lo, hi = vv.min(0), vv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 + .02
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r); ax.view_init(28, -58); ax.set_axis_off()
고른 = [(k, "오름") for k in 오] + [(k, "그대로") for k in 그] + [(k, "내림") for k in 내]
fig = plt.figure(figsize=(36, 5.2 * len(고른)))
for r, (k, 종) in enumerate(고른):
    j = 범[k]; vv, ff, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통37((X[j], F[j], S[j]), H)
    for c, (im, t) in enumerate(((X[j], "위"), (F[j], "앞"), (S[j], "옆"))):
        ax = fig.add_subplot(len(고른), 6, r * 6 + c + 1); ax.imshow(1 - im, cmap="gray"); ax.axis("off"); ax.set_title(("[%s] %d 번 · " % (종, j) if c == 0 else "") + t + " 선 그림", fontsize=20)
    for c, (q, t, 색) in enumerate(((J.점유_메시(vv, ff, 96), "정답", "#5cb85c"), (J.점유_캐드(몸, 48), "틀 48 칸  %.2f" % v48[k, 1], "#f0a030"), (J.점유_캐드(몸, 96), "틀 96 칸  %.2f" % v[k], "#e07020"))):
        ax = fig.add_subplot(len(고른), 6, r * 6 + 4 + c, projection="3d"); 면(ax, q, 색, 96 if "48" not in t else 48); ax.set_title(t, fontsize=22)
    print(j, 종, flush=True)
fig.suptitle("판정기준49 — 칸을 반으로 줄이면 무엇이 바뀌나 · 오른 것은 얇은 부품 · 그대로인 것은 틀 모양이 정답과 다름", fontsize=28)
plt.savefig(O + "결과49_모양.png", dpi=40, bbox_inches="tight")
